# Upgrading an existing AgriSense checkout to v1

If you already ran the stack, you do **not** need to delete anything. Copy the changed
files in, rebuild two images, and the database migrates itself on boot.

Your project lives at something like `D:\Projects\Agri_chatbot\agrisense-ai\agrisense-ai`.
Below, that is `$proj`. The extracted `agrisense` folder is `$new`.

---

## The whole thing, in five commands (PowerShell)

```powershell
# 1. point these at your two folders
$proj = "D:\Projects\Agri_chatbot\agrisense-ai\agrisense-ai"
$new  = "D:\Downloads\agrisense_v1"

# 2. keep a copy of what you have, in case you edited something
Copy-Item $proj "$proj-backup-$(Get-Date -f yyyyMMdd-HHmm)" -Recurse

# 3. copy the new code over the old (your .env, uploads and models are untouched)
Copy-Item "$new\backend"   $proj -Recurse -Force
Copy-Item "$new\frontend"  $proj -Recurse -Force
Copy-Item "$new\nginx"     $proj -Recurse -Force
Copy-Item "$new\tests"     $proj -Recurse -Force
Copy-Item "$new\docs"      $proj -Recurse -Force
Copy-Item "$new\README.md","$new\.env.example" $proj -Force

# 4. if you have no .env yet, take the ready-made one
if (-not (Test-Path "$proj\.env")) { Copy-Item "$new\.env" $proj }

# 5. rebuild only what changed, and restart
cd $proj
docker compose up -d --build backend worker frontend
docker compose up -d nginx
```

Then open http://localhost:8080 and hard-refresh once (**Ctrl+Shift+R**) so the browser
drops the old service-worker cache and picks up the new chat page.

---

## Check it worked

```powershell
docker compose ps                       # every service Up; nginx no longer restarting
curl http://localhost:8080/health
docker compose logs backend | Select-String "migration|ready"
```

In the app: open **Ask AI**, switch the language selector to తెలుగు, and send a question.
The reply should come back in Telugu script. Then tap the paperclip, attach a leaf photo,
and you should get a disease name, severity and remedy card — in the same language.

---

## What actually changed

**New files**

| File | Why |
|---|---|
| `backend/app/knowledge/localization.py` | Phrase pack, disease names and script verification for 8 languages |
| `backend/app/db/migrate.py` | Idempotent `ALTER TABLE ... IF NOT EXISTS` so old databases survive |
| `tests/test_localization.py` | Fails the build if any phrase is missing or in the wrong script |
| `frontend/src/vite-env.d.ts` | Vite env typings |
| `.env` | Ready-to-run config with a generated `SECRET_KEY` |

**Modified**

| File | Change |
|---|---|
| `nginx/nginx.conf` | **Removed the duplicate `proxy_read_timeout`** that crash-looped nginx |
| `backend/app/services/llm.py` | Native-script enforcement with one forced rewrite, Redis answer cache, trimmed prompts, attachment context |
| `backend/app/api/routes/chat.py` | New `POST /chat/attach` for photos and documents |
| `backend/app/services/vision.py` | Advisory now carries `affected_area_pct` |
| `backend/app/db/models.py` | `chat_history.attachment` and `chat_history.engine` |
| `backend/app/schemas.py` | `ChatOut` carries `language`, `cached`, `attachment` |
| `backend/app/main.py` | Runs migrations and warms the retrieval index at boot |
| `backend/requirements.txt` | `pypdf` for soil-health-card PDFs |
| `frontend/src/lib/i18n.ts` | All 8 languages, chat strings, localised starter questions |
| `frontend/src/pages/Chat.tsx` | Attachment button, preview, image rendering, localised UI |
| `frontend/package.json`, `frontend/Dockerfile` | Build script fix, lockfile-aware `npm ci` |

---

## Notes

**Your data survives.** Postgres, Redis, uploads and Grafana all live in named Docker
volumes, and the new columns are added with `IF NOT EXISTS`. Only `docker compose down -v`
would wipe them.

**If the chat page still looks old**, it is the service worker. Hard-refresh, or open
DevTools → Application → Service Workers → Unregister, then reload.

**If you want a clean slate instead**, skip all of the above: delete the old folder, use
`agrisense_v1` as-is, and run `docker compose up --build`.
