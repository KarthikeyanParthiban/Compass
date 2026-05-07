import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area 
} from 'recharts';
import { 
  Plus, Trash2, TrendingUp, AlertTriangle, CheckCircle, RefreshCw, BarChart3, Info, IndianRupee, Activity
} from 'lucide-react';
import { CONFIG } from './config';

const App = () => {
  const [holdings, setHoldings] = useState([
    { symbol: "SHRIRAMFIN.NS", quantity: 158, value: 150842 },
    { symbol: "SBIN.NS", quantity: 10, value: 10524 },
    { symbol: "LLOYDSME.NS", quantity: 28, value: 49490 }
  ]);
  
  const [apiKey, setApiKey] = useState(localStorage.getItem('compass_api_key') || '');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    localStorage.setItem('compass_api_key', apiKey);
  }, [apiKey]);

  const addHolding = () => {
    setHoldings([...holdings, { symbol: "", quantity: 0, value: 0 }]);
  };

  const removeHolding = (index) => {
    setHoldings(holdings.filter((_, i) => i !== index));
  };

  const updateHolding = (index, field, val) => {
    const newHoldings = [...holdings];
    newHoldings[index][field] = field === 'symbol' ? val.toUpperCase() : Number(val);
    setHoldings(newHoldings);
  };

  const runSimulation = async () => {
    if (!apiKey) {
      setError("Please enter your API Key in the settings below.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(CONFIG.API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": apiKey
        },
        body: JSON.stringify({
          portfolio_id: "dashboard_user_" + Date.now(),
          holdings: holdings,
          num_sims: 1000,
          horizon_months: 60
        })
      });

      if (!response.ok) throw new Error("API request failed: " + response.statusText);
      
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Prepare chart data
  const chartData = result ? result.scenarios.expected.monthly_values.map((val, i) => ({
    month: i,
    expected: val,
    optimistic: result.scenarios.optimistic.monthly_values[i],
    pessimistic: result.scenarios.pessimistic.monthly_values[i]
  })) : [];

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <header className="flex justify-between items-end mb-8 animate-fade-in">
          <div>
            <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-teal-200">
              Compass Monte Carlo
            </h1>
            <p className="text-zinc-400 mt-2">Institutional-grade portfolio projection & risk engine</p>
          </div>
          <div className="hidden md:flex gap-4">
             <div className="text-right">
                <p className="text-xs text-zinc-500 uppercase tracking-widest">Market Data</p>
                <p className="text-sm font-medium text-emerald-400 flex items-center gap-1">
                  <Activity size={14} /> LIVE (5Y History)
                </p>
             </div>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Sidebar: Inputs */}
          <div className="lg:col-span-4 space-y-6">
            <div className="glass-card p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold flex items-center gap-2">
                  <BarChart3 size={20} className="text-emerald-400" /> Portfolio Holdings
                </h2>
                <button onClick={addHolding} className="p-2 hover:bg-white/5 rounded-full transition-colors text-emerald-400">
                  <Plus size={20} />
                </button>
              </div>

              <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                {holdings.map((h, i) => (
                  <div key={i} className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-3 group transition-all hover:border-white/10">
                    <div className="flex justify-between items-center">
                      <input 
                        className="bg-transparent border-none font-bold text-white focus:ring-0 w-full"
                        placeholder="SYMBOL.NS"
                        value={h.symbol}
                        onChange={(e) => updateHolding(i, 'symbol', e.target.value)}
                      />
                      <button onClick={() => removeHolding(i)} className="text-zinc-500 hover:text-rose-400 transition-colors opacity-0 group-hover:opacity-100">
                        <Trash2 size={16} />
                      </button>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-[10px] uppercase text-zinc-500 block mb-1">Quantity</label>
                        <input 
                          type="number"
                          className="glass-input w-full text-sm"
                          value={h.quantity}
                          onChange={(e) => updateHolding(i, 'quantity', e.target.value)}
                        />
                      </div>
                      <div>
                        <label className="text-[10px] uppercase text-zinc-500 block mb-1">Value (INR)</label>
                        <input 
                          type="number"
                          className="glass-input w-full text-sm"
                          value={h.value}
                          onChange={(e) => updateHolding(i, 'value', e.target.value)}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <button 
                onClick={runSimulation}
                disabled={loading}
                className="btn-primary w-full mt-6 flex items-center justify-center gap-2"
              >
                {loading ? <RefreshCw className="animate-spin" size={18} /> : "Run Simulation"}
              </button>
            </div>

            {/* API Settings */}
            <div className="glass-card p-6 border-zinc-800">
               <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                 <Info size={14} /> API Configuration
               </h3>
               <div className="space-y-2">
                 <label className="text-[10px] uppercase text-zinc-500 block">x-api-key</label>
                 <input 
                    type="password"
                    className="glass-input w-full text-xs"
                    placeholder="Enter your API key..."
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                 />
                 <p className="text-[9px] text-zinc-600">Saved securely in browser storage.</p>
               </div>
               
               {error && (
                 <div className="mt-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
                   <AlertTriangle size={14} /> {error}
                 </div>
               )}
            </div>

            {result && (
              <div className="glass-card p-6 border-emerald-500/20 bg-emerald-500/5">
                <h3 className="text-sm font-semibold text-emerald-400 uppercase tracking-widest mb-4">Risk Probability</h3>
                <div className="space-y-6">
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-zinc-400">Prob. of Profit</span>
                      <span className="text-emerald-400 font-bold">{result.probability_scores.probability_of_profit}%</span>
                    </div>
                    <div className="w-full bg-zinc-800 rounded-full h-1.5">
                      <div className="bg-emerald-500 h-1.5 rounded-full transition-all duration-1000" style={{ width: `${result.probability_scores.probability_of_profit}%` }}></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-zinc-400">Prob. of Doubling</span>
                      <span className="text-teal-400 font-bold">{result.probability_scores.probability_of_doubling}%</span>
                    </div>
                    <div className="w-full bg-zinc-800 rounded-full h-1.5">
                      <div className="bg-teal-500 h-1.5 rounded-full transition-all duration-1000" style={{ width: `${result.probability_scores.probability_of_doubling}%` }}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Main Content: Results */}
          <div className="lg:col-span-8 space-y-6">
            {!result && !loading && (
              <div className="glass-card h-[600px] flex flex-col items-center justify-center text-center p-12">
                <div className="w-20 h-20 rounded-full bg-emerald-500/10 flex items-center justify-center mb-6">
                  <TrendingUp size={40} className="text-emerald-400" />
                </div>
                <h2 className="text-2xl font-bold mb-2">Ready for Simulation</h2>
                <p className="text-zinc-500 max-w-sm">Configure your portfolio on the left and run the Monte Carlo engine to visualize 5-year projections.</p>
              </div>
            )}

            {loading && (
              <div className="glass-card h-[600px] flex flex-col items-center justify-center text-center p-12">
                <RefreshCw size={48} className="text-emerald-400 animate-spin mb-6" />
                <h2 className="text-2xl font-bold mb-2">Crunching Numbers...</h2>
                <p className="text-zinc-500 max-w-sm">SageMaker is currently running 1,000 correlated simulations using Student-t distribution and historical volatility.</p>
              </div>
            )}

            {result && (
              <div className="animate-fade-in space-y-6">
                {/* Dashboard Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="glass-card p-6">
                    <p className="text-zinc-500 text-xs uppercase mb-1">Current Value</p>
                    <p className="text-2xl font-bold flex items-center gap-1">
                      <IndianRupee size={20} className="text-emerald-400" /> {result.current_value.toLocaleString()}
                    </p>
                  </div>
                  <div className="glass-card p-6 border-emerald-500/30">
                    <p className="text-emerald-400 text-xs uppercase mb-1">Bull Case (5Y)</p>
                    <p className="text-2xl font-bold">₹{result.scenarios.optimistic.terminal_value.toLocaleString()}</p>
                    <p className="text-xs text-emerald-400/60">+{result.scenarios.optimistic.cagr_pct}% CAGR</p>
                  </div>
                  <div className="glass-card p-6 border-rose-500/30">
                    <p className="text-rose-400 text-xs uppercase mb-1">Bear Case (5Y)</p>
                    <p className="text-2xl font-bold">₹{result.scenarios.pessimistic.terminal_value.toLocaleString()}</p>
                    <p className="text-xs text-rose-400/60">{result.scenarios.pessimistic.cagr_pct}% CAGR</p>
                  </div>
                </div>

                {/* Main Chart */}
                <div className="glass-card p-6 h-[500px]">
                  <div className="flex justify-between items-center mb-8">
                    <h3 className="text-xl font-semibold flex items-center gap-2">
                      <Activity size={20} className="text-emerald-400" /> 5-Year Projection Trajectory
                    </h3>
                  </div>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#222" vertical={false} />
                      <XAxis 
                        dataKey="month" 
                        stroke="#666" 
                        fontSize={12} 
                        tickLine={false} 
                        axisLine={false}
                        tickFormatter={(v) => v % 12 === 0 ? `Yr ${v/12}` : ''}
                      />
                      <YAxis 
                        stroke="#666" 
                        fontSize={12} 
                        tickLine={false} 
                        axisLine={false}
                        tickFormatter={(v) => `₹${(v/100000).toFixed(1)}L`}
                      />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#111', borderColor: '#333', borderRadius: '8px' }}
                        itemStyle={{ fontSize: '12px' }}
                        formatter={(v) => [`₹${v.toLocaleString()}`, '']}
                        labelFormatter={(l) => `Month ${l}`}
                      />
                      <Line type="monotone" dataKey="optimistic" stroke="#10b981" strokeWidth={2} dot={false} strokeDasharray="5 5" opacity={0.5} />
                      <Line type="monotone" dataKey="expected" stroke="#10b981" strokeWidth={4} dot={false} />
                      <Line type="monotone" dataKey="pessimistic" stroke="#f43f5e" strokeWidth={2} dot={false} strokeDasharray="5 5" opacity={0.5} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                {/* Risk Warning */}
                <div className="p-4 rounded-xl bg-rose-500/5 border border-rose-500/20 flex items-start gap-4">
                   <AlertTriangle className="text-rose-500 mt-1" size={20} />
                   <div>
                      <h4 className="text-rose-400 font-semibold text-sm">Worst Case Scenario (VaR)</h4>
                      <p className="text-xs text-rose-500/70 mt-1">
                        There is a 5% statistical probability that your portfolio could see a drawdown of <strong>{result.probability_scores.var_drawdown_pct}%</strong> within this horizon. This simulation uses historical fat-tailed volatility.
                      </p>
                   </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
