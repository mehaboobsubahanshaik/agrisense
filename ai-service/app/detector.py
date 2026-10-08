"""Crop disease detection.

Two paths, one contract:

1. `models/crop_disease_yolo11.pt` present  -> real YOLOv11 inference (custom
   trained on PlantVillage + PlantDoc, see docs/MODEL_TRAINING.md).
2. No weights                              -> a deterministic lesion-analysis
   fallback built on OpenCV colour segmentation. It is clearly labelled as such
   in the response so nobody mistakes it for the trained model.

Both return the same shape, so the backend, the UI and the demo never break.
"""
from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

import cv2
import numpy as np

log = logging.getLogger(__name__)

MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "/models/crop_disease_yolo11.pt")
CONF = float(os.getenv("YOLO_CONF", "0.35"))

# class names of the custom trained model, mapped to the backend remedy library
CLASS_ALIAS = {
    "blast": "rice_blast",
    "rice_blast": "rice_blast",
    "bacterial_leaf_blight": "bacterial_leaf_blight",
    "blb": "bacterial_leaf_blight",
    "brown_spot": "leaf_spot",
    "leaf_spot": "leaf_spot",
    "cercospora": "leaf_spot",
    "rust": "leaf_rust",
    "leaf_rust": "leaf_rust",
    "powdery_mildew": "powdery_mildew",
    "late_blight": "late_blight",
    "early_blight": "early_blight",
    "armyworm": "pest_damage",
    "bollworm": "pest_damage",
    "aphid": "pest_damage",
    "pest": "pest_damage",
    "nutrient_deficiency": "nutrient_deficiency",
    "healthy": "healthy",
}

_model = None


def _load():
    global _model
    if _model is not None:
        return _model
    if not Path(MODEL_PATH).exists():
        return None
    try:
        from ultralytics import YOLO

        _model = YOLO(MODEL_PATH)
        log.info("loaded YOLO weights from %s", MODEL_PATH)
        return _model
    except Exception as exc:
        log.error("could not load YOLO weights: %s", exc)
        return None


def _severity(fraction: float) -> str:
    if fraction >= 0.25:
        return "high"
    if fraction >= 0.08:
        return "medium"
    return "low"


def _encode(img: np.ndarray) -> str:
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode() if ok else ""


