"""
ai_health.py - AI Portfolio Health Score via NVIDIA NIM Free Endpoint.
Uses the OpenAI-compatible NVIDIA NIM API when available and falls back to
metric-based narrative generation when the external model is unavailable.
"""

import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOTENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=DOTENV_PATH)

NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
NIM_MODEL = "google/gemma-4-31b-it"
AI_TIMEOUT_SECONDS = 12

_client = None
_client_key = None


def _get_api_key() -> str:
    return os.getenv("NVIDIA_API_KEY", "").strip()


def _get_client():
    global _client, _client_key
    api_key = _get_api_key()
    if not api_key:
        _client = None
        _client_key = None
        return None
    if _client is None or _client_key != api_key:
        _client = OpenAI(base_url=NIM_BASE_URL, api_key=api_key)
        _client_key = api_key
    return _client


def _score_diversification(holdings: list, weights: dict) -> dict:
    """Herfindahl-Hirschman Index -> diversification score 0-100."""
    if not weights:
        return {"score": 50, "label": "Moderate", "detail": "No weight data."}
    w = list(weights.values())
    hhi = sum(wi ** 2 for wi in w)
    n = len(w)
    ideal_hhi = 1 / n if n else 1
    div_score = max(0.0, (1 - hhi) / (1 - ideal_hhi)) if n > 1 else 0.0
    score = round(div_score * 100)
    if score >= 75:
        label = "Well Diversified"
    elif score >= 50:
        label = "Moderately Diversified"
    else:
        label = "Concentrated"
    return {"score": score, "label": label, "detail": f"{n} assets, HHI={hhi:.2f}"}


def _score_momentum(holdings: list) -> dict:
    """Average 1-year return of holdings -> momentum score."""
    if not holdings:
        return {"score": 50, "label": "Neutral", "detail": "No holdings."}
    rets = [h.get("ret_1y", 0) for h in holdings]
    avg = sum(rets) / len(rets) if rets else 0
    score = min(100, max(0, int(50 + avg * (50 / 30))))
    if score >= 70:
        label = "Strong Momentum"
    elif score >= 45:
        label = "Neutral"
    else:
        label = "Weak Momentum"
    return {"score": score, "label": label, "detail": f"Avg 1Y return: {avg:+.1f}%"}


def _score_risk_adjusted(prob_profit: float, var_value: float, current_value: float) -> dict:
    """Combine profit probability and VaR drawdown into a risk score."""
    prob_score = prob_profit * 100
    var_pct = (1 - var_value / current_value) * 100 if current_value > 0 else 50
    var_score = max(0, 100 - var_pct * 2)
    score = round(0.6 * prob_score + 0.4 * var_score)
    if score >= 70:
        label = "Low Risk"
    elif score >= 45:
        label = "Moderate Risk"
    else:
        label = "High Risk"
    return {
        "score": score,
        "label": label,
        "detail": f"Profit prob: {prob_profit * 100:.0f}%, VaR drawdown: {var_pct:.1f}%",
    }


def _score_growth_potential(cagrs: dict) -> dict:
    """Base-case CAGR of the median scenario -> growth potential score."""
    if not cagrs:
        return {"score": 50, "label": "Moderate", "detail": "No CAGR data."}
    base_cagr = cagrs.get("expected", 0)
    score = min(100, max(0, int(30 + base_cagr * (70 / 25))))
    if score >= 70:
        label = "High Growth"
    elif score >= 45:
        label = "Steady Growth"
    else:
        label = "Low Growth"
    return {"score": score, "label": label, "detail": f"Base CAGR: {base_cagr:+.1f}%"}


def _overall(scores: list[int]) -> int:
    return round(sum(scores) / len(scores)) if scores else 50


