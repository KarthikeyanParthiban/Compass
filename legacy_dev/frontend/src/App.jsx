import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  LineChart, Line, XAxis, YAxis, ReferenceLine,
  ResponsiveContainer, Tooltip, AreaChart, Area
} from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Home, Briefcase, Search, Bell, User, Compass,
  TrendingUp, Signal, Wifi, Battery, Info, ChevronDown, BarChart2, ArrowLeft, Brain
} from 'lucide-react';
import './App.css';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const PROFILES = [
  { id: 'sample',          name: 'Sample Portfolio' },
  { id: 'index_follower',  name: 'Index Follower' },
  { id: 'growth_retail',   name: 'Retail Growth' },
  { id: 'dividend_king',   name: 'Dividend King' },
  { id: 'tech_visionary',  name: 'Tech Visionary' },
  { id: 'balanced_hybrid', name: 'Balanced Hybrid' }
];

const COLORS = ['#007aff', '#34c759', '#ff9500', '#af52de', '#ff2d55', '#5ac8fa', '#ff3b30', '#4cd964'];

const fmtINR = v => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(v);
const fmtShort = v => {
  if (!v && v !== 0) return '—';
  if (v >= 1e7) return `₹${(v / 1e7).toFixed(2)}Cr`;
  if (v >= 1e5) return `₹${(v / 1e5).toFixed(2)}L`;
  return fmtINR(v);
};

/* ─── Line Tooltip ─── */
const LineTooltip = ({ active, payload, current_value }) => {
  if (!active || !payload?.length || !current_value) return null;
  const d = payload[0]?.payload;
  
  // CAGR helper: ((Val / Start) ^ (1 / Years) - 1) * 100
  const years = d.month / 12;
  const calcC = (val) => {
    if (years === 0) return 0;
    return ((val / current_value) ** (1 / years) - 1) * 100;
  };

  return (
    <div style={{
      background: 'rgba(10,10,20,0.95)', backdropFilter: 'blur(20px)',
      padding: '12px 16px', borderRadius: 16, fontSize: 11,
      color: '#fff', fontWeight: 500, lineHeight: 1.8,
      border: '1px solid rgba(255,255,255,0.1)',
      boxShadow: '0 10px 20px rgba(0,0,0,0.4)'
    }}>
      <div style={{ fontWeight: 800, marginBottom: 6, fontSize: 13 }}>{d?.milestone || `Month ${d.month}`}</div>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto auto', gap: '4px 12px', alignItems: 'center' }}>
        <span style={{ color: '#34c759', fontWeight: 600 }}>Bull Case</span>
        <span>{fmtShort(d?.p85)}</span>
        <span style={{ opacity: 0.7, fontSize: 10 }}>({calcC(d.p85).toFixed(1)}% CAGR)</span>

        <span style={{ color: '#007aff', fontWeight: 700 }}>Base Case</span>
        <span style={{ fontWeight: 800 }}>{fmtShort(d?.median)}</span>
        <span style={{ opacity: 0.8, fontSize: 10, color: '#007aff' }}>({calcC(d.median).toFixed(1)}% CAGR)</span>

        <span style={{ color: '#ff3b30', fontWeight: 600 }}>Bear Case</span>
        <span>{fmtShort(d?.p15)}</span>
        <span style={{ opacity: 0.7, fontSize: 10 }}>({calcC(d.p15).toFixed(1)}% CAGR)</span>
      </div>
    </div>
  );
};

/* ─── Skeleton ─── */
const Skel = ({ w = '100%', h = 14, r = 10, style = {} }) => (
  <div className="skeleton" style={{ width: w, height: h, borderRadius: r, flexShrink: 0, ...style }} />
);

