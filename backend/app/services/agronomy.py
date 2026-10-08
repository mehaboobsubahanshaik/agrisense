"""Agronomy engine: soil rating, fertiliser plan, crop choice and yield.

All coefficients come from ICAR package-of-practices recommended doses and the
Soil Health Card rating bands, so the numbers a farmer sees are defensible.
Everything is deterministic and explainable - no black box for the decisions
that cost money.
"""
from dataclasses import dataclass

# Soil Health Card rating bands (kg/ha)
N_BANDS = (280, 560)
P_BANDS = (10, 25)
K_BANDS = (120, 280)

ACRE_PER_HA = 2.4711

# Recommended dose of fertiliser, kg/ha of N, P2O5, K2O
RDF: dict[str, tuple[float, float, float]] = {
    "rice": (120, 60, 40),
    "wheat": (120, 60, 40),
    "maize": (150, 75, 60),
    "cotton": (120, 60, 60),
    "sugarcane": (250, 115, 115),
    "groundnut": (25, 50, 75),
    "soybean": (30, 75, 45),
    "chickpea": (20, 60, 20),
    "pigeonpea": (25, 50, 30),
    "greengram": (20, 40, 20),
    "tomato": (150, 100, 100),
    "chilli": (120, 60, 60),
    "onion": (110, 60, 60),
    "turmeric": (120, 60, 100),
    "banana": (200, 100, 300),
}

CROP_PROFILE: dict[str, dict] = {
    "rice":       {"ph": (5.5, 7.5), "rain": (900, 2000), "season": ["kharif"], "water": "high",   "soils": ["clay", "loam", "black"],  "yield_q_acre": 22},
    "maize":      {"ph": (5.5, 7.5), "rain": (500, 900),  "season": ["kharif", "rabi"], "water": "medium", "soils": ["loam", "red", "black"], "yield_q_acre": 25},
    "cotton":     {"ph": (6.0, 8.0), "rain": (500, 900),  "season": ["kharif"], "water": "medium", "soils": ["black", "loam"],          "yield_q_acre": 8},
    "wheat":      {"ph": (6.0, 7.5), "rain": (400, 700),  "season": ["rabi"],   "water": "medium", "soils": ["loam", "clay", "black"],  "yield_q_acre": 18},
    "chickpea":   {"ph": (6.0, 8.0), "rain": (350, 600),  "season": ["rabi"],   "water": "low",    "soils": ["black", "loam"],          "yield_q_acre": 8},
    "groundnut":  {"ph": (6.0, 7.5), "rain": (500, 800),  "season": ["kharif"], "water": "low",    "soils": ["sandy", "red", "loam"],   "yield_q_acre": 10},
    "soybean":    {"ph": (6.0, 7.5), "rain": (600, 1000), "season": ["kharif"], "water": "medium", "soils": ["black", "loam"],          "yield_q_acre": 10},
    "pigeonpea":  {"ph": (6.0, 8.0), "rain": (500, 900),  "season": ["kharif"], "water": "low",    "soils": ["red", "black", "loam"],   "yield_q_acre": 6},
    "greengram":  {"ph": (6.2, 7.5), "rain": (350, 600),  "season": ["kharif", "summer"], "water": "low", "soils": ["loam", "red"],     "yield_q_acre": 4},
    "turmeric":   {"ph": (5.5, 7.5), "rain": (700, 1200), "season": ["kharif"], "water": "high",   "soils": ["loam", "red"],            "yield_q_acre": 90},
    "chilli":     {"ph": (6.0, 7.5), "rain": (600, 1000), "season": ["kharif", "rabi"], "water": "medium", "soils": ["loam", "black", "red"], "yield_q_acre": 10},
    "onion":      {"ph": (6.0, 7.5), "rain": (500, 800),  "season": ["rabi"],   "water": "medium", "soils": ["loam", "red"],            "yield_q_acre": 100},
    "sugarcane":  {"ph": (6.0, 7.5), "rain": (1000, 1800),"season": ["annual"], "water": "high",   "soils": ["loam", "black", "clay"],  "yield_q_acre": 350},
}


