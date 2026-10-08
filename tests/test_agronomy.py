"""Unit tests for the agronomy engine - the numbers a farmer spends money on."""
import pytest

from app.services import agronomy


def test_soil_rating_bands_follow_soil_health_card():
    low = agronomy.analyse_soil("rice", n=200, p=8, k=90, ph=6.5, oc=0.4, moisture=25, area_acres=1)
    high = agronomy.analyse_soil("rice", n=600, p=40, k=400, ph=6.5, oc=0.9, moisture=25, area_acres=1)
    assert low["ratings"] == {"n": "low", "p": "low", "k": "low"}
    assert high["ratings"] == {"n": "high", "p": "high", "k": "high"}
    # low fertility must be corrected upward, high downward
    assert low["dose_per_acre"]["N"] > high["dose_per_acre"]["N"]


def test_dose_matches_icar_rdf_for_medium_soil():
    r = agronomy.analyse_soil("rice", n=400, p=18, k=200, ph=6.8, oc=0.6, moisture=25, area_acres=1)
    # 120 kg N/ha at a medium rating -> 120/2.4711 = 48.6 kg N/acre
    assert r["dose_per_acre"]["N"] == pytest.approx(48.6, abs=0.3)


def test_product_conversion_accounts_for_nitrogen_in_dap():
    r = agronomy.analyse_soil("rice", n=400, p=18, k=200, ph=6.8, oc=0.6, moisture=25, area_acres=1)
    p = r["products_per_acre"]
    n_supplied = p["urea_kg"] * 0.46 + p["dap_kg"] * 0.18
    assert n_supplied == pytest.approx(r["dose_per_acre"]["N"], rel=0.02)
    assert p["dap_kg"] * 0.46 == pytest.approx(r["dose_per_acre"]["P2O5"], rel=0.02)


def test_acidic_soil_triggers_lime_correction():
    r = agronomy.analyse_soil("rice", n=300, p=15, k=150, ph=5.1, oc=0.4, moisture=25, area_acres=1)
    assert any("lime" in c.lower() for c in r["corrections"])


def test_field_total_scales_with_area():
    one = agronomy.analyse_soil("cotton", n=300, p=15, k=150, ph=7, oc=0.6, moisture=20, area_acres=1)
    five = agronomy.analyse_soil("cotton", n=300, p=15, k=150, ph=7, oc=0.6, moisture=20, area_acres=5)
    assert five["total_for_field"]["urea_kg"] == pytest.approx(one["total_for_field"]["urea_kg"] * 5, rel=0.01)


def test_crop_recommendation_respects_season_and_water():
    dry = agronomy.recommend_crops(n=250, p=20, k=200, ph=6.8, rainfall_mm=300,
                                   season="kharif", irrigation="rainfed", soil_type="red")
    crops = [c["crop"] for c in dry]
    assert "rice" not in crops[:2]          # paddy must not top a rainfed 300 mm field
    assert any(c in crops[:3] for c in ("pigeonpea", "groundnut", "greengram"))


def test_rabi_season_excludes_kharif_only_crops():
    rabi = agronomy.recommend_crops(n=300, p=20, k=200, ph=7.0, rainfall_mm=500,
                                    season="rabi", irrigation="canal", soil_type="loam")
    assert "cotton" not in [c["crop"] for c in rabi]


def test_yield_penalties_are_monotonic():
    good = agronomy.predict_yield("rice", 1, 90, 1000, "drip", "low", True)
    bad = agronomy.predict_yield("rice", 1, 40, 300, "rainfed", "high", False)
    assert good["total_quintals"] > bad["total_quintals"]
    assert bad["levers"], "a low-scoring field must be told how to improve"


def test_yield_scales_linearly_with_area():
    one = agronomy.predict_yield("maize", 1, 70, 700, "borewell", "low", True)
    three = agronomy.predict_yield("maize", 3, 70, 700, "borewell", "low", True)
    assert three["total_quintals"] == pytest.approx(one["total_quintals"] * 3, rel=0.01)


# ---------------------------------------------------------------------------
# Accuracy guards: a wrong crop name must never produce a confident dose.
# ---------------------------------------------------------------------------
def test_local_crop_names_map_to_the_right_icar_dose():
    for alias, canonical in [
        ("paddy", "rice"), ("Dhan", "rice"), ("vari", "rice"),
        ("corn", "maize"), ("Mokkajonna", "maize"),
        ("kapas", "cotton"), ("BT Cotton", "cotton"),
        ("tur", "pigeonpea"), ("senagalu", "chickpea"), ("moong", "greengram"),
        ("groundnut", "groundnut"), ("  RICE  ", "rice"),
    ]:
        crop, known = agronomy.normalise_crop(alias)
        assert crop == canonical, f"{alias} -> {crop}, expected {canonical}"
        assert known, f"{alias} should resolve to a known crop"


def test_paddy_and_rice_give_identical_fertiliser_plans():
    a = agronomy.analyse_soil("paddy", 235, 11, 190, 6.4, 0.42, 24, 2.5)
    b = agronomy.analyse_soil("rice", 235, 11, 190, 6.4, 0.42, 24, 2.5)
    assert a["products_per_acre"] == b["products_per_acre"]
    assert a["total_for_field"] == b["total_for_field"]
    assert a["score"] == b["score"]


def test_unknown_crop_is_flagged_not_guessed():
    out = agronomy.analyse_soil("dragonfruit", 235, 11, 190, 6.4, 0.42, 24, 1)
    assert out["crop_known"] is False
    assert "not in the ICAR dose table" in " ".join(out["corrections"])
    assert "generic" in out["basis"]


def test_unknown_crop_yield_confidence_is_capped():
    known = agronomy.predict_yield("rice", 2, 80, 1100, "canal", "low", True)
    unknown = agronomy.predict_yield("dragonfruit", 2, 80, 1100, "canal", "low", True)
    assert unknown["crop_known"] is False
    assert unknown["confidence"] <= 0.45
    assert unknown["confidence"] < known["confidence"]
