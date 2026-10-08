# Architecture notes

## Why these choices

**Everything degrades instead of failing.** The deployment target is a rural district with an
unreliable link and no budget for API credits. So each external dependency has an offline path:
retrieval falls back from ChromaDB to an in-process TF-IDF index, chat falls back from Gemini to
composing an answer from the same retrieved passages, weather falls back from a provider API to
seasonal climatology, detection falls back from YOLO to OpenCV lesion analysis, and SMS falls back
to a log line. The response always carries which path was used — `engine`, `model`, `source` — so
nothing is silently pretended.

**The agronomy is explainable, not learned.** Fertiliser doses, crop ranking and yield come from
published ICAR recommended doses and Soil Health Card rating bands, implemented as plain code. A
farmer spending money on urea deserves a number that can be traced to a source and audited by an
extension officer — a black box cannot be argued with in a field.

**The LLM is a translator, not an oracle.** Retrieval runs first; the system prompt allows answers
only from retrieved passages and requires the model to admit when the corpus does not cover the
question. This is what keeps a confident-sounding hallucination from becoming a pesticide purchase.

**Auth is phone-first because that is what farmers have.** No email, no password to lose. The design
constraint is SMS cost, which drives the 30-second cooldown, the daily cap, and two independent rate
limiters.

## Request path

1. nginx terminates the connection, applies rate limits and security headers, routes `/api/*` to the
   backend, `/ai/*` to the inference service, everything else to the SPA.
2. FastAPI's middleware applies a per-IP Redis fixed-window limit — tighter on `/auth`.
3. `deps.current_user` decodes the JWT, confirms the session row is not revoked, loads the user.
4. The route delegates to a service; services are pure enough to unit test without a database.
5. Prometheus metrics are recorded for every request; structured JSON logs go to stdout.

## Data model

17 tables: `users`, `otp_requests` (audit only — live codes are in Redis), `sessions`, `farms`,
`crop_images`, `disease_reports`, `weather_cache`, `government_schemes`, `chat_history`,
`notifications`, `soil_reports`, `yield_predictions`, `activity_logs`, `feedback`, `iot_devices`,
`settings`, `languages`.

Schema is created on boot (`Base.metadata.create_all`) and reference data is seeded idempotently, so
a first run needs no migration step. Alembic config is included for versioned migrations once the
schema stabilises.

## Offline behaviour in the browser

The service worker caches the app shell (cache-first) and API GET responses (network-first with a
cached fallback). A farmer who opened the dashboard on the village Wi-Fi keeps the forecast, the
advisories and the last disease report on the way to the field. Writes are not queued — a scan
submitted with no signal fails with a clear message rather than silently disappearing.

## Scaling notes

* `backend` and `ai-service` are stateless — scale with `docker compose up --scale backend=3` behind
  the existing nginx upstream.
* Uploads live on a shared volume; move to S3-compatible storage for multi-host deployment.
* The heavy path is YOLO inference. Export to ONNX, or move detection into Celery and return a job id
  if concurrent scan volume grows.
* Redis holds OTPs, rate-limit counters and the weather cache. It is deliberately non-critical: if
  Redis is down the limiter fails open and the API keeps serving.