# Farmers and forms use local names. Map them onto the crops we actually have
# ICAR doses for, so "paddy" is not silently treated as an unknown crop and
# given a generic 100:50:50 recommendation.
CROP_ALIASES: dict[str, str] = {
    "paddy": "rice", "dhan": "rice", "vari": "rice", "nel": "rice", "batta": "rice",
    "corn": "maize", "makka": "maize", "mokkajonna": "maize", "jowar_maize": "maize",
    "kapas": "cotton", "narma": "cotton", "patti": "cotton", "bt cotton": "cotton",
    "gehun": "wheat", "godhuma": "wheat",
    "bengal gram": "chickpea", "chana": "chickpea", "senagalu": "chickpea", "gram": "chickpea",
    "red gram": "pigeonpea", "tur": "pigeonpea", "arhar": "pigeonpea", "kandulu": "pigeonpea",
    "green gram": "greengram", "moong": "greengram", "mung": "greengram", "pesalu": "greengram",
    "peanut": "groundnut", "mungfali": "groundnut", "verusenaga": "groundnut",
    "soya": "soybean", "soya bean": "soybean",
    "mirchi": "chilli", "mirch": "chilli", "chili": "chilli", "chile": "chilli",
    "pyaz": "onion", "ulli": "onion",
    "haldi": "turmeric", "pasupu": "turmeric",
    "ganna": "sugarcane", "cheruku": "sugarcane",
    "tamatar": "tomato", "tomatoes": "tomato",
    "kela": "banana", "arati": "banana",
}

# Crops we have a published RDF for but no full agronomic profile
GENERIC_RDF = (100.0, 50.0, 50.0)


def normalise_crop(name: str) -> tuple[str, bool]:
    """Return (canonical crop, is_known).

    is_known=False means we fell back to a generic recommendation. Callers must
    surface that to the farmer rather than presenting a guess as a dose.
    """
    key = (name or "").strip().lower().replace("-", " ")
    key = " ".join(key.split())
    key = CROP_ALIASES.get(key, key)
    return key, key in RDF


def _rate(value: float, bands: tuple[float, float]) -> str:
    low, high = bands
    return "low" if value < low else ("medium" if value <= high else "high")


def _adjust(rating: str) -> float:
    """Soil Health Card correction: +25% for low, -25% for high."""
    return {"low": 1.25, "medium": 1.0, "high": 0.75}[rating]


@dataclass
class Fertiliser:
    urea: float
    dap: float
    mop: float


def _to_products(n: float, p: float, k: float) -> Fertiliser:
    """Convert a nutrient dose (kg/acre) into bag quantities.
    DAP = 18% N + 46% P2O5, Urea = 46% N, MOP = 60% K2O.
    Phosphorus is met with DAP first, then the N it contributes is deducted.
    """
    dap = p / 0.46 if p > 0 else 0
    n_from_dap = dap * 0.18
    urea = max(0.0, (n - n_from_dap)) / 0.46
    mop = k / 0.60 if k > 0 else 0
    return Fertiliser(round(urea, 1), round(dap, 1), round(mop, 1))


