# AgriSense AI

**An AI advisor for smallholder farms in India.** Photograph a sick leaf, ask a question by voice or text,
or type in a soil health card — and get back the dose, the timing and the reason, in Telugu, Hindi or English.

Built for the *AI-Powered Agricultural Advisor for Farmers* brief: LLM chat with RAG, YOLO image
detection, weather-driven advisories, soil and fertiliser planning, government schemes, multilingual
voice, and offline-capable PWA delivery — all behind one `docker compose up --build`.

---

## Run it (one command)

```bash
git clone <your-repo-url> agrisense-ai && cd agrisense-ai
cp .env.example .env          # optional — sensible defaults are baked in
docker compose up --build
```

Then open:

| What | Where |
|---|---|
| App | http://localhost:8080 |
| API docs (OpenAPI) | http://localhost:8080/docs |
| Health check | http://localhost:8080/health |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 (`admin` / `admin`) |

Or use the helper, which waits until the stack is actually ready:

```bash
./scripts/start.sh
```

### Signing in

There is no password. Enter **any 10-digit number** → you get a 6-digit code.
With `DEV_MODE=true` (the default) the code is shown on screen and printed in the log:

```bash
docker compose logs -f backend | grep OTP
```

Set `SMS_PROVIDER=msg91` (recommended for India) or `twilio` plus the matching keys to send real SMS.

### It runs with zero API keys

Every external dependency has a working fallback, so a demo never dies on a dead Wi-Fi or an
expired key:

| Service | With key | Without key |
|---|---|---|
| Chat | Gemini 2.5 Flash, grounded on retrieved passages | Local RAG composes the answer from the same passages |
| Weather | WeatherAPI / OpenWeather | **Open-Meteo (no key needed)**, then seasonal climatology offline |
| Disease detection | Custom-trained YOLOv11 weights | OpenCV lesion analysis, clearly labelled as a fallback |
| OTP SMS | MSG91 / Twilio | Printed to the backend log |
| Retrieval | ChromaDB vector store | In-process TF-IDF index over the same corpus |

Add keys any time in `.env` and restart — nothing else changes.

---

## What it does

**1. Crop and disease detection.** Upload or snap a leaf. The YOLO service returns the disease, how
much of the leaf is affected, and a severity band. The backend attaches a remedy card: chemical dose
per litre, organic alternative, and the field practice that stops it recurring — plus a spray-safety line.

**2. Chat, grounded, multilingual, and it takes attachments.** Questions are answered from a curated
corpus of ICAR package-of-practices, KVK bulletins and state advisories. Retrieval runs first; the
LLM is instructed to answer only from what was retrieved and to say so when the corpus does not
cover the question. Every answer shows its sources and can be read aloud.

Three things make the chat usable for a farmer rather than a developer:

* **Answers come back in the farmer's own script** — Telugu in Telugu letters, not romanised. The
  prompt names both the language and the script, and the reply is verified against that script's
  Unicode block. Models drift into romanised output; when that happens we force one rewrite.
* **Attach a photo or a file.** A leaf photo goes through the same YOLO detector as the Crop scan
  page and comes back as a disease name, severity and remedy card in the farmer's language — then
  the LLM answers the follow-up question with that detection as evidence. A soil health card PDF,
  TXT or CSV is parsed and read as context. Photos sent through chat also appear in scan history.
* **Repeat questions are instant.** Answers are cached in Redis for six hours, passages are trimmed
  before they reach the prompt, and the retrieval index is warmed at boot.

| Language | Chat answers | Interface |
|---|---|---|
| English, हिन्दी, తెలుగు, தமிழ், ಕನ್ನಡ, मराठी, বাংলা, ਪੰਜਾਬੀ | native script | native script |

With no Gemini key the offline path still answers in native script: headings, disease name,
severity, the remedy sections and the safety line are all localised, with the English reference
detail labelled underneath. We do not machine translate a pesticide dose without a model — a
hallucinated Telugu dose is worse than a correct English one.

**3. Weather that tells you what to do.** Not just millimetres — *"25 mm in 48 hours: hold the urea,
it will leach"*, *"dry and calm Thursday: that is your spray window"*, frost and heat-stress warnings,
sowing windows, and fungal-risk alerts from humidity and temperature.

**4. Soil and fertiliser.** Enter the six numbers from a Soil Health Card. You get a 0–100 score, the
Soil Health Card rating for N, P and K, the ICAR recommended dose corrected ±25% by that rating,
converted into **kilograms of urea, DAP and MOP for your acreage** and split across three growth
stages — plus pH/organic-carbon corrections and an organic route.

**5. Crop choice and yield.** Crops are ranked against your pH, water availability, soil type and
season with the reason for each position. The yield model is deliberately explainable: a baseline
yield multiplied by soil, water, disease and fertiliser factors, each shown, plus the levers that
would raise it.