/* ─── COMPASS CARD ─── */
function CompassCard({ data, loading }) {
  const [showInfo, setShowInfo] = useState(false);

  const gain = data?.outcomes?.expected && data?.current_value
    ? ((data.outcomes.expected / data.current_value - 1) * 100)
    : null;
  const isPos = gain !== null ? gain >= 0 : true;
  const prob = data?.prob_profit != null ? (data.prob_profit * 100).toFixed(0) : null;

  return (
    <motion.div
      className="compass-card"
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2, type: 'spring', damping: 22 }}
    >
      {/* Header */}
      <div className="compass-header" style={{ position: 'relative' }}>
        <div className="compass-title-group">
          <div className="compass-icon-wrap">
            <Compass size={18} color="#fff" />
          </div>
          <div>
            <div className="compass-title">Portfolio Compass</div>
            <div className="compass-subtitle">Monte Carlo · 5Y horizon</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Info
            size={18}
            color="var(--text3)"
            style={{ cursor: 'pointer' }}
            onClick={() => setShowInfo(!showInfo)}
          />
        </div>

        {/* Info Popover */}
        <AnimatePresence>
          {showInfo && (
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              style={{
                position: 'absolute',
                top: '100%',
                right: 0,
                marginTop: 12,
                width: 300,
                background: 'rgba(28,28,30,0.95)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255,255,255,0.1)',
                padding: 14,
                borderRadius: 16,
                zIndex: 100,
                boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
                fontSize: 12,
                color: '#e5e5ea',
                lineHeight: 1.5,
              }}
            >
              <div style={{ color: '#fff', fontWeight: 600, marginBottom: 10, display: 'flex', justifyContent: 'space-between' }}>
                About Portfolio Compass
                <span onClick={() => setShowInfo(false)} style={{ color: 'rgba(255,255,255,0.5)', cursor: 'pointer' }}>✕</span>
              </div>

              <div style={{ marginBottom: 10 }}>
                <strong style={{ color: '#fff' }}>The Rationale</strong><br />
                Markets don't move in straight lines. We use <em>Monte Carlo</em> math to run 5,000 random market scenarios based on historical risk, giving you a realistic probability map instead of a blind guess.
              </div>

              <div style={{ marginBottom: 10 }}>
                <strong style={{ color: '#fff' }}>How to read this</strong>
                <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '4px 8px', marginTop: 4 }}>
                  <span style={{ color: '#ff3b30' }}>■</span> <span> <strong>Bear Case:</strong> Bottom 15% outcome (slowdown/correction)</span>
                  <span style={{ color: '#007aff' }}>■</span> <span> <strong>Base Case:</strong> Most likely path (moderate growth)</span>
                  <span style={{ color: '#34c759' }}>■</span> <span> <strong>Bull Case:</strong> Top 15% upside (strong equity rally)</span>
                </div>
              </div>

              <div>
                <strong style={{ color: '#fff' }}>Key Insight</strong><br />
                Don't just look at the best case. Ensure the <strong>red (Bear Case)</strong> scenario aligns with your personal risk tolerance for peace of mind.
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ── Monthly Line Chart ── */}
      <div className="chart-wrapper">
        {loading || !data?.monthly_bars?.length ? (
          <Skel h="100%" r={16} />
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={data.monthly_bars}
              margin={{ top: 15, right: 25, left: 2, bottom: 0 }}
            >
              <Tooltip content={<LineTooltip current_value={data.current_value} />} />
              <XAxis
                dataKey="month"
                type="number"
                domain={[0, 60]}
                ticks={[0, 12, 24, 36, 48, 60]}
                tickFormatter={(m) => {
                  if (m === 0) return 'Now';
                  return `${m}M`;
                }}
                tick={{ fontSize: 10, fontWeight: 600, fill: '#8e8e93' }}
                axisLine={false}
                tickLine={false}
                padding={{ left: 10, right: 10 }}
              />
              <YAxis hide domain={['auto', 'auto']} />
              <ReferenceLine
                y={data.current_value}
                stroke="rgba(255,255,255,0.08)"
                strokeDasharray="4 4"
                strokeWidth={1}
              />

              <Line
                type="monotone"
                dataKey="p85"
                stroke="#34c759"
                strokeWidth={3}
                dot={(props) => props.payload.is_milestone ? <circle cx={props.cx} cy={props.cy} r={3.5} fill="#34c759" stroke="#fff" strokeWidth={1.5} /> : null}
                activeDot={{ r: 6, fill: '#34c759', stroke: '#fff', strokeWidth: 2 }}
              />
              <Line
                type="monotone"
                dataKey="median"
                stroke="#007aff"
                strokeWidth={3}
                dot={(props) => props.payload.is_milestone ? <circle cx={props.cx} cy={props.cy} r={3.5} fill="#007aff" stroke="#fff" strokeWidth={1.5} /> : null}
                activeDot={{ r: 6, fill: '#007aff', stroke: '#fff', strokeWidth: 2 }}
              />
              <Line
                type="monotone"
                dataKey="p15"
                stroke="#ff3b30"
                strokeWidth={3}
                dot={(props) => props.payload.is_milestone ? <circle cx={props.cx} cy={props.cy} r={3.5} fill="#ff3b30" stroke="#fff" strokeWidth={1.5} /> : null}
                activeDot={{ r: 6, fill: '#ff3b30', stroke: '#fff', strokeWidth: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Legend */}
      {data?.monthly_bars?.length > 0 && (
        <div style={{ display: 'flex', gap: 14, fontSize: 11, fontWeight: 600, color: '#8e8e93', marginBottom: 14, paddingLeft: 2, justifyContent: 'center' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{ width: 8, height: 8, borderRadius: 2, background: '#ff3b30' }} />
            Bear Case
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{ width: 8, height: 8, borderRadius: 2, background: '#007aff' }} />
            Base Case
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{ width: 8, height: 8, borderRadius: 2, background: '#34c759' }} />
            Bull Case
          </span>
        </div>
      )}

      {/* Outcome trio */}
      <div className="outcome-row">
        {!data?.outcomes ? (
          <>
            <Skel h={60} r={14} />
            <Skel h={60} r={14} />
            <Skel h={60} r={14} />
          </>
        ) : (
          <>
            <div className="outcome-item">
              <div className="outcome-label">Bear Case</div>
              <div className="outcome-value" style={{ color: '#ff3b30' }}>
                {fmtShort(data.outcomes.pessimistic)}
                {data.cagrs && (
                  <span style={{ fontSize: 10, opacity: 0.8, marginLeft: 4 }}>
                    ({data.cagrs.pessimistic > 0 ? '+' : ''}{data.cagrs.pessimistic.toFixed(1)}%)
                  </span>
                )}
              </div>
            </div>
            <div className="outcome-item" style={{ background: 'linear-gradient(135deg,rgba(0,122,255,0.08),rgba(88,86,214,0.08))', border: '1.5px solid rgba(0,122,255,0.18)' }}>
              <div className="outcome-label" style={{ color: '#007aff' }}>Base Case</div>
              <div className="outcome-value" style={{ color: '#007aff' }}>
                {fmtShort(data.outcomes.expected)}
                {data.cagrs && (
                  <span style={{ fontSize: 10, opacity: 0.8, marginLeft: 4 }}>
                    ({data.cagrs.expected > 0 ? '+' : ''}{data.cagrs.expected.toFixed(1)}%)
                  </span>
                )}
              </div>
            </div>
            <div className="outcome-item">
              <div className="outcome-label">Bull Case</div>
              <div className="outcome-value" style={{ color: '#34c759' }}>
                {fmtShort(data.outcomes.optimistic)}
                {data.cagrs && (
                  <span style={{ fontSize: 10, opacity: 0.8, marginLeft: 4 }}>
                    ({data.cagrs.optimistic > 0 ? '+' : ''}{data.cagrs.optimistic.toFixed(1)}%)
                  </span>
                )}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Plain-English insight */}
      <div className="compass-insight">
        {gain === null ? (
          <>
            <Skel h={12} w="80%" style={{ marginBottom: 6 }} />
            <Skel h={12} w="60%" />
          </>
        ) : isPos ? (
          <>Your portfolio is <strong>likely to grow {gain.toFixed(1)}%</strong> over the next 5 years. There's a <strong>{prob}% chance</strong> you end up in profit.</>
        ) : (
          <>Our model shows higher risk over 5 years. Your <strong>{prob}%</strong> profit probability suggests reviewing your allocation.</>
        )}
      </div>

      {/* Legal Disclaimer */}
      <div style={{ fontSize: 9, color: 'var(--text3)', textAlign: 'center', marginTop: 16, padding: '0 8px', lineHeight: 1.4 }}>
        ⚠️ Disclaimer: This is a mathematical projection based on historical returns, not financial advice. Actual results will vary.
      </div>
    </motion.div>
  );
}

/* ─── HOLDING ROW ─── */
function HoldingRow({ symbol, weight, ret_1y, cagr_3y, cagr_5y, idx }) {
  const name = symbol.replace('.NS', '');
  
  const FmtC = ({ v }) => (
    <div style={{ textAlign: 'right' }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: v >= 0 ? '#34c759' : '#ff3b30' }}>
        {v > 0 ? '+' : ''}{v.toFixed(1)}%
      </div>
    </div>
  );

  return (
    <motion.div 
      className="holding-row"
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.4 + idx * 0.05 }}
      style={{
        display: 'grid',
        gridTemplateColumns: '1.2fr 1fr 1fr 1fr',
        alignItems: 'center',
        padding: '14px 4px',
        borderBottom: '1px solid rgba(0,0,0,0.05)'
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <div style={{ fontSize: 12, fontWeight: 800, color: '#1c1c1e', letterSpacing: -0.3 }}>{name}</div>
        <div style={{ fontSize: 9, color: '#8e8e93', fontWeight: 700, letterSpacing: 0.2 }}>{weight.toFixed(1)}% Weight</div>
      </div>

      <FmtC v={ret_1y} />
      <FmtC v={cagr_3y} />
      <FmtC v={cagr_5y} />
    </motion.div>
  );
}