def analyse_soil(crop: str, n: float, p: float, k: float, ph: float, oc: float,
                 moisture: float, area_acres: float) -> dict:
    crop, crop_known = normalise_crop(crop)
    rdf = RDF.get(crop, GENERIC_RDF)
    ratings = {"n": _rate(n, N_BANDS), "p": _rate(p, P_BANDS), "k": _rate(k, K_BANDS)}

    dose_ha = (
        rdf[0] * _adjust(ratings["n"]),
        rdf[1] * _adjust(ratings["p"]),
        rdf[2] * _adjust(ratings["k"]),
    )
    dose_acre = tuple(round(d / ACRE_PER_HA, 1) for d in dose_ha)
    products = _to_products(*dose_acre)

    # --- health score, 0-100 ---
    score = 0.0
    score += {"low": 8, "medium": 22, "high": 28}[ratings["n"]]
    score += {"low": 8, "medium": 20, "high": 24}[ratings["p"]]
    score += {"low": 8, "medium": 18, "high": 22}[ratings["k"]]
    lo, hi = CROP_PROFILE.get(crop, {}).get("ph", (6.0, 7.5))
    score += 16 if lo <= ph <= hi else (8 if 5.5 <= ph <= 8.2 else 2)
    score += 10 if oc >= 0.75 else (6 if oc >= 0.5 else 2)
    score = round(min(100.0, score), 1)

    corrections: list[str] = []
    if not crop_known:
        corrections.append(
            f"'{crop}' is not in the ICAR dose table, so a general 100:50:50 NPK basis was used. "
            "Confirm the dose for this crop with your agriculture officer before buying fertiliser."
        )
    if ph < 5.5:
        corrections.append("Soil is acidic. Apply 2-4 quintals of agricultural lime per acre 3-4 weeks before sowing.")
    elif ph > 8.2:
        corrections.append("Soil is alkaline/sodic. Apply 2-5 quintals of gypsum per acre and improve drainage.")
    if oc < 0.5:
        corrections.append("Organic carbon is low. Add 5 tonnes of farmyard manure or 2 tonnes of vermicompost per acre.")
    if ratings["n"] == "low":
        corrections.append("Nitrogen is low. Split urea into 3 doses and consider a legume in the next season.")
    if ratings["p"] == "low":
        corrections.append("Phosphorus is low. Apply the full DAP dose as basal, placed below the seed.")
    if ratings["k"] == "low":
        corrections.append("Potassium is low. Split MOP: half basal, half at flowering, to improve grain filling.")
    if moisture < 12:
        corrections.append("Soil moisture is low. Irrigate before sowing and mulch to conserve it.")
    elif moisture > 45:
        corrections.append("Soil is waterlogged. Open drainage channels; roots will suffocate above field capacity.")

    schedule = [
        {"stage": "Basal (at sowing/transplanting)",
         "detail": f"{products.dap} kg DAP + {round(products.mop / 2, 1)} kg MOP + {round(products.urea * 0.3, 1)} kg urea per acre"},
        {"stage": "Vegetative (25-30 days)",
         "detail": f"{round(products.urea * 0.4, 1)} kg urea per acre"},
        {"stage": "Reproductive (flowering / panicle initiation)",
         "detail": f"{round(products.urea * 0.3, 1)} kg urea + {round(products.mop / 2, 1)} kg MOP per acre"},
    ]

    return {
        "crop": crop,
        "crop_known": crop_known,
        "basis": "ICAR recommended dose" if crop_known else "generic 100:50:50 NPK (crop not in dose table)",
        "score": score,
        "grade": "Good" if score >= 75 else ("Fair" if score >= 50 else "Poor"),
        "ratings": ratings,
        "ph_status": "acidic" if ph < 6 else ("alkaline" if ph > 7.5 else "neutral"),
        "oc_status": "low" if oc < 0.5 else ("medium" if oc < 0.75 else "high"),
        "dose_per_acre": {"N": dose_acre[0], "P2O5": dose_acre[1], "K2O": dose_acre[2]},
        "products_per_acre": {"urea_kg": products.urea, "dap_kg": products.dap, "mop_kg": products.mop},
        "total_for_field": {
            "area_acres": area_acres,
            "urea_kg": round(products.urea * area_acres, 1),
            "dap_kg": round(products.dap * area_acres, 1),
            "mop_kg": round(products.mop * area_acres, 1),
            "urea_bags_45kg": round(products.urea * area_acres / 45, 1),
        },
        "schedule": schedule,
        "corrections": corrections,
        "organic_options": [
            "Farmyard manure 5 t/acre incorporated 3 weeks before sowing",
            "Vermicompost 2 t/acre + neem cake 100 kg/acre",
            "Azospirillum/Rhizobium + PSB 5 kg/acre - cuts N and P need by about 25%",
            "Green manure (dhaincha/sunhemp) ploughed in at 45 days adds 20-40 kg N/ha",
            "Jeevamrutham drench every 15 days and panchagavya 3% foliar spray",
        ],
    }