**6. Schemes and live market prices.** PM-KISAN, PMFBY, KCC, Soil Health Card, PMKSY, PM-KUSUM,
eNAM, AIF and state schemes — benefit, eligibility, documents to carry, where to apply.

**Today's mandi prices are genuinely live**, pulled from the data.gov.in feed published daily by the
Directorate of Marketing and Inspection. Ask "what is the rate for cotton" in chat and the answer is
built from today's reported modal prices, including which nearby market paid the most. Every price
response states its own `as_of` date and whether it came from the live feed or a cached snapshot; if
the feed is down we say so rather than showing a stale number as current.

**Scheme text is not live, and the app says so.** There is no public API serving the full text of
Indian agricultural schemes — myscheme.gov.in has no open endpoint and data.gov.in publishes
datasets, not a maintained catalogue. Scraping portals that change layout without notice would mean
silently showing farmers wrong eligibility rules, which is the worst failure this feature could have.
So: a curated catalogue written from the official portals, a nightly job that verifies every official
link is still reachable, a freshness chip on each card ("Official link verified today", or a warning
when the page stops responding), and a direct link out for the final word. `last_verified` is an
honest claim about the link, not a claim that a human re-read the eligibility text.

**7. Accessibility.** Eight languages in the interface, Web Speech API for voice in and out (no upload,
so it works on 2G), Whisper on the server when audio quality matters, and a service worker that keeps
the shell and your last dashboard usable with no signal.

---

## Architecture

```
                     ┌──────────── nginx :8080 ────────────┐
                     │  TLS-ready · gzip · rate limits     │
                     │  security headers · reverse proxy   │
                     └───┬──────────────┬──────────────┬───┘
                         │              │              │
                  /  (SPA)        /api/*          /ai/*
                         │              │              │
                ┌────────▼──────┐ ┌─────▼──────────┐ ┌─▼─────────────────┐
                │  frontend     │ │  backend       │ │  ai-service       │
                │  React 19     │ │  FastAPI 3.12  │ │  YOLOv11 + OpenCV │
                │  Vite · TS    │ │  async SQLA 2  │ │  faster-whisper   │
                │  Tailwind PWA │ │  JWT · OTP     │ └───────────────────┘
                └───────────────┘ └──┬───┬───┬─────┘
                                     │   │   │
                        ┌────────────┘   │   └───────────┐
                   ┌────▼─────┐   ┌──────▼─────┐   ┌─────▼──────┐
                   │ Postgres │   │   Redis    │   │  ChromaDB  │
                   │ 17 tables│   │ OTP · rate │   │  RAG store │
                   └──────────┘   │ limit·cache│   └────────────┘
                                  └──────┬─────┘
                                    ┌────▼────┐   ┌────────────┐   ┌─────────┐
                                    │ Celery  │   │ Prometheus │──▶│ Grafana │
                                    │ + beat  │   └────────────┘   └─────────┘
                                    └─────────┘
```

**Repository layout**

```
agrisense-ai/
├── backend/app/
│   ├── api/routes/      auth · chat · disease · weather · advisory · schemes · dashboard · voice · misc
│   ├── core/            config · security (JWT/HMAC) · logging · redis
│   ├── db/              async engine + 17 SQLAlchemy models
│   ├── knowledge/       curated agri corpus + disease remedy library
│   ├── services/        otp · sms · llm · rag · weather · agronomy · vision
│   ├── main.py          app, rate limiter, health, metrics
│   └── worker.py        Celery beat: daily weather advisories
├── ai-service/app/      YOLO inference, OpenCV fallback, Whisper
├── frontend/src/        pages · components · lib (api, i18n) · store
├── nginx/ monitoring/ scripts/ tests/ docs/ database/ models/
└── docker-compose.yml
```

---

## Authentication

Passwordless, phone + OTP, exactly to spec:

```
phone → 6-digit OTP → SMS → verify (5 min window, 5 attempts) → JWT + refresh → dashboard
```

* Codes are **never stored in clear** — Redis holds an HMAC-SHA256 with a 300-second TTL.
* Resend is blocked for 30 seconds and capped per day.
* Five wrong attempts destroys the code.
* Refresh tokens are **rotated on every use** and stored hashed against a session row.
* Every device is a session: list them and revoke one or all from Settings.
* Two layers of rate limiting: nginx (`1 r/s` on auth, `20 r/s` elsewhere) and a Redis
  fixed-window limiter in the app (12/min on auth).

Other security: strict CORS, SQL injection prevented by the ORM's parameter binding, XSS mitigated by
React escaping plus `X-Content-Type-Options`/`X-Frame-Options`/`Referrer-Policy`/`Permissions-Policy`
at the edge, upload MIME and size validation, Pydantic validation on every request body, secrets via
`.env` only, and an HTTPS server block ready to uncomment once certificates are in `nginx/certs/`.

---

## Using the real YOLO model

The stack ships with the OpenCV fallback so it runs anywhere. To use trained weights:

