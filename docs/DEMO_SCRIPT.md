# Five-minute demo script

**Before you start:** `./scripts/start.sh`, then keep `docker compose logs -f backend` in a second
terminal. Have one photo of a diseased leaf and one healthy leaf on the demo machine.

**0:00 — The problem.** A farmer sees spots on paddy. The choice is a two-hour trip to the KVK, a
shopkeeper who profits from selling more chemical, or a guess. Show the landing page.

**0:30 — Sign in.** Type any 10-digit number. The code appears on screen (dev mode) and in the log.
Say the number out loud: no password, 6 digits, 5 minutes, 5 attempts. That is the whole barrier.

**1:00 — Dashboard.** Point at the weather card, then the advisory strip below it. The line that
lands is *"hold the urea, 25 mm of rain will wash it away"* — that is money saved today.

**1:45 — Scan a leaf.** Upload the diseased photo. Show the annotated image, severity, and the three
remedy columns. Say plainly which model produced it: the fallback, or your trained weights if
`models/crop_disease_yolo11.pt` is mounted. Judges reward the honesty, not the bigger number.

**2:45 — Ask in Telugu.** Switch the language selector, tap the mic, ask about the same disease.
Show the source chips under the answer and press "read aloud" — that is the whole accessibility
story in ten seconds.

**3:30 — Soil to bags.** Enter a Soil Health Card: N 235, P 11, K 190, pH 6.4, OC 0.42, 2.5 acres.
The output that matters is the third card: *kilograms of urea, DAP and MOP to buy*, and how many
45 kg bags. Then the split-application schedule.

**4:15 — Offline.** Open dev tools, tick "offline", reload. The shell and the last dashboard are
still there. That is the difference between a demo and a deployment.

**4:45 — Under the hood.** One screen: `docker compose ps` showing ten healthy containers, then
Grafana. Close on `/docs` — 29 documented endpoints.

**Answers to the three questions you will be asked**

*"Is the disease model actually trained?"* — Whatever is true. The fallback is labelled in every API
response; swapping in trained weights is one file copy and a restart (`docs/MODEL_TRAINING.md`).

*"What stops the LLM hallucinating a pesticide dose?"* — Retrieval runs first and the prompt permits
answers only from retrieved passages; sources are shown with every reply; with no API key the answer
is composed from the passages directly, so there is no free-running generation path.

*"Does it work without internet?"* — The PWA shell and last data, yes. Weather falls back to
climatology, chat to local retrieval, detection to on-device analysis. Only fresh forecasts and
Gemini need the network.
