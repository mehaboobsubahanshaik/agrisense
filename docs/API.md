# API reference

Base URL `http://localhost:8080/api/v1`. Interactive docs at `/docs`, schema at `/openapi.json`.
All routes except the auth pair and `/config` need `Authorization: Bearer <access_token>`.

## Auth

| Method | Path | Body | Notes |
|---|---|---|---|
| POST | `/auth/request-otp` | `{phone}` | 6-digit code, 5-min TTL, 30-s cooldown. Returns `dev_otp` when `DEV_MODE=true` |
| POST | `/auth/verify-otp` | `{phone, otp, device?}` | Creates the user on first login. Returns access + refresh + user |
| POST | `/auth/refresh` | `{refresh_token}` | Rotates the refresh token |
| GET / PATCH | `/auth/me` | `{name?, language?, state?, district?, lat?, lon?}` | Profile |
| GET | `/auth/sessions` | — | Every device that has signed in |
| POST | `/auth/logout` · `/auth/logout-all` | — | Revoke this session, or all |

```bash
# full login in two calls
OTP=$(curl -s -X POST localhost:8080/api/v1/auth/request-otp \
      -H 'content-type: application/json' -d '{"phone":"9876543210"}' | jq -r .dev_otp)

TOKEN=$(curl -s -X POST localhost:8080/api/v1/auth/verify-otp \
        -H 'content-type: application/json' \
        -d "{\"phone\":\"9876543210\",\"otp\":\"$OTP\"}" | jq -r .access_token)
```

## Advisory

| Method | Path | Body / query |
|---|---|---|
| POST | `/chat` | `{message, language}` → `{reply, sources[], engine, language, cached}` |
| POST | `/chat/attach` | multipart `file` + `message` + `language`. Photo → detection + remedy in `language`, then a grounded answer. PDF/TXT/CSV → parsed as context. Max 12 MB |
| GET / DELETE | `/chat/history` | last 50 turns |
| POST | `/disease/analyze` | multipart `file`, `crop_hint` → detection + remedy card |
| GET | `/disease/reports` | scan history |
| GET | `/weather` | `?lat&lon` → current, 7-day, decision advisories |
| POST | `/soil/analyze` | `{crop,n,p,k,ph,oc,moisture,area_acres}` → score, dose, bags, schedule |
| POST | `/crop/recommend` | `{n,p,k,ph,rainfall_mm,season,irrigation,soil_type}` → ranked shortlist |
| POST | `/yield/predict` | `{crop,area_acres,soil_score,rainfall_mm,irrigation,disease_pressure,fertilizer_applied}` |
| GET | `/schemes` | `?state&category&q` |
| GET | `/dashboard/summary` | every widget in one call |
| POST | `/voice/transcribe` | multipart `file`, `language` (Whisper) |

```bash
# ask about a leaf photo, answered in Telugu
curl -X POST localhost:8080/api/v1/chat/attach \
  -H "Authorization: Bearer $TOKEN" \
  -F file=@leaf.jpg -F language=te -F message="ఏమి పిచికారీ చేయాలి?"

curl -X POST localhost:8080/api/v1/disease/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -F file=@leaf.jpg -F crop_hint=rice

curl -X POST localhost:8080/api/v1/soil/analyze \
  -H "Authorization: Bearer $TOKEN" -H 'content-type: application/json' \
  -d '{"crop":"rice","n":235,"p":11,"k":190,"ph":6.4,"oc":0.42,"moisture":24,"area_acres":2.5}'
```

## Other

| Method | Path | Purpose |
|---|---|---|
| GET / POST | `/notifications` · `/notifications/read-all` | Alerts |
| GET / PATCH | `/farms` · `/farms/{id}` | Farm profile |
| POST | `/iot/reading` | Sensor ingest — authenticates on `device_key`, no user token |
| GET | `/iot/devices` | Registered sensors |
| GET | `/languages` · `/config` | Reference data |
| POST | `/feedback` | Rating + message |
| GET | `/admin/stats` | Admin role only |
| GET | `/health` · `/metrics` | Liveness and Prometheus |

## Errors

Standard HTTP codes with a human-readable `detail` written for a farmer, not a developer:
`400` bad code, `401` session ended, `403` wrong role, `413` photo too large, `415` wrong file type,
`429` rate limited or resend too soon, `503` a dependency is down.