def recommend_crops(n: float, p: float, k: float, ph: float, rainfall_mm: float,
                    season: str, irrigation: str, soil_type: str) -> list[dict]:
    season = season.lower()
    soil_type = soil_type.lower()
    water_available = irrigation.lower() not in ("rainfed", "none")
    results = []

    for crop, prof in CROP_PROFILE.items():
        if season not in prof["season"] and "annual" not in prof["season"]:
            continue
        score, reasons = 0.0, []

        lo, hi = prof["ph"]
        if lo <= ph <= hi:
            score += 30
            reasons.append(f"pH {ph} is in the ideal {lo}-{hi} range")
        elif lo - 0.7 <= ph <= hi + 0.7:
            score += 16
            reasons.append(f"pH {ph} is slightly outside the ideal range")
        else:
            score += 3
            reasons.append(f"pH {ph} is unsuitable without correction")

        rlo, rhi = prof["rain"]
        effective_rain = rainfall_mm + (350 if water_available else 0)
        if rlo <= effective_rain <= rhi * 1.3:
            score += 28
            reasons.append("water availability matches the crop's need")
        elif effective_rain >= rlo * 0.75:
            score += 14
            reasons.append("water is slightly short; plan supplementary irrigation")
        else:
            score += 4
            reasons.append("not enough water for this crop")

        if soil_type in prof["soils"]:
            score += 20
            reasons.append(f"{soil_type} soil suits this crop")
        else:
            score += 7

        need = RDF.get(crop, (100, 50, 50))
        supply = (n / 560, p / 25, k / 280)
        fit = sum(min(1.0, s) for s in supply) / 3
        score += 22 * fit
        if fit < 0.5:
            reasons.append("soil fertility is low: budget for a full fertiliser dose")

        results.append({
            "crop": crop,
            "score": round(min(100.0, score), 1),
            "expected_yield_q_per_acre": prof["yield_q_acre"],
            "water_need": prof["water"],
            "npk_rdf_kg_ha": {"N": need[0], "P2O5": need[1], "K2O": need[2]},
            "reasons": reasons[:3],
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:6]


def predict_yield(crop: str, area_acres: float, soil_score: float, rainfall_mm: float,
                  irrigation: str, disease_pressure: str, fertilizer_applied: bool) -> dict:
    crop, crop_known = normalise_crop(crop)
    prof = CROP_PROFILE.get(crop, {"yield_q_acre": 15, "rain": (500, 1000)})
    base = prof["yield_q_acre"]

    f_soil = 0.55 + 0.60 * (soil_score / 100)                       # 0.55 - 1.15
    rlo, rhi = prof["rain"]
    if rainfall_mm < rlo * 0.6:
        f_water = 0.55
    elif rainfall_mm > rhi * 1.5:
        f_water = 0.80                                              # waterlogging / lodging
    else:
        f_water = 1.0
    if irrigation.lower() in ("drip", "sprinkler"):
        f_water = min(1.15, f_water + 0.15)
    elif irrigation.lower() in ("rainfed", "none"):
        f_water *= 0.85

    f_disease = {"low": 1.0, "medium": 0.88, "high": 0.68}.get(disease_pressure.lower(), 1.0)
    f_fert = 1.0 if fertilizer_applied else 0.72

    per_acre = base * f_soil * f_water * f_disease * f_fert
    total = per_acre * area_acres
    confidence = round(min(0.92, 0.55 + soil_score / 400 + (0.1 if fertilizer_applied else 0)), 2)
    if not crop_known:
        # A generic baseline deserves a generic confidence. Never present a guess
        # about an unlisted crop with the same certainty as a profiled one.
        confidence = min(confidence, 0.45)

    factors = {
        "soil_factor": round(f_soil, 2),
        "water_factor": round(f_water, 2),
        "disease_factor": round(f_disease, 2),
        "fertiliser_factor": round(f_fert, 2),
        "baseline_q_per_acre": base,
    }
    levers = []
    if f_soil < 0.9:
        levers.append(f"Raising the soil score to 85 would add about {round(base * (1.06 - f_soil) * area_acres, 1)} quintals.")
    if not fertilizer_applied:
        levers.append(f"Applying the recommended fertiliser dose would add about {round(total * 0.39, 1)} quintals.")
    if f_disease < 1:
        levers.append("Bringing disease pressure down to low recovers "
                      f"{round(total * (1 / f_disease - 1), 1)} quintals.")
    if f_water < 1:
        levers.append("Drip or sprinkler irrigation would recover part of the water-limited loss.")
    if not crop_known:
        levers.append(
            f"'{crop}' has no district yield profile here, so this uses a generic 15 q/acre baseline. "
            "Treat it as a rough order of magnitude only."
        )

    return {
        "crop": crop,
        "crop_known": crop_known,
        "area_acres": area_acres,
        "per_acre_quintals": round(per_acre, 1),
        "total_quintals": round(total, 1),
        "confidence": confidence,
        "factors": factors,
        "levers": levers,
        "note": "Explainable multiplicative model on ICAR baseline yields. Not a substitute for a field trial.",
    }