def _pick_risk(sub_scores: dict) -> str:
    weakest_key = min(
        [
            ("diversification", sub_scores["diversification"]["score"]),
            ("momentum", sub_scores["momentum"]["score"]),
            ("risk_adjusted", sub_scores["risk_adjusted"]["score"]),
            ("growth_potential", sub_scores["growth_potential"]["score"]),
        ],
        key=lambda item: item[1],
    )[0]

    if weakest_key == "diversification":
        return "Portfolio concentration is the clearest risk, so one holding can drive outcomes disproportionately."
    if weakest_key == "momentum":
        return "Recent price momentum is weak, which can drag confidence if market sentiment stays soft."
    if weakest_key == "risk_adjusted":
        return "Downside protection looks only moderate, so drawdowns may feel sharper during volatile periods."
    return "Growth expectations are muted, which may make long-term compounding lag a broader equity benchmark."


def _pick_opportunity(sub_scores: dict) -> str:
    strongest_key = max(
        [
            ("diversification", sub_scores["diversification"]["score"]),
            ("momentum", sub_scores["momentum"]["score"]),
            ("risk_adjusted", sub_scores["risk_adjusted"]["score"]),
            ("growth_potential", sub_scores["growth_potential"]["score"]),
        ],
        key=lambda item: item[1],
    )[0]

    if strongest_key == "diversification":
        return "Diversification is a real strength here, giving the portfolio a sturdier base across scenarios."
    if strongest_key == "momentum":
        return "Relative momentum is supportive, which can help returns if market leadership remains intact."
    if strongest_key == "risk_adjusted":
        return "Risk-adjusted behavior is encouraging, suggesting the portfolio can absorb volatility reasonably well."
    return "The projected growth profile still offers upside if earnings and market conditions improve over time."


def _pick_action(sub_scores: dict) -> str:
    weakest_key = min(
        [
            ("diversification", sub_scores["diversification"]["score"]),
            ("momentum", sub_scores["momentum"]["score"]),
            ("risk_adjusted", sub_scores["risk_adjusted"]["score"]),
            ("growth_potential", sub_scores["growth_potential"]["score"]),
        ],
        key=lambda item: item[1],
    )[0]

    if weakest_key == "diversification":
        return "Reduce concentration by adding one or two uncorrelated large-cap or index positions."
    if weakest_key == "momentum":
        return "Review lagging holdings and rebalance gradually toward names with stronger earnings and trend support."
    if weakest_key == "risk_adjusted":
        return "Trim the most volatile allocation and increase exposure to steadier compounders or diversified funds."
    return "Pair the portfolio with a higher-growth sleeve only if it still fits your risk tolerance."


SYSTEM_PROMPT = """You are an expert Indian equity portfolio analyst.
Given a structured portfolio health report, produce a concise, plain-English analysis in EXACTLY this JSON format:
{
  "headline": "<15-word punchy headline about portfolio health>",
  "summary": "<2-3 sentences. Key insight for an Indian retail investor.>",
  "top_risk": "<Biggest risk in one sentence>",
  "top_opportunity": "<Best opportunity in one sentence>",
  "action": "<Single, actionable recommendation>"
}
Return ONLY the JSON. No extra text."""


def _build_user_prompt(data: dict, sub_scores: dict) -> str:
    profile = data.get("profile_name", "Portfolio")
    cv = data.get("current_value", 0)
    pp = data.get("prob_profit", 0) * 100
    cagrs = data.get("cagrs", {})
    holdings = data.get("holdings", [])
    syms = [h["symbol"].replace(".NS", "") for h in holdings]
    base_cagr = cagrs.get("expected", 0)
    bull_cagr = cagrs.get("optimistic", 0)
    bear_cagr = cagrs.get("pessimistic", 0)

    return f"""Portfolio: {profile}
Current Value: INR {cv:,.0f}
Assets: {', '.join(syms)}
Profit Probability (5Y): {pp:.0f}%
Base-Case CAGR: {base_cagr:+.1f}%
Bull-Case CAGR: {bull_cagr:+.1f}%
Bear-Case CAGR: {bear_cagr:+.1f}%
Health Sub-Scores:
  - Diversification: {sub_scores['diversification']['score']}/100 ({sub_scores['diversification']['label']})
  - Momentum: {sub_scores['momentum']['score']}/100 ({sub_scores['momentum']['label']})
  - Risk-Adjusted: {sub_scores['risk_adjusted']['score']}/100 ({sub_scores['risk_adjusted']['label']})
  - Growth Potential: {sub_scores['growth_potential']['score']}/100 ({sub_scores['growth_potential']['label']})
Overall Health Score: {sub_scores['overall']}/100

Provide your analysis."""


