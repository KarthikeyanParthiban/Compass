from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from monte_carlo import get_management_data, get_available_profiles
from ai_health import compute_health_score
import uvicorn

app = FastAPI(title="Portfolio Compass API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "online", "message": "Portfolio Compass API is running. Visit /docs for API documentation."}

@app.get("/profiles")
async def list_profiles():
    return {"status": "success", "data": get_available_profiles()}

@app.get("/simulate")
async def simulate(
    profile_id:  str = Query("sample"),
    iterations:  int = Query(1000, ge=100,  le=10000),
    days:        int = Query(252,  ge=30,   le=1825),
    confidence:  int = Query(95,   ge=50,   le=99),
):
    try:
        result = get_management_data(
            profile_id=profile_id,
            num_sims=iterations,
            days=days,
            confidence_level=confidence,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


@app.get("/health-score")
async def health_score(
    profile_id: str = Query("sample"),
    iterations: int = Query(1000, ge=100, le=10000),
    days:       int = Query(1260, ge=252, le=1825),
    confidence: int = Query(95,   ge=50,  le=99),
):
    """
    Compute an AI-powered Portfolio Health Score (0-100) for the given profile.
    Uses deterministic quant metrics + NVIDIA NIM LLM for narrative insights.
    """
    try:
        sim_data = get_management_data(
            profile_id=profile_id,
            num_sims=iterations,
            days=days,
            confidence_level=confidence,
        )
        score_data = compute_health_score(sim_data)
        return {"status": "success", "data": score_data}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
