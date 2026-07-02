# Economic Simulation World Engine

A real-time agent-based economic simulation with a live analytics dashboard. Workers earn wages, spend money, and save. Businesses hire, produce, price goods, and chase profit. A government collects taxes and pays unemployment benefits. Watch the whole economy evolve over 120 months — then inject a recession or stimulus and see what happens.

![Dashboard Screenshot](screenshot.png)

---

## Features

- **Live dashboard** — 6 real-time charts (GDP, unemployment, inflation, consumer spending, wages & prices, government finance) updating as the simulation runs
- **Stat cards with sparklines** — every key metric has a 60-point mini trend chart and a % change indicator
- **AI Analysis strip** — plain-English summary of what the economy is doing right now (growth trend, jobs market, price pressure, consumer confidence)
- **Event log** — automatically flags notable moments (hiring surges, contractions, deflation, shocks)
- **30-month milestone reports** — the simulation pauses every 30 months and shows a detailed popup with embedded mini-charts, a metrics table with period-over-period deltas, a written narrative, and forward-looking watch items
- **Shock injection** — trigger a recession, boom, inflation spike, or government stimulus at any point
- **Randomised starting conditions** — every run produces a different economy (worker count, wages, prices, tax rate all vary)
- **Variable simulation speed** — Slow / Normal / Fast / Max

---

## How It Works

The simulation is built around three interacting agent types:

### Workers
Each of the 50–200 workers has an individual **marginal propensity to consume (MPC)** — how much of their income they spend vs. save. Employed workers receive a net wage; unemployed workers receive a government benefit. Workers adjust their spending based on a **consumer sentiment index** derived from recent GDP trends, unemployment direction, and inflation.

### Businesses
Each firm picks from four industries (**food, tech, housing, services**), each with different price sensitivity and production rates. Businesses:
- Produce goods based on recent sales trends (not just raw capacity)
- Adjust prices up when demand exceeds supply, down when shelves pile up
- Raise wages when margins are healthy, trim them when losing money
- Hire when profits are growing or sales are trending up; fire after enough consecutive losses

### Government
Acts as an **automatic stabiliser**:
- Collects income tax from employed workers
- Pays flat unemployment benefits to jobless workers
- Recycles tax revenue back into the market as government spending (closes the Keynesian savings leakage)
- Gradually lowers the tax rate in a slump, raises it in a boom

### Market
A single central market aggregates supply from all businesses and demand from all workers each month, clears trades proportionally to inventory share, then signals each business to adjust its price.

---

## Economic Concepts Demonstrated

| Concept | Where it appears |
|---|---|
| Keynesian circular flow | Government spending + investment recycling closes the savings gap |
| Marginal propensity to consume | Per-worker MPC drives spending decisions |
| Automatic fiscal stabilisers | Tax rate adjusts counter-cyclically with unemployment |
| Supply & demand price discovery | Market demand/supply ratio drives business price adjustments |
| Business cycle | Boom → overheating → layoffs → slump → recovery emerges naturally |
| Consumer sentiment | Confidence index scales household spending based on GDP trend, unemployment, and inflation |
| Cost-push vs. demand-pull inflation | Both can emerge depending on shock type and market conditions |
| Unemployment equilibrium | Full employment creates wage pressure; recessions spike unemployment |

---

## Getting Started

**Requirements:** Python 3.10+

```bash
pip install -r requirements.txt
python main.py
```

The dashboard window opens immediately. Press **▶ Start** to run the simulation.

---

## Dashboard Controls

| Control | What it does |
|---|---|
| ▶ Start / ⏸ Pause | Run or pause the simulation |
| ↺ Reset | Start a brand-new randomised economy |
| Speed selector | Slow (600 ms/step) → Max (5 ms/step) |
| Shock dropdown + ⚡ Apply | Inject an economic shock at the current month |

### Shock Types

- **Recession** — consumer confidence collapses, MPCs fall, a third of businesses suddenly shed workers
- **Boom** — household savings surge, spending propensity rises
- **Inflation Spike** — cost-push shock raises all business prices by ~30%
- **Stimulus** — government direct transfer to every worker (helicopter money)

---

## Project Structure

```
EconSim/
├── main.py          # Entry point — launches the GUI
├── dashboard.py     # Tkinter + Matplotlib live dashboard and report windows
├── economy.py       # Top-level simulation orchestrator and Government class
├── agents.py        # Worker and Business agent classes
├── market.py        # Supply/demand aggregation, market clearing, price adjustment
├── stats.py         # Per-step metric recording
└── requirements.txt
```

---

## Tech Stack

- **Python 3.10+**
- **Tkinter** — GUI framework (standard library)
- **Matplotlib** — embedded live charts (`TkAgg` backend)
- No external simulation libraries — all economic logic is hand-written

---

## Example Scenarios to Try

1. **Let it run naturally** — watch a business cycle emerge on its own around month 40–60
2. **Recession at month 20** — inject a recession early and see how long recovery takes
3. **Stimulus response** — trigger a recession, wait 10 months, then apply stimulus and watch GDP recover
4. **Inflation spike** — fire an inflation spike in a booming economy and observe stagflation dynamics
5. **Reset repeatedly** — because starting conditions are randomised, every run tells a different story
"# EconomicWorldSim" 
