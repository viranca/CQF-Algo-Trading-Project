# CQF Final Project — End-to-End Algorithmic Trading System

A containerized, research-to-production algorithmic trading system built for the
**Certificate in Quantitative Finance (CQF)** final project, **supervised by Dr. Paul Wilmott**
with guidance from **Kannan Singaravelu**.

The system covers the full lifecycle — **multi-source market data → storage → signal research →
backtesting → live execution** — with each stage running as its own Docker service.

> **Honest result up front:** the goal of this project was to build the full pipeline end to end.
> The strategies themselves **did not achieve positive risk-adjusted returns** — overall return
> was negative and the Sharpe ratio was near zero. The value here is the engineering and the
> research workflow, not a profitable strategy.

---

## Architecture

```
Data sources            Storage                Research               Execution
────────────            ───────                ────────               ─────────
Yahoo Finance  ┐                          ┌─ data-quality checks
Alpaca         ├─►  PostgreSQL / TimescaleDB ─┼─ backtesting          ┌─ order routing
Interactive    ┘    (daily + minute bars)    └─ signal generation ───►│  (Alpaca / IBKR
Brokers                                                                └─  gateway)
                         all services orchestrated with Docker Compose
```

- **Ingestion** — daily and minute bars pulled from **Yahoo Finance**, **Alpaca**, and
  **Interactive Brokers** (via the IB Gateway), each in its own container.
- **Storage** — **PostgreSQL** and **TimescaleDB** (a PostgreSQL extension optimized for
  time series), initialized from SQL scripts.
- **Data quality** — a dedicated service (`Research/data_quality/dq_control.py`) validates
  availability/consistency before signals are computed.
- **Strategies** — **trend-following** (EMA crossover filtered by ADX) and **mean-reversion**
  (rolling z-score), at daily and minute frequencies.
- **Backtesting** — portfolio value, drawdowns, and risk-adjusted returns, in Python/Pandas.
- **Execution** — order placement (`Trading/execution/`) and monitoring via the Alpaca broker
  API and the Interactive Brokers gateway.

---

## Repository structure

| Path | What it is |
| ---- | ---------- |
| `Research/alpaca/`, `Research/yfinance/`, `Research/interactive_brokers/` | Market-data ingestion (daily + minute) per source. |
| `Research/postgresql/`, `Research/timescaledb/` | Database services + init scripts. |
| `Research/data_quality/` | Data-quality control service. |
| `Research/generic_strategies/` | Strategy logic + technical indicators (`ADX`, `EMA`, `rolling_z_score`). |
| `Research/backtest/` | Backtests for the mean-reversion and trend-following strategies. |
| `Research/docker-compose-research.yml` | Orchestrates the research stack. |
| `Trading/execution/`, `Trading/monitoring/` | Live order routing and monitoring. |
| `Research/interactive_brokers/ib-gateway-docker-master/` | Vendored third-party [ib-gateway-docker](https://github.com/gnzsnz/ib-gateway-docker) (Dockerized IB Gateway). |
| `test_scripts/` | Standalone connectivity/indicator/signal smoke tests. |
| `(AL) VIRANCA BALSINGH REPORT.pdf` | The 25-page final project report. |
| `Exam Reports/` | Companion CQF exam reports (see below). |

### Companion CQF exam work (`Exam Reports/`)

- **Exam 1** — portfolio theory & risk (GMV portfolio, analytical Value-at-Risk).
- **Exam 2** — **options pricing under the Heston stochastic-volatility model** (Euler–Maruyama
  Monte Carlo), with interest-rate and sensitivity extensions.
- **Exam 3** — a **machine-learning trend classifier** (SVM with GridSearchCV, ROC/AUC).

---

## Running it

The stack is Docker-based. Configuration for the IB Gateway lives in `Research/.env` — copy the
template and fill in your own values (the committed `.env` contains no real credentials):

```bash
cp Research/.env.example Research/.env    # then edit with your own IBKR/paper-trading settings
```

Bring up the research stack:

```bash
docker-compose -f Research/docker-compose-research.yml up --build
```

Individual services can be built from their own `Dockerfile.*` (Postgres, TimescaleDB, each data
source, backtest, strategies, data-quality). The Interactive Brokers gateway runs from the
vendored `ib-gateway-docker` compose file under `Research/interactive_brokers/`.

> Note: database credentials in the scripts (`DB_PASSWORD`) are a throwaway local default for the
> containerized Postgres, not a real secret.

---

## Notes & honesty

- This is a **learning / research** system, not production trading infrastructure.
- Backtested strategies underperformed (negative return, ~0 Sharpe); results are reported as-is.
- The IB Gateway Docker setup under `interactive_brokers/ib-gateway-docker-master/` is
  third-party open-source software, included for reproducibility and credited above.

---

*Author: Viranca Balsingh — CQF Final Project, 2025. Supervised by Dr. Paul Wilmott; guidance from Kannan Singaravelu.*
