from app.services import weather


def _forecast(rain, tmax=30, tmin=20, humidity=60, wind=8):
    return {
        "daily": [
            {"date": f"2026-07-0{i+1}", "tmax": tmax, "tmin": tmin, "rain_mm": rain,
             "rain_chance": 60, "humidity": humidity, "wind_kph": wind}
            for i in range(7)
        ]
    }


def test_heavy_rain_stops_irrigation_and_spraying():
    kinds = {a["kind"]: a for a in weather.build_advisory(_forecast(rain=25))}
    assert "irrigation" in kinds and "Skip" in kinds["irrigation"]["title"]
    assert kinds["spray"]["level"] == "high"


def test_dry_hot_week_recommends_irrigation():
    kinds = {a["kind"]: a for a in weather.build_advisory(_forecast(rain=0, tmax=36))}
    assert kinds["irrigation"]["title"] == "Irrigate soon"


def test_humid_warm_weather_raises_disease_risk():
    advisory = weather.build_advisory(_forecast(rain=0.2, tmax=28, humidity=88))
    assert any(a["kind"] == "disease" for a in advisory)


def test_frost_warning_is_issued():
    advisory = weather.build_advisory(_forecast(rain=0, tmax=14, tmin=2))
    assert any(a["kind"] == "frost" and a["level"] == "high" for a in advisory)


def test_synthetic_fallback_is_deterministic():
    a = weather._synthetic(17.4, 78.5)
    b = weather._synthetic(17.4, 78.5)
    assert a == b and len(a["daily"]) == 7