/* ─── HOLDING SKELETON ─── */
const HoldingSkel = () => (
  <div style={{ display: 'flex', gap: 12, padding: '14px 0', borderBottom: '1px solid var(--border)', alignItems: 'center' }}>
    <Skel w={40} h={40} r={12} />
    <div style={{ flex: 1 }}>
      <Skel w="55%" style={{ marginBottom: 6 }} />
      <Skel w="35%" h={11} />
    </div>
    <div>
      <Skel w={60} style={{ marginBottom: 6 }} />
      <Skel w={40} h={11} />
    </div>
  </div>
);

/* ─── AI HEALTH SCORE CARD ─── */
const SCORE_COLORS = {
  A: '#34c759', B: '#007aff', C: '#ff9500', D: '#ff6b00', F: '#ff3b30'
};
const BAR_COLORS = [
  '#007aff',   // diversification
  '#34c759',   // momentum
  '#af52de',   // risk_adjusted
  '#ff9500',   // growth_potential
];
const BAR_LABELS = [
  { key: 'diversification', label: 'Diversification' },
  { key: 'momentum',        label: 'Momentum' },
  { key: 'risk_adjusted',   label: 'Risk-Adjusted' },
  { key: 'growth_potential',label: 'Growth Potential' },
];

function ScoreDial({ score, grade }) {
  const r      = 42;
  const circ   = 2 * Math.PI * r;  // ≈ 263.9
  const offset = circ - (score / 100) * circ;
  const color  = SCORE_COLORS[grade] || '#ff9500';
  const dialRef = useRef(null);

  useEffect(() => {
    if (!dialRef.current) return;
    dialRef.current.style.transition = 'none';
    dialRef.current.style.strokeDashoffset = circ;
    // Trigger reflow so the transition resets
    void dialRef.current.getBoundingClientRect();
    dialRef.current.style.transition = 'stroke-dashoffset 1.4s cubic-bezier(0.4,0,0.2,1)';
    dialRef.current.style.strokeDashoffset = offset;
  }, [score, offset, circ]);

  return (
    <div className="health-dial-wrap">
      <svg width="100" height="100" viewBox="0 0 100 100">
        {/* Track */}
        <circle cx="50" cy="50" r={r} fill="none" stroke="#f2f2f7" strokeWidth="8" />
        {/* Progress */}
        <circle
          ref={dialRef}
          cx="50" cy="50" r={r}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={circ}
          style={{ filter: `drop-shadow(0 0 6px ${color}55)` }}
        />
      </svg>
      <div className="health-dial-inner">
        <div className="health-dial-score" style={{ color }}>{score}</div>
        <div className="health-dial-label">/ 100</div>
      </div>
    </div>
  );
}

