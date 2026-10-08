"""Language guarantees.

A farmer who picks Telugu must not receive romanised text or an untranslated key.
These tests fail loudly if a phrase is missing from any supported language.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.knowledge import localization as L  # noqa: E402


LANGS = list(L.LANGUAGES)


def test_every_phrase_exists_in_every_language():
    missing = [
        (key, lang)
        for key, entry in L.PHRASES.items()
        for lang in LANGS
        if lang not in entry or not entry[lang].strip()
    ]
    assert not missing, f"untranslated phrases: {missing}"


def test_every_disease_named_in_every_language():
    missing = [
        (key, lang)
        for key, entry in L.DISEASE_NAMES.items()
        for lang in LANGS
        if lang not in entry or not entry[lang].strip()
    ]
    assert not missing, f"untranslated disease names: {missing}"


def test_phrases_are_actually_in_the_right_script():
    """Catches a copy-paste that leaves English text under a Telugu key."""
    for key in ("safety", "no_answer", "detected", "healthy_note"):
        for lang in LANGS:
            if lang == "en":
                continue
            text = L.t(key, lang)
            assert L.is_native_script(text, lang), f"{key}/{lang} is not in {L.meta(lang)['script']}"


def test_disease_names_are_in_the_right_script():
    for key in L.DISEASE_NAMES:
        for lang in LANGS:
            if lang == "en":
                continue
            assert L.is_native_script(L.disease_name(key, lang), lang), f"{key}/{lang}"


def test_script_detector_rejects_romanised_text():
    assert L.is_native_script("వరి అగ్గి తెగులు నివారణ", "te")
    assert not L.is_native_script("vari aggi tegulu nivarana", "te")
    # Chemical names and numbers inside a native sentence must still pass
    assert L.is_native_script("వరి అగ్గి తెగులుకు Tricyclazole 75 WP 0.6 g/litre పిచికారీ చేయండి", "te")


def test_unknown_language_falls_back_to_english_not_a_key():
    assert L.t("safety", "zz") == L.PHRASES["safety"]["en"]
    assert L.disease_name("rice_blast", "zz") == "Rice blast"
    assert L.disease_name("not_a_disease", "hi") == "Not A Disease"
