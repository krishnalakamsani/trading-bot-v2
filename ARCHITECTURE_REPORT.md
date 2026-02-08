# Trading Bot V2 — End-to-End Architecture Walkthrough

_Date: 2026-02-06_

## 1. High-level purpose of the application

### What problem it solves
This is an automated intraday options trading bot for NSE/BSE indices that executes a rules-based strategy (SuperTrend, optionally MACD-confirmed) and tracks trades, P&L, and analytics.

It solves: “run a simple discretionary-style intraday options system automatically, with guardrails (max loss, max trades), plus a live dashboard.”

### Who it is for
A single trader/operator (or small team) who wants to run and monitor an index options bot (NIFTY/BANKNIFTY/SENSEX/FINNIFTY) and later review performance.

### What kind of system it is
- Backend: Python FastAPI service exposing REST endpoints + WebSocket stream and running an in-process trading engine loop.
- Frontend: React dashboard (SPA) consuming REST + WebSocket.
- Database: SQLite for trades/config/candle snapshots.

## 2. Architecture overview

### Components/modules
Backend (Python):
- backend/server.py — FastAPI routes + WebSocket manager
- backend/bot_service.py — interface layer between API and engine
- backend/trading_bot.py — trading engine loop (entries/exits)
- backend/dhan_api.py — Dhan broker SDK wrapper
- backend/indicators.py — SuperTrend + MACD implementations
- backend/utils.py — market-hours/time helpers
- backend/indices.py — index metadata (lot sizes, strike rounding)
- backend/database.py — SQLite persistence + analytics
- backend/config.py — global runtime state + config dicts
- backend/models.py — request models (Pydantic)

