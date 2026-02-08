# Market Data Service

Independent microservice for historical backfill + live streaming candle ingestion.

## Run (Docker)
- `docker compose up -d timescaledb market-data-service`

## Env
- `POSTGRES_DSN=postgresql://market:market@timescaledb:5432/marketdata`
- `DHAN_CLIENT_ID=...`
- `DHAN_ACCESS_TOKEN=...`

Historical (1m bulk):
- `DHAN_BASE_URL=https://<dhan-host>` (service will call `POST /charts/intraday`)
	- OR set `DHAN_HISTORICAL_URL=https://<dhan-host>/charts/intraday`
- If your gateway requires custom headers, set:
	- `DHAN_HISTORICAL_HEADERS_JSON={"access-token":"...","client-id":"..."}`

Timestamps:
- Your `/charts/intraday` response uses `timestamp[]` as **IST epoch**.
- This service **persists IST-epoch as-is** when `DHAN_EPOCH_IS_IST=true` (default).
- If you want real UTC normalization, set `DHAN_EPOCH_IS_IST=false` (applies a -5h30 shift).

Symbol mapping overrides (important):
- By default, this service uses the index `security_id` values from your bot repo.
- If your `/charts/intraday` expects different identifiers (like the example `securityId: "1333"`, `exchangeSegment: "NSE_EQ"`, `instrument: "EQUITY"`), override per symbol:
	- `DHAN_SYMBOL_MAP_JSON={"NIFTY":{"securityId":"13","exchangeSegment":"IDX_I","instrument":"INDEX","expiryCode":0,"oi":false}}`

## Endpoints
- `GET /v1/health`
- `GET /v1/lag`
- `GET /v1/candles/last?symbol=NIFTY&timeframe_seconds=5&limit=500`
- `GET /v1/candles/range?symbol=NIFTY&timeframe_seconds=60&start=...&end=...`

## Notes
- Dhan historical bulk is treated as **1-minute only** in this service.
- 5s/15s/30s are produced going forward via streaming (5s base); optionally derive 15s/30s/1m via continuous aggregates.

## Backfill (5 years)

Run the one-shot job:
- `docker compose run --rm market-data-backfill`

Resume is automatic via `ingest_watermarks(kind='backfill')`.