function AIHealthScoreCard({ profileId }) {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    const controller = new AbortController();
    let isActive = true;
    let timedOut = false;
    const timeoutId = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, 15000);

    setLoading(true);
    setError(null);
    setData(null);

    fetch(`${API}/health-score?profile_id=${profileId}&days=1260&iterations=1000`, {
      signal: controller.signal,
    })
      .then(r => r.json())
      .then(j => {
        if (j.status === 'success') {
          setData(j.data);
        } else {
          setData(null);
          setError(j.message || 'Unknown error');
        }
      })
      .catch(e => {
        if (e.name !== 'AbortError') {
          setData(null);
          setError(e.message);
        } else if (timedOut) {
          setData(null);
          setError('AI health score timed out. Please try again.');
        }
      })
      .finally(() => {
        clearTimeout(timeoutId);
        if (isActive) {
          setLoading(false);
        }
      });

    return () => {
      isActive = false;
      clearTimeout(timeoutId);
      controller.abort();
    };
  }, [profileId]);

  const grade = data?.grade || 'C';
  const subs  = data?.sub_scores || {};
  const narrative = data?.narrative || {};

  return (
    <motion.div
      className="health-card"
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.28, type: 'spring', damping: 22 }}
    >
      {/* Header */}
      <div className="health-card-header">
        <div className="health-title-group">
          <div className="health-icon-wrap">
            <Brain size={18} color="#fff" />
          </div>
          <div>
            <div className="health-title">AI Health Score</div>
            <div className="health-subtitle">Powered by NVIDIA NIM · Llama 3.1 70B</div>
          </div>
        </div>
        {data && (
          <div className={`health-grade-badge ${grade}`}>{grade}</div>
        )}
      </div>

      {/* Loading state */}
      {loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 4 }}>
            <Skel w={100} h={100} r={50} />
            <div style={{ flex: 1 }}>
              <Skel h={14} w="80%" style={{ marginBottom: 8 }} />
              <Skel h={11} w="95%" style={{ marginBottom: 6 }} />
              <Skel h={11} w="70%" />
            </div>
          </div>
          {[1,2,3,4].map(i => (
            <div key={i}>
              <Skel h={10} w="60%" style={{ marginBottom: 5 }} />
              <Skel h={6} r={100} />
            </div>
          ))}
        </div>
      )}

      {/* Error state */}
      {!loading && error && (
        <div style={{ fontSize: 12, color: 'var(--red)', padding: '12px 0', lineHeight: 1.5 }}>
          ⚠️ {error}
        </div>
      )}

      {/* Data */}
      {!loading && data && (
        <>
          {/* Dial + headline */}
          <div className="health-dial-row">
            <ScoreDial score={data.overall_score} grade={grade} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="health-headline">{narrative.headline || 'Portfolio analysis ready'}</div>
              <div className="health-summary">{narrative.summary}</div>
            </div>
          </div>

          {/* Sub-score bars */}
          <div className="health-bars">
            {BAR_LABELS.map(({ key, label }, i) => {
              const sub = subs[key] || {};
              const pct = sub.score ?? 0;
              const barColor = BAR_COLORS[i];
              return (
                <div key={key} className="health-bar-row">
                  <div className="health-bar-meta">
                    <span>{label}</span>
                    <span style={{ color: barColor, fontWeight: 700 }}>{pct}<span style={{ fontWeight: 500, color: 'var(--text3)', fontSize: 10 }}>/100</span> · {sub.label}</span>
                  </div>
                  <div className="health-bar-track">
                    <div className="health-bar-fill" style={{ width: `${pct}%`, background: barColor }} />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Narrative pills */}
          <div className="health-insight-row">
            <div className="health-insight-pill">
              <div className="health-pill-label" style={{ color: '#ff3b30' }}>⚠ Top Risk</div>
              <div className="health-pill-text">{narrative.top_risk || '—'}</div>
            </div>
            <div className="health-insight-pill">
              <div className="health-pill-label" style={{ color: '#34c759' }}>✦ Opportunity</div>
              <div className="health-pill-text">{narrative.top_opportunity || '—'}</div>
            </div>
          </div>

          {/* Action */}
          <div className="health-action-box">
            <div className="health-action-label">🎯 AI Recommendation</div>
            {narrative.action || 'No action needed at this time.'}
          </div>

          {/* AI badge */}
          <div className="health-ai-badge">
            <div className="health-ai-dot" />
            AI · NVIDIA NIM · {data.key_present ? 'Live' : 'Demo Mode'}
          </div>
        </>
      )}
    </motion.div>
  );
}

/* ─── APP ─── */
export default function App() {
  const [allData, setAllData] = useState(() => {
    try {
      const saved = localStorage.getItem('portfolio_cache');
      return saved ? JSON.parse(saved) : {};
    } catch { return {}; }
  });
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('portfolio');
  const [profileId, setProfileId] = useState('sample');

  useEffect(() => {
    const updateData = (id, data) => {
      setAllData(prev => {
        const next = { ...prev, [id]: data };
        localStorage.setItem('portfolio_cache', JSON.stringify(next));
        return next;
      });
    };

    PROFILES.forEach(p => {
      fetch(`${API}/simulate?profile_id=${p.id}&days=1260&iterations=5000`)
        .then(r => r.json())
        .then(j => {
          if (j.status === 'success') {
            updateData(p.id, j.data);
          }
        })
        .catch(err => {
          console.error(`Error loading ${p.id}:`, err);
        });
    });
  }, []); // Run once on mount

  useEffect(() => {
    setLoading(!allData[profileId]);
  }, [profileId, allData]);

  useEffect(() => {
    if (allData[profileId]) return;

    fetch(`${API}/simulate?profile_id=${profileId}&days=1260&iterations=5000`)
      .then(r => r.json())
      .then(j => {
        if (j.status === 'success') {
          setAllData(prev => {
            const next = { ...prev, [profileId]: j.data };
            localStorage.setItem('portfolio_cache', JSON.stringify(next));
            return next;
          });
        }
      })
      .catch(err => {
        console.error(`Error loading ${profileId}:`, err);
      });
  }, [profileId, allData]);

  const data = useMemo(() => allData[profileId], [allData, profileId]);
  const holdingsList = useMemo(() => data?.holdings || [], [data]);

  return (
    <>
    <div className="device">
      <div className="dynamic-island" />

      {/* Status bar */}
      <div className="status-bar">
        <span className="status-time">9:41</span>
        <div className="status-icons">
          <Signal size={13} strokeWidth={2.5} />
          <Wifi size={13} strokeWidth={2.5} />
          <Battery size={14} strokeWidth={2.5} />
        </div>
      </div>

      {/* Main screen */}
      <div className="screen">

        {/* Greeting row */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div>
            <div style={{ fontSize: 13, color: 'var(--text3)', fontWeight: 500, marginBottom: 2 }}>Welcome to,</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ fontSize: 24, fontWeight: 800, letterSpacing: -0.6 }}>Portfolio Compass 🧭</div>
              <div style={{ position: 'relative' }}>
                <select 
                  value={profileId}
                  onChange={(e) => setProfileId(e.target.value)}
                  style={{
                    position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer', width: '100%'
                  }}
                >
                  {PROFILES.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
                <div style={{ background: 'rgba(0,122,255,0.08)', padding: '4px 8px', borderRadius: 8, fontSize: 10, fontWeight: 700, color: 'var(--blue)', border: '1px solid rgba(0,122,255,0.1)', pointerEvents: 'none', display: 'flex', alignItems: 'center', gap: 4 }}>
                  {PROFILES.find(p => p.id === profileId)?.name}
                  <ChevronDown size={10} />
                </div>
              </div>
            </div>
          </div>
          <div style={{ position: 'relative', cursor: 'pointer' }}>
            <div style={{ width: 42, height: 42, borderRadius: '50%', background: 'linear-gradient(135deg,#007aff,#5856d6)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ color: '#fff', fontWeight: 700, fontSize: 15 }}>{data?.user_name?.[0] || 'A'}</span>
            </div>
            <div style={{ position: 'absolute', top: 1, right: 1, width: 10, height: 10, background: '#ff3b30', border: '2px solid var(--bg)', borderRadius: '50%' }} />
          </div>
        </div>

        {/* Hero balance */}
        <motion.div
          className="hero-card"
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ type: 'spring', damping: 22 }}
        >
          <div className="hero-label">Total Portfolio Value</div>
          {loading && !data
            ? <Skel h={42} w="70%" r={10} style={{ marginBottom: 10 }} />
            : <div className="hero-amount">{fmtShort(data?.current_value)}</div>
          }
          <div className="hero-change">
            <TrendingUp size={13} />
            +2.38% today
          </div>
        </motion.div>

        {/* Quick stats */}
        <motion.div
          className="quick-stats"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.12 }}
        >
          <div className="stat-mini">
            <div className="stat-mini-label">Day's Gain</div>
            <div className="stat-mini-value" style={{ color: 'var(--green)' }}>
              {loading || !data ? <Skel h={20} w="70%" /> : `+${fmtShort(data.current_value * 0.0238)}`}
            </div>
          </div>
          <div className="stat-mini">
            <div className="stat-mini-label">Profit Probability</div>
            <div className="stat-mini-value">
              {loading || !data ? <Skel h={20} w="50%" /> : `${(data.prob_profit * 100).toFixed(0)}%`}
            </div>
          </div>
        </motion.div>

        {/* ── PORTFOLIO COMPASS ── */}
        <CompassCard
          data={data}
          loading={loading}
        />

        {/* ── AI HEALTH SCORE ── */}
        <AIHealthScoreCard profileId={profileId} />

        {/* Holdings header */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr 1fr', padding: '0 4px', marginBottom: 4 }}>
          <div style={{ fontSize: 10, fontWeight: 800, color: '#8e8e93', letterSpacing: 1 }}>ASSET / WEIGHT</div>
          <div style={{ fontSize: 10, fontWeight: 800, color: '#8e8e93', letterSpacing: 1, textAlign: 'right' }}>1Y RET</div>
          <div style={{ fontSize: 10, fontWeight: 800, color: '#8e8e93', letterSpacing: 1, textAlign: 'right' }}>3Y CAGR</div>
          <div style={{ fontSize: 10, fontWeight: 800, color: '#8e8e93', letterSpacing: 1, textAlign: 'right' }}>5Y CAGR</div>
        </div>

        {/* Holdings list */}
        {loading && !data
          ? Array.from({ length: 4 }).map((_, i) => <HoldingSkel key={i} />)
          : (data?.holdings || []).map((h, i) => <HoldingRow key={h.symbol} {...h} idx={i} />)
        }

      </div>

      {/* Bottom nav */}
      <div className="navbar">
        {[
          { id: 'home', label: 'Home', Icon: Home },
          { id: 'portfolio', label: 'Portfolio', Icon: Briefcase },
          { id: 'antara', label: 'Antara', Icon: BarChart2 },
          { id: 'alerts', label: 'Alerts', Icon: Bell },
          { id: 'account', label: 'Account', Icon: User },
        ].map(({ id, label, Icon }) => (
          <div
            key={id}
            className={`nav-item ${tab === id ? 'active' : ''}`}
            onClick={() => setTab(id)}
          >
            <Icon size={24} strokeWidth={tab === id ? 2.5 : 1.8} />
            <span className="nav-label">{label}</span>
          </div>
        ))}
        <div className="home-bar" />
      </div>
    </div>

    {/* ── Antara Full-Screen Overlay ── */}
    {tab === 'antara' && (
      <div style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        background: '#2B1055',
        display: 'flex',
        flexDirection: 'column',
      }}>
        {/* Back button */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          zIndex: 10000,
          padding: '12px 16px',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          background: 'linear-gradient(180deg, rgba(43,16,85,0.95) 0%, transparent 100%)',
          pointerEvents: 'none',
        }}>
          <button
            onClick={() => setTab('portfolio')}
            style={{
              pointerEvents: 'auto',
              background: 'rgba(255,255,255,0.12)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: 20,
              color: '#fff',
              padding: '7px 14px',
              cursor: 'pointer',
              backdropFilter: 'blur(12px)',
              fontSize: 12,
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: 5,
              letterSpacing: 0.3,
            }}
          >
            <ArrowLeft size={13} strokeWidth={2.5} />
            Portfolio Compass
          </button>
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', fontWeight: 600, letterSpacing: 1, textTransform: 'uppercase' }}>
            Antara
          </div>
        </div>

        {/* Antara app iframe */}
        <iframe
          src="/antara.html"
          style={{
            width: '100%',
            height: '100%',
            border: 'none',
            display: 'block',
          }}
          title="Antara — Portfolio & Trading"
          allow="autoplay"
        />
      </div>
    )}
    </>
  );
}