Frontend (React):
- frontend/src/App.js — routing, global state, REST + WebSocket wiring
- frontend/src/pages/Dashboard.jsx — dashboard layout
- frontend/src/pages/Settings.jsx — credentials + risk params
- frontend/src/pages/TradesAnalysis.jsx — analytics UI
- frontend/src/components/* — panels/widgets

Infra:
- docker-compose.yml — runs backend (8001) + frontend (80)
- frontend/nginx.conf — proxies /api and /ws to backend in Docker

### How they interact
- REST calls: React UI calls /api/* endpoints → FastAPI server delegates to bot_service and database.
- WebSocket: UI connects to /ws → trading loop broadcasts “state_update” snapshots via server.ConnectionManager.
- Persistence: bot writes trades, candle telemetry, and config into SQLite (backend/data/trading.db).

### Data flow (from input to output)
1) Operator updates settings in UI → POST /api/config/update → bot_service updates config dict → database.save_config persists.
2) Operator clicks Start → POST /api/bot/start → TradingBot.start spawns TradingBot.run_loop() asyncio task.
3) Bot loop fetches spot/option prices via DhanAPI (live) or simulation (paper + bypass).
4) Bot aggregates 1-second ticks into candles; on candle close updates SuperTrend + MACD.
5) Bot decides exit/entry; updates global bot_state and persists trade rows.
6) Bot broadcasts updated state via WebSocket; UI updates panels in real-time.
7) Analytics page fetches /api/analytics; backend computes stats from DB.

### Design patterns used
- Thin controller: backend/server.py delegates business logic.
- Service façade: backend/bot_service.py wraps engine + persistence.
- Singleton-ish state: config + bot_state dicts in backend/config.py.
- Push + pull: WebSocket streaming + periodic REST polling fallback.

## 3. Folder & file-level walkthrough

### Root
- README.md — feature overview + run steps.
- docker-compose.yml — two services: backend:8001 and nginx frontend:80.
- init_database.py — creates DB tables.
- backend_test.py — HTTP smoke tests for endpoints.
- tests/ — currently empty besides __init__.py.
- memory/PRD.md — product requirements and implementation checklist.

### backend/
- server.py
  - Defines FastAPI app and routes under /api.
  - Defines WebSocket endpoint /ws.
  - Implements ConnectionManager (active websocket list + broadcast).
  - Startup: init_db + load_config.
- bot_service.py
  - Lazy constructs TradingBot.
  - start_bot/stop_bot/squareoff_position call engine.
  - get_bot_status/get_market_data/get_position/get_config expose state for UI.
  - update_config_values applies updates + persists.
- trading_bot.py
  - TradingBot.run_loop: 1-second loop building candles and applying strategy.
  - process_signal_on_close: primary entry/exit state machine.
  - check_tick_sl/check_trailing_sl_on_close: risk exits.
  - enter_position/close_position: creates/clears positions + orders + DB writes.
- dhan_api.py
  - Wraps dhanhq SDK.
  - Fetches quotes/option chain.
  - Resolves option security id and expiry.
  - Places market orders.
  - Optionally verifies order fills by polling.
- indicators.py
  - SuperTrend(period, multiplier) and MACD(fast, slow, signal).
- database.py
  - SQLite schema init.
  - load_config/save_config.
  - save_trade/update_trade_exit.
  - get_trade_analytics (aggregations).
  - save_candle_data/get_candle_data.
- config.py
  - bot_state (runtime) + config (settings) + DB_PATH.
- utils.py
  - is_market_open/can_take_new_trade/should_force_squareoff (IST time helpers).
- indices.py
  - per-index metadata + strike rounding.
- models.py
  - ConfigUpdate request model.

### frontend/
- nginx.conf
  - Proxies /api and /ws to backend service in Docker.
- src/App.js
  - Global app context state.
  - Fetches initial data via REST.
  - Connects to WebSocket and updates UI state.
  - Routes: / (Dashboard), /settings, /analysis.
- src/pages/Dashboard.jsx
  - Composes panels: TopBar, PositionPanel, ControlsPanel, NiftyTracker, TradesTable, DailySummary, LogsViewer.
- src/pages/Settings.jsx
  - Credentials and risk parameter forms; posts config updates.
- src/pages/TradesAnalysis.jsx
  - Fetches /api/analytics and implements filters + derived statistics.

## 4. Execution flow

### What happens when the app starts
- Backend uvicorn starts FastAPI app.
- Startup hook initializes DB and loads persisted config.
- Bot engine is idle until started via API.

### Entry point
- Backend: uvicorn server:app (port 8001 in Docker).
- Frontend: nginx serves React build; in dev use craco start.

### Runtime flow step-by-step
1) UI loads and calls /api/status, /api/config, /api/trades, etc.
2) UI opens WebSocket to /ws.
3) User clicks Start → /api/bot/start.
4) TradingBot.start() spawns TradingBot.run_loop().
5) run_loop each tick:
   - market gating
   - fetch quotes (spot, option when in a position)
   - update candle aggregates
   - tick-level risk exits
   - candle-close indicator updates
   - reversal exit / new entry decision
   - broadcast state_update

### Background processes / loops
- Backend: trading loop asyncio task; background DB updates via asyncio.create_task.
- Frontend: WebSocket reconnect + 5s REST polling.

## 5. Configuration & environment

### Env variables
- Frontend: REACT_APP_BACKEND_URL (API base, WebSocket base).
- Backend: loads backend/.env if present, but most config is stored in SQLite.

### Config files
- SQLite config table persists config values.
- frontend/nginx.conf provides reverse proxy in Docker.

### Secrets
- Dhan access token + client id are saved via Settings and persisted in SQLite as plaintext.

## 6. External dependencies & integrations

- Broker API: DhanHQ (dhanhq Python SDK).
- Database: SQLite via aiosqlite.
- No queues/message brokers.

## 7. Core business logic

### Decision making logic
- Candle timeframe in seconds (default 5s).
- Signal: SuperTrend direction.
- Optional MACD confirmation.
- Optional HTF SuperTrend alignment (60s).

### Entry rules (summary)
- Must be within market hours + entry cutoff.
- Must respect max trades/day.
- Must respect flip-only and order cooldown.
- If enabled: MACD confirms direction.
- If enabled: HTF filter aligns direction.

### Exit rules (priority)
Tick-level:
1) daily max loss breach
2) max loss per trade
3) target points
4) trailing SL

Candle-level:
- exit immediately on SuperTrend reversal (unless min_hold_seconds blocks it)

Scheduled:
- force squareoff at 15:25 IST.

## 8. Error handling & logging

- Bot loop catches exceptions and continues after sleep.
- Logging to stdout + backend/logs/bot.log.
- UI fetches logs via /api/logs.

## 9. Performance & scalability

- Dhan SDK calls are synchronous and may block the async event loop.
- WS broadcasts are sequential per client.
- Not designed for multiple concurrent bots.

## 10. Security considerations

- No authentication/authorization on API.
- CORS allows *.
- Secrets stored plaintext in SQLite.

## 11. How to run & test locally

Docker:
- docker-compose up -d --build
- Frontend: http://localhost
- Backend: http://localhost:8001/api

Local dev:
- cd backend && python -m uvicorn server:app --reload --port 8001
- cd frontend && yarn start

## 12. Known issues / code smells

- backend/database.py: save_trade() appears to use db without opening a connection.
- Risk sizing qty semantics inconsistent (lots vs absolute qty).
- bypass_market_hours does not bypass TradingBot.is_within_trading_hours.
- Potential for multiple bot instances (global TradingBot plus lazy singleton).
- Settings page hardcodes lot sizes that may not match backend indices.

## 13. Improvement suggestions

- Fix DB trade insert path first (save_trade connection bug).
- Standardize quantity units and position sizing.
- Offload broker calls to threads to avoid blocking event loop.
- Add authentication for control/config endpoints.
- Encrypt or externalize secrets; restrict CORS in production.
- Add pytest tests for entry/exit rules and analytics.

---

# Appendix A — Implemented Fixes (2026-02-07)

This section records the production-impacting fixes implemented after the original walkthrough, based on live/paper runtime observations.

## A1. Live trading: order fill verification (core fix)

Goal: stop “phantom” entries/exits where the bot updates state/DB even though the broker order is still pending/not-found/rejected.

Implemented:
- **Entry (LIVE):** after placing a BUY, the bot now waits for broker confirmation via `verify_order_filled(...)` before opening the position and saving the trade.
- **Exit (LIVE):** exits now place *one* SELL (no duplicate orders) and wait for fill confirmation before clearing position state and updating the trade exit row.
- **Failure behavior:** if fill is not confirmed within the timeout, the bot keeps the position open and logs the broker status instead of force-closing locally.

Files:
- `backend/trading_bot.py`
- `backend/dhan_api.py`

## A2. Prevent duplicate exit orders (squareoff / close_position)

Issue: `squareoff()` used to place a SELL, then call `close_position()` which placed another SELL.

Implemented:
- `squareoff()` now delegates to `close_position()` and does not place its own broker order.
- `close_position()` supports re-entrancy using an `exit_order_id` guard on the position, so repeated exit triggers don’t spam the broker.

Files:
- `backend/trading_bot.py`

## A3. Quantity semantics normalized (lots vs absolute quantity)

Issue: risk sizing path computed “lots” but sent it directly as `qty` (incorrect). This also made P&L and exits inconsistent.

Implemented:
- Risk sizing now computes `lots`, then converts to absolute `qty = lots * lot_size`.
- The bot stores the actual `qty` on the open position and uses it consistently for P&L, exits, and UI reporting.

Files:
- `backend/trading_bot.py`
- `backend/bot_service.py`

## A4. DB persistence bug fixed (trade insert)

Issue: `save_trade()` attempted to use a `db` handle without opening a connection, causing trade rows to not insert reliably.

Implemented:
- `save_trade()` now properly opens an `aiosqlite.connect(...)` context and commits.

Files:
- `backend/database.py`

## A5. Market-hours bypass made consistent

Issue: `bypass_market_hours` bypassed some hour checks (`utils.is_market_open()`), but not the bot’s internal `is_within_trading_hours()` gate.

Implemented:
- `TradingBot.is_within_trading_hours()` now returns `True` when `bypass_market_hours` is enabled.

Files:
- `backend/trading_bot.py`

## A6. Remove dual-bot-instance hazard

Issue: there was a module-level global bot instance in `trading_bot.py` while `bot_service.py` also created its own singleton lazily.

Implemented:
- Removed the global `trading_bot = TradingBot()` instance so the API layer remains the single source of truth.

Files:
- `backend/trading_bot.py`

## A7. Dhan SDK calls moved off the event loop

Issue: Dhan SDK calls are synchronous and can block the asyncio loop (affecting strategy timing and WebSocket responsiveness).

Implemented:
- Wrapped key broker calls with `asyncio.to_thread(...)`:
  - order placement
  - order list polling during fill verification
  - expiry list and option chain calls

Files:
- `backend/dhan_api.py`
- `backend/trading_bot.py` (index/option quote fetching)

## A8. Fill-status compatibility improvements

Issue: broker `orderStatus` strings can vary.

Implemented:
- Fill verification treats `FILLED`, `TRADED`, `COMPLETE`, `COMPLETED` as “filled equivalents”.

Files:
- `backend/dhan_api.py`

## A9. MACD blocking bug fixed

Issue: MACD was being set to `None` on position close, causing perpetual “MACD not ready yet” blocks.

Implemented:
- Do not disable MACD on exit; MACD continues to update across trades.

Files:
- `backend/trading_bot.py`

## A10. Paper mode made fully simulated (no mixed real quotes)

Issue: paper mode could mix simulated index candles with real option-chain/quote data, causing unrealistic premiums and sudden large P&L.

Implemented:
- Paper mode always uses `SIM_...` security IDs and purely simulated option pricing.
- Live mode is the only mode that calls Dhan option chain / option quote resolution.

Files:
- `backend/trading_bot.py`

## A11. WebSocket broadcast stability

Issue: intermittent log noise like: `sent 1011 (internal error) keepalive ping timeout` when a client disconnects or stalls.

Implemented:
- Broadcast now uses a bounded send timeout and drops stale clients to prevent repeated errors.
- Heartbeat send failures break the receive loop and disconnect cleanly.

Files:
- `backend/server.py`

---

# B. Historical + Live Market Data Microservice (Dhan)

This section designs a **production-grade historical + live market data system** for real-money options trading.

## B1. High-Level Architecture Diagram (Text)

```
                 +----------------------------+
                 |        Dhan API            |
                 |  - quotes (poll/stream)    |
                 |  - historical candles      |
                 +-------------+--------------+
                               |
                 (rate-limit, retry, resume)
                               |
                +--------------v--------------------+
                |       Market Data Service         |
                |  FastAPI + workers                |
                |-----------------------------------|
                |  Backfill Job (5y)                |
                |   - windowed/paginated fetch      |
                |   - idempotent upserts            |
                |   - gap detection + repair        |
                |  Streaming Job (24/7)             |
                |   - ticks -> 5s base candles      |
                |   - watermark + lag tracking      |
                +-----------------+-----------------+
                                  |
                                  | SQL (primary) + optional Parquet (cold)
                                  |
                 +----------------v-----------------+
                 |         TimescaleDB (PG)         |
                 |  candles hypertable              |
                 |  ingest_watermarks (resume/lag)  |
                 +----------------+-----------------+
                                  |
                   REST (low-latency reads)
                                  |
           +----------------------v----------------------+
           |                 Trading Bot                  |
           |  - consumes candle windows                    |
           |  - never blocks on warm-up                     |
           |  - places orders only                          |
           +----------------------------------------------+
```

## B2. Why microservice (vs in-process collector)

**Opinionated stance:** for real-money trading, a microservice is safer and easier to operate.

- **Failure isolation:** trading loop can crash/restart without stopping data ingestion.
- **Correctness boundary:** ingestion owns the candle truth; bot becomes a pure consumer.
- **Independent scaling:** backfill and validation are heavy; streaming is latency-sensitive.
- **Maintenance:** storage/ingestion changes don’t risk order-placement code.

## B3. Data ingestion design

### Backfill job (5 years)

Backfill is a distinct worker that:

- Iterates `symbol × timeframe_seconds`.
- Pulls historical candles in fixed **time windows** (pagination-by-time) sized per timeframe.
- Writes using **idempotent upserts** keyed by `(symbol, timeframe_seconds, ts)`.
- Persists progress to `ingest_watermarks(kind='backfill')` so it can resume after restarts.

### Streaming job (continuous append)

Streaming should run 24/7 and:

- Polls (or subscribes to) index LTP at 1s.
- Builds **base 5s candles** deterministically by flooring timestamps to boundaries.
- Upserts each closed candle and updates `ingest_watermarks(kind='stream')`.
- Runs a periodic **gap detector** that checks recent periods and triggers historical fetch to repair missing candles.

**Key guarantee:** “no gaps, no duplicates, no overlaps” comes from boundary alignment + unique keys + upserts.

## B4. Storage recommendations (explicit, production)

Primary (live + recent queries): **PostgreSQL + TimescaleDB**

- Best correctness story (constraints + transactions).
- Great range queries for strategies (symbol/tf/time).
- Compression + retention are mature.

Cold (optional, long-term): **S3 + Parquet**

- Cheapest multi-year storage.
- Best for offline analytics/backtests (Athena/Spark).

Trade-offs summary:

- **AWS Timestream:** great managed TSDB but stricter “exactly-once” constraints are less direct.
- **TimescaleDB:** most control and simplest idempotent ingestion.
- **InfluxDB:** solid TSDB but operationally another system and constraints differ.
- **S3+Parquet:** not for low-latency bot reads; excellent for analytics/cold.

## B5. Schema (example)

- `candles(ts, symbol, timeframe_seconds, open, high, low, close, volume, source, ingested_at)`
  - **Primary key:** `(symbol, timeframe_seconds, ts)`
- `ingest_watermarks(symbol, timeframe_seconds, kind, last_ts, updated_at, details)`

Recommended partitioning/indexing:

- Timescale hypertable on `ts`, plus index `(symbol, timeframe_seconds, ts desc)`.
- Compress 5s candles after 7–30 days; retain 90–180 days hot for 5s.

## B6. Service API design

REST is the default (your stack is Python + React):

- `GET /v1/candles/last?symbol=NIFTY&timeframe_seconds=5&limit=5000`
- `GET /v1/candles/range?symbol=NIFTY&timeframe_seconds=60&start=...&end=...`
- `GET /v1/lag` (watermarks)
- `GET /v1/health`

Caching strategy:

- In-memory cache for “last N” per (symbol, timeframe) within the service.
- Add Redis only if you run multiple replicas.

Latency considerations:

- Strategies should **never** call Dhan directly; they read from the service/DB.

## B7. Operational concerns

- **Holidays / partial days:** do not synthesize candles; watermarks should remain stable.
- **Exchange downtime:** gap detector will detect missing periods and repair after recovery.
- **API outages:** ingestion fails safe; bot can detect lag via `/v1/lag` and fail closed.
- **Clock sync:** enforce NTP and standardize on UTC in storage.
- **Data drift/sanity:** validate monotonic timestamps and candle bounds; quarantine bad batches.

## B8. Deployment model

- Docker Compose for dev.
- ECS/EC2 for production (Kubernetes only if you already run it).
- Timescale on managed Postgres (preferred) or self-managed with backups.

## B9. How the bot integrates

- On strategy init, fetch a **pre-warmed** window (`last N candles`) and seed indicators immediately.
- During runtime, consume new candles (or candle-close events) from the service.
- Bot remains deterministic and does not block on indicator warm-up.

## B10. Repo scaffold

Scaffold added to this repository:

- `market_data_service/` (FastAPI + Timescale schema + basic candle read APIs)
- `docker-compose.yml` includes `timescaledb` and `market-data-service`
