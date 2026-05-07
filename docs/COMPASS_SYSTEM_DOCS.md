# Project Compass: Institutional-Grade Portfolio Intelligence

**Project Compass** is a high-fidelity financial analysis platform designed to bridge the gap between complex institutional quantitative modeling and intuitive retail investment insights. By combining advanced probabilistic simulations with cutting-edge Large Language Models (LLMs), Compass provides a 360-degree view of portfolio health, risk, and future performance.

---

## 1. Executive Summary (The "What" and "Why")

### What is Compass?
Compass is a sophisticated "Portfolio GPS." It doesn't just show where your money is today; it uses advanced mathematics and AI to project where it could be in 5 years, how likely you are to make a profit, and exactly what risks might derail your strategy.

### Why was it built?
Most retail investors rely on "rear-view mirror" metrics (historical returns). Compass introduces **Forward-Looking Analytics**, allowing users to stress-test their portfolios against thousands of simulated market conditions, including crashes and bull runs, before they happen.

---

## 2. Key Features

### 🛡️ AI Portfolio Health Score
A proprietary scoring engine that evaluates your portfolio across four dimensions:
1.  **Diversification**: Measured via the Herfindahl-Hirschman Index (HHI) to ensure you aren't over-exposed to a single stock.
2.  **Momentum**: Analysis of recent price action across all holdings.
3.  **Risk-Adjusted Stability**: Evaluating the probability of profit relative to potential drawdowns.
4.  **Growth Potential**: Forecasting long-term CAGR based on simulated median outcomes.

### 🔮 Probabilistic Forecasting (Monte Carlo)
Compass runs **1,000+ simulations** for every portfolio. Instead of a single "expected" return, you get a probability cloud:
*   **Pessimistic Case**: What happens if the market underperforms?
*   **Expected Case**: The most likely outcome.
*   **Optimistic Case**: The potential upside in a strong bull market.

### 🤖 AI Narrative Insights
Powered by **NVIDIA NIM (Llama 3.1-70B)**, the system translates complex numbers into professional, actionable advice. It identifies your "Top Risk" and "Top Opportunity" in plain English, providing a human-like second opinion on your investments.

### 📊 Institutional Risk Metrics
*   **Value at Risk (VaR)**: Quantifies the maximum expected loss over a specific timeframe at a 95% confidence level.
*   **Reliability Score**: A walk-forward validation metric that proves the simulation's accuracy against historical data.

---

## 3. Technical Architecture (The "How")

### High-Level Stack
| Component | Technology | Role |
| :--- | :--- | :--- |
| **Frontend** | React / Vite / Tailwind | Premium, high-performance UI/UX. |
| **Backend** | FastAPI (Python) | High-concurrency API for heavy computations. |
| **Sim Engine** | NumPy / Pandas | Vectorized financial modeling. |
| **AI Intelligence**| NVIDIA NIM / Llama 3.1 | Qualitative narrative generation. |
| **Data Sourcing** | yfinance / Groww API | Historical price ingestion. |
| **Caching** | Disk-level Parquet/JSON | Sub-second latency for repeat simulations. |

### The Mathematics of Compass
Compass doesn't just use simple averages. It employs:
1.  **Geometric Brownian Motion (GBM)**: The industry standard for modeling stock price paths.
2.  **Student’s T-Distribution**: Unlike a "Normal" distribution, this accounts for "Fat Tails"—the reality that market crashes happen more often than simple bell curves predict.
3.  **Cholesky Decomposition**: A method to ensure that when one stock in your portfolio moves, its correlated peers (e.g., TCS and Infosys) move together realistically in the simulation.

### Data Flow
1.  **Ingestion**: Backend fetches 5 years of daily price data for all symbols.
2.  **Correlation Matrix**: Calculates how every stock moves in relation to others.
3.  **Simulation Loop**: Generates 1,000+ random paths using correlated T-distributed shocks.
4.  **Aggregation**: Compiles paths into percentiles (15th, 50th, 85th).
5.  **AI Analysis**: Sends quantitative results to NVIDIA NIM for the final narrative layer.

---

## 4. User Personas (Profiles)

Compass comes pre-loaded with curated investment strategies to showcase its versatility:
*   **Passive Index Follower (Siddharth)**: Focused on low-cost ETFs and steady growth.
*   **Growth-Focused Retail (Priyanka)**: Concentrated in high-beta, high-growth Indian equities.
*   **Dividend Income Seeker (Vikram)**: Optimized for cash flow and capital preservation.
*   **Tech Visionary (Ishita)**: High-exposure to the technology and digital transformation sector.

---

## 5. Developer Guide (Setup & Installation)

### Prerequisites
*   Python 3.10+
*   Node.js (for frontend)
*   NVIDIA API Key (optional, for AI features)

### Backend Setup
1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Environment Variables**:
    Create a `.env` file in the root:
    ```env
    NVIDIA_API_KEY=your_key_here
    ```
3.  **Run Server**:
    ```bash
    python api.py
    ```

### Frontend Setup
1.  **Navigate to directory**:
    ```bash
    cd frontend
    ```
2.  **Install & Run**:
    ```bash
    npm install
    npm run dev
    ```

---

## 6. Design Philosophy

The Compass UI is built on a **"Dark Mode First"** aesthetic, using:
*   **Vibrant Gradients**: To represent growth and optimism.
*   **Glassmorphism**: For a modern, layered feel.
*   **Micro-animations**: To keep the interface alive while heavy simulations run in the background.

---

**Compass** is a decision-support system designed for the modern investor who demands institutional precision without the institutional complexity.
