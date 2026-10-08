import logging
import os

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from app.detector import MODEL_PATH, analyse

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ai-service")

app = FastAPI(title="AgriSense Vision & Voice Service", version="1.0.0")

_whisper = None


def whisper():
    global _whisper
    if _whisper is None:
        from faster_whisper import WhisperModel

        _whisper = WhisperModel(os.getenv("WHISPER_MODEL", "tiny"), device="cpu", compute_type="int8")
    return _whisper


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "weights_present": os.path.exists(MODEL_PATH),
        "weights_path": MODEL_PATH,
    }


@app.post("/detect")
async def detect(file: UploadFile = File(...), crop_hint: str = Form(default="")):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    result = analyse(data)
    result["crop_hint"] = crop_hint
    return result


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...), language: str = Form(default="en")):
    data = await file.read()
    tmp = f"/tmp/{file.filename or 'audio.webm'}"
    with open(tmp, "wb") as fh:
        fh.write(data)
    try:
        segments, info = whisper().transcribe(tmp, language=None if language == "auto" else language)
        text = " ".join(s.text.strip() for s in segments).strip()
        return {"text": text, "language": info.language, "duration": info.duration}
    except Exception as exc:
        log.error("transcription failed: %s", exc)
        raise HTTPException(status_code=503, detail="Transcription failed.")
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