def _heuristic(bgr: np.ndarray) -> dict:
    """Colour-signature leaf analysis. Deterministic, explainable, offline."""
    img = cv2.resize(bgr, (640, 640), interpolation=cv2.INTER_AREA)
    blur = cv2.GaussianBlur(img, (5, 5), 0)
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    total = img.shape[0] * img.shape[1]

    plant = cv2.inRange(hsv, (20, 30, 25), (95, 255, 255))          # green + yellow-green plant tissue
    plant_area = max(int(plant.sum() / 255), 1)

    masks = {
        "healthy_green": cv2.inRange(hsv, (35, 60, 40), (85, 255, 255)),
        "chlorosis": cv2.inRange(hsv, (22, 70, 120), (34, 255, 255)),   # yellowing
        "necrosis": cv2.inRange(hsv, (5, 40, 20), (20, 255, 160)),      # brown / dead tissue
        "rust": cv2.inRange(hsv, (8, 120, 130), (18, 255, 255)),        # orange pustules
        "powdery": cv2.inRange(hsv, (0, 0, 195), (180, 45, 255)),       # white bloom
        "dark_lesion": cv2.inRange(hsv, (0, 0, 0), (180, 255, 60)),     # water-soaked / greasy
    }
    frac = {k: float(m.sum() / 255) / plant_area for k, m in masks.items()}

    # holes and chewed margins: plant mask contour irregularity
    contours, _ = cv2.findContours(plant, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    solidity = 1.0
    if contours:
        c = max(contours, key=cv2.contourArea)
        hull = cv2.convexHull(c)
        area, hull_area = cv2.contourArea(c), cv2.contourArea(hull)
        if hull_area > 0:
            solidity = area / hull_area

    lesion_frac = min(0.95, frac["necrosis"] + frac["dark_lesion"] * 0.5 + frac["rust"])
    scores = {
        "healthy": 0.55 + frac["healthy_green"] * 0.4 - lesion_frac * 1.6 - frac["chlorosis"] * 0.8,
        "leaf_rust": frac["rust"] * 3.2,
        "powdery_mildew": frac["powdery"] * 3.0,
        "late_blight": frac["dark_lesion"] * 2.2 + frac["necrosis"] * 0.8,
        "leaf_spot": frac["necrosis"] * 2.6,
        "early_blight": frac["necrosis"] * 1.9 + frac["chlorosis"] * 0.9,
        "nutrient_deficiency": frac["chlorosis"] * 2.8 - lesion_frac,
        "pest_damage": max(0.0, (1.0 - solidity) * 2.4),
    }
    ranked = sorted(((k, max(0.0, v)) for k, v in scores.items()), key=lambda x: x[1], reverse=True)
    top_sum = sum(v for _, v in ranked[:4]) or 1.0

    predictions = [
        {
            "class": name,
            "confidence": round(min(0.94, score / top_sum), 3),
            "severity": _severity(lesion_frac if name != "healthy" else 0.0),
            "affected_area_pct": round(lesion_frac * 100, 1),
        }
        for name, score in ranked[:3]
        if score > 0
    ]
    if not predictions:
        predictions = [{"class": "healthy", "confidence": 0.5, "severity": "low", "affected_area_pct": 0.0}]

    overlay = img.copy()
    lesion_mask = cv2.bitwise_or(masks["necrosis"], masks["dark_lesion"])
    lesion_mask = cv2.morphologyEx(lesion_mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    cnts, _ = cv2.findContours(lesion_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in cnts:
        if cv2.contourArea(c) > 220:
            x, y, w, hgt = cv2.boundingRect(c)
            cv2.rectangle(overlay, (x, y), (x + w, y + hgt), (0, 0, 220), 2)

    return {
        "ok": True,
        "model": "opencv-lesion-analysis (fallback - no trained weights mounted)",
        "predictions": predictions,
        "metrics": {k: round(v, 4) for k, v in frac.items()} | {"leaf_solidity": round(solidity, 3)},
        "annotated_image": _encode(overlay),
    }


def _yolo(bgr: np.ndarray, model) -> dict:
    res = model.predict(source=bgr, conf=CONF, verbose=False)[0]
    names = res.names
    preds = []
    area_total = bgr.shape[0] * bgr.shape[1]
    covered = 0.0
    for box in res.boxes:
        cls = names[int(box.cls)]
        x1, y1, x2, y2 = [float(t) for t in box.xyxy[0]]
        covered += (x2 - x1) * (y2 - y1)
        preds.append(
            {
                "class": CLASS_ALIAS.get(cls.lower(), cls.lower()),
                "raw_class": cls,
                "confidence": round(float(box.conf), 3),
                "box": [round(x1), round(y1), round(x2), round(y2)],
            }
        )
    preds.sort(key=lambda p: p["confidence"], reverse=True)
    frac = min(1.0, covered / area_total)
    for p in preds:
        p["severity"] = _severity(frac)
        p["affected_area_pct"] = round(frac * 100, 1)
    return {
        "ok": True,
        "model": f"yolov11-custom ({Path(MODEL_PATH).name})",
        "predictions": preds or [{"class": "healthy", "confidence": 0.6, "severity": "low", "affected_area_pct": 0.0}],
        "annotated_image": _encode(res.plot()),
    }


def analyse(image_bytes: bytes) -> dict:
    arr = np.frombuffer(image_bytes, np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        return {"ok": False, "model": "none", "predictions": [], "error": "That file is not a readable image."}

    model = _load()
    if model is not None:
        try:
            return _yolo(bgr, model)
        except Exception as exc:
            log.error("yolo inference failed, falling back: %s", exc)
    return _heuristic(bgr)