def _fallback_narrative(simulation_data: dict, sub_scores: dict, reason: str | None = None) -> dict:
    profile = simulation_data.get("profile_name", "Portfolio")
    overall = sub_scores["overall"]
    prob_profit = simulation_data.get("prob_profit", 0.0) * 100
    expected_cagr = simulation_data.get("cagrs", {}).get("expected", 0.0)

    if overall >= 80:
        tone = "looks very healthy"
    elif overall >= 65:
        tone = "looks solid overall"
    elif overall >= 50:
        tone = "is workable but mixed"
    elif overall >= 35:
        tone = "needs a careful review"
    else:
        tone = "looks fragile right now"

    summary = (
        f"{profile} {tone}, with a {prob_profit:.0f}% modeled profit probability over five years. "
        f"The base-case CAGR sits around {expected_cagr:+.1f}%, so the current mix may need refinement to improve conviction."
    )
    if reason:
        summary = f"{summary} Live AI commentary is unavailable, so this insight is generated from the portfolio metrics directly."

    return {
        "headline": f"{profile} health score: {overall}/100",
        "summary": summary,
        "top_risk": _pick_risk(sub_scores),
        "top_opportunity": _pick_opportunity(sub_scores),
        "action": _pick_action(sub_scores),
    }


def _call_nvidia_llm(prompt: str, simulation_data: dict, sub_scores: dict) -> dict:
    client = _get_client()
    if client is None:
        return _fallback_narrative(simulation_data, sub_scores, reason="missing_api_key")

    try:
        completion = client.chat.completions.create(
            model=NIM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=400,
            stream=False,
            timeout=AI_TIMEOUT_SECONDS,
        )
        raw = completion.choices[0].message.content.strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(raw)
    except Exception as exc:
        return _fallback_narrative(simulation_data, sub_scores, reason=str(exc)[:200])


def compute_health_score(simulation_data: dict) -> dict:
    """Given the full simulation result dict, return a health score report."""
    holdings = simulation_data.get("holdings", [])
    weights = simulation_data.get("weights", {})
    prob = simulation_data.get("prob_profit", 0.5)
    var_val = simulation_data.get("var_value", simulation_data.get("current_value", 1))
    cv = simulation_data.get("current_value", 1)
    cagrs = simulation_data.get("cagrs", {})

    div = _score_diversification(holdings, weights)
    mom = _score_momentum(holdings)
    risk = _score_risk_adjusted(prob, var_val, cv)
    growth = _score_growth_potential(cagrs)

    overall = _overall([div["score"], mom["score"], risk["score"], growth["score"]])
    sub_scores = {
        "diversification": div,
        "momentum": mom,
        "risk_adjusted": risk,
        "growth_potential": growth,
        "overall": overall,
    }

    narrative = _call_nvidia_llm(
        _build_user_prompt(simulation_data, sub_scores),
        simulation_data,
        sub_scores,
    )

    return {
        "overall_score": overall,
        "grade": _grade(overall),
        "sub_scores": sub_scores,
        "narrative": narrative,
        "model_used": NIM_MODEL,
        "key_present": bool(_get_api_key()),
    }


def _grade(score: int) -> str:
    if score >= 80:
        return "A"
    if score >= 65:
        return "B"
    if score >= 50:
        return "C"
    if score >= 35:
        return "D"
    return "F"