```bash
cp your_trained_model.pt models/crop_disease_yolo11.pt
docker compose restart ai-service
curl http://localhost:8080/ai/health     # weights_present: true
```

Training instructions, dataset sources (PlantVillage, PlantDoc, Rice Leaf Diseases) and the class map
are in [`docs/MODEL_TRAINING.md`](docs/MODEL_TRAINING.md).

---

## Development without Docker

```bash
# backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+asyncpg://agri:agri@localhost:5432/agrisense
uvicorn app.main:app --reload

# frontend (proxies /api to :8000)
cd frontend && npm install && npm run dev      # http://localhost:5173

# ai-service
cd ai-service && pip install -r requirements.txt && uvicorn app.main:app --port 9000
```

Postgres and Redis alone: `docker compose up -d postgres redis`.

---

## Tests

```bash
pip install pytest pytest-asyncio httpx
pytest tests -q
```

21 unit tests cover the parts where a wrong number costs a farmer money — Soil Health Card rating
bands, ICAR dose conversion (including the nitrogen that DAP contributes), area scaling, crop
ranking by season and water, yield monotonicity, weather decision rules, retrieval accuracy, and JWT
and OTP hashing. The integration test walks the whole OTP login flow, including resend cooldown,
wrong-code rejection and single-use enforcement; it skips itself when Postgres and Redis are not up.

CI (`.github/workflows/ci.yml`) runs lint, tests against real Postgres and Redis service containers,
a frontend production build, a Docker build, and a Trivy vulnerability scan.

---

## Operations

```bash
docker compose ps                     # health of every container
docker compose logs -f backend
./scripts/backup.sh                   # pg_dump + uploads tarball, 14-day retention
./scripts/restore.sh backups/db-*.sql.gz
docker compose down -v                # reset everything, including volumes
```

`/health` reports the API, database and Redis separately and returns 503 when the database is gone,
so a load balancer can act on it. Prometheus scrapes request rate, latency histograms and error rate;
the Grafana dashboard is provisioned automatically.

**Before going to production:** set `DEV_MODE=false`, replace `SECRET_KEY` with a long random
string, set `CORS_ORIGINS` to your domain, configure a real SMS provider, put certificates in
`nginx/certs/` and uncomment the HTTPS block, and change the Grafana password.

---

## Datasets and preprocessing

Two pipelines under `datasets/`, both of which report on their own output rather than silently
producing something plausible.

**`prepare_disease_dataset.py`** turns raw downloads into a clean YOLO training set: maps the
inconsistent folder names the public datasets ship with onto our ten classes, drops truncated files
and thumbnails, removes exact duplicates by content hash, and splits **stratified by class and by
source**. That second part matters — splitting by class alone lets every lab photo land in
validation and every field photo in training, which produces a validation score that means nothing.
The run writes `dataset_report.json` and warns you out loud when under 20% of training images are
field photos, when classes are imbalanced beyond 10:1, or when a class has no training data at all.

**`prepare_chat_corpus.py`** preprocesses the advisory corpus and then measures whether retrieval
actually works. Documents are split into sentence-aware passages with overlap (never mid-sentence —
that separates a dose from its units), units and spellings are normalised, and near-duplicates are
dropped. Then 24 golden questions written in farmer vocabulary are scored:

```
Retrieval quality
  questions   24
  hit@1       0.833
  hit@3       1.0
  mrr         0.91
```

Any question that misses is named, with what came back instead, so you fix the corpus rather than
guess. A CI test fails the build if hit@3 drops below 0.95.

## Accuracy guards

The engine refuses to be confidently wrong. Three specific protections:

* **Local crop names are normalised.** "paddy", "dhan", "vari", "kapas", "tur", "mokkajonna" and
  thirty-odd others resolve to the crop that actually has an ICAR dose behind it, so a farmer typing
  the name they use does not silently get a generic 100:50:50 recommendation.
* **An unrecognised crop is flagged, not guessed.** The soil result carries `crop_known: false` and
  says in plain language that a generic basis was used; the yield estimate caps its confidence at
  0.45 and says so. A guess is never dressed up as a dose.
* **Enums are enums.** Season, irrigation type, soil type and disease pressure are validated
  `Literal` values. A typo used to fall through to a default and produce a confident recommendation
  for the wrong season; now it returns a 422.

31 unit tests cover this, including that `paddy` and `rice` produce byte-identical fertiliser plans.

## Honest limitations

* The bundled disease detector is a **colour-signature heuristic**, not a trained network. It is
  labelled as such in every response. Accuracy claims require your own trained weights and the
  evaluation in `docs/MODEL_TRAINING.md`.
* Agronomic figures are Indian national recommendations. Local KVK advice overrides them.
* The yield model is a transparent multiplicative estimate, not a calibrated regression on your
  district's history.
* This is decision support. Confirm chemical doses with an agriculture officer before spraying.
#   a g r i s e n s e  
 