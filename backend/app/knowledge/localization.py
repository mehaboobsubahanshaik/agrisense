"""Native-script localisation for chat answers.

Two jobs:

1. Tell the LLM exactly which language AND which script to write in, then verify
   the reply actually came back in that script (models drift into romanised
   output surprisingly often - "vari agginu tegulu" instead of Telugu script).

2. Give the offline fallback a real native-script skeleton. We do not machine
   translate the reference passages without a model - inventing a Telugu
   pesticide dose would be worse than showing the English one - so the structure,
   the disease name, the severity and the safety line are localised, and the
   detailed English text is clearly labelled underneath.
"""
from __future__ import annotations

import re

# code -> (English name, native name, script name, unicode range for verification)
LANGUAGES: dict[str, dict[str, str]] = {
    "en": {"name": "English", "native": "English", "script": "Latin", "range": ""},
    "hi": {"name": "Hindi", "native": "हिन्दी", "script": "Devanagari", "range": "\u0900-\u097f"},
    "te": {"name": "Telugu", "native": "తెలుగు", "script": "Telugu", "range": "\u0c00-\u0c7f"},
    "ta": {"name": "Tamil", "native": "தமிழ்", "script": "Tamil", "range": "\u0b80-\u0bff"},
    "kn": {"name": "Kannada", "native": "ಕನ್ನಡ", "script": "Kannada", "range": "\u0c80-\u0cff"},
    "mr": {"name": "Marathi", "native": "मराठी", "script": "Devanagari", "range": "\u0900-\u097f"},
    "bn": {"name": "Bengali", "native": "বাংলা", "script": "Bengali", "range": "\u0980-\u09ff"},
    "pa": {"name": "Punjabi", "native": "ਪੰਜਾਬੀ", "script": "Gurmukhi", "range": "\u0a00-\u0a7f"},
}

DEFAULT = "en"


def meta(lang: str) -> dict[str, str]:
    return LANGUAGES.get(lang, LANGUAGES[DEFAULT])


def is_native_script(text: str, lang: str) -> bool:
    """True when the text really is in the script we asked for.

    Requires 20% of letters to be in range, which tolerates embedded product
    names and numbers ("Tricyclazole 75 WP") without accepting a fully
    romanised answer.
    """
    rng = meta(lang)["range"]
    if not rng:
        return True
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    native = len(re.findall(f"[{rng}]", text))
    return native / len(letters) >= 0.20


# --------------------------------------------------------------------------
# Phrase pack. Short, high-confidence agricultural strings only.
# --------------------------------------------------------------------------
PHRASES: dict[str, dict[str, str]] = {
    "ref_intro": {
        "en": "Here is what the practice notes say:",
        "hi": "अभ्यास नोट्स के अनुसार:",
        "te": "సాగు మార్గదర్శకాల ప్రకారం:",
        "ta": "பயிர் வழிகாட்டி குறிப்புகளின்படி:",
        "kn": "ಬೇಸಾಯ ಮಾರ್ಗಸೂಚಿಗಳ ಪ್ರಕಾರ:",
        "mr": "शेती मार्गदर्शक नोंदींनुसार:",
        "bn": "চাষের নির্দেশিকা অনুযায়ী:",
        "pa": "ਖੇਤੀ ਹਦਾਇਤਾਂ ਅਨੁਸਾਰ:",
    },
    "no_answer": {
        "en": "I could not find this in my agricultural reference set. Describe the crop, its age and what you see on the leaf, or contact your nearest Krishi Vigyan Kendra.",
        "hi": "यह जानकारी मेरे कृषि संदर्भ में नहीं मिली। फसल, उसकी उम्र और पत्ती पर क्या दिख रहा है बताइए, या नजदीकी कृषि विज्ञान केंद्र से संपर्क करें।",
        "te": "ఈ సమాచారం నా వ్యవసాయ సమాచార నిధిలో దొరకలేదు. పంట, దాని వయసు, ఆకుపై ఏమి కనిపిస్తుందో చెప్పండి, లేదా దగ్గరలోని కృషి విజ్ఞాన కేంద్రాన్ని సంప్రదించండి.",
        "ta": "இந்தத் தகவல் என் விவசாயக் குறிப்புகளில் இல்லை. பயிர், அதன் வயது, இலையில் என்ன தெரிகிறது என்பதைச் சொல்லுங்கள், அல்லது அருகிலுள்ள கிருஷி விஞ்ஞான் கேந்திராவைத் தொடர்பு கொள்ளுங்கள்.",
        "kn": "ಈ ಮಾಹಿತಿ ನನ್ನ ಕೃಷಿ ಆಕರಗಳಲ್ಲಿ ಸಿಗಲಿಲ್ಲ. ಬೆಳೆ, ಅದರ ವಯಸ್ಸು ಮತ್ತು ಎಲೆಯಲ್ಲಿ ಏನು ಕಾಣುತ್ತಿದೆ ಎಂದು ತಿಳಿಸಿ, ಅಥವಾ ಹತ್ತಿರದ ಕೃಷಿ ವಿಜ್ಞಾನ ಕೇಂದ್ರವನ್ನು ಸಂಪರ್ಕಿಸಿ.",
        "mr": "ही माहिती माझ्या कृषी संदर्भात सापडली नाही. पीक, त्याचे वय आणि पानावर काय दिसते ते सांगा, किंवा जवळच्या कृषी विज्ञान केंद्राशी संपर्क साधा.",
        "bn": "এই তথ্য আমার কৃষি সহায়িকায় পাইনি। ফসল, তার বয়স এবং পাতায় কী দেখছেন জানান, অথবা নিকটবর্তী কৃষি বিজ্ঞান কেন্দ্রে যোগাযোগ করুন।",
        "pa": "ਇਹ ਜਾਣਕਾਰੀ ਮੇਰੇ ਖੇਤੀ ਹਵਾਲਿਆਂ ਵਿੱਚ ਨਹੀਂ ਮਿਲੀ। ਫ਼ਸਲ, ਉਸ ਦੀ ਉਮਰ ਅਤੇ ਪੱਤੇ ਉੱਤੇ ਕੀ ਦਿੱਸ ਰਿਹਾ ਹੈ ਦੱਸੋ, ਜਾਂ ਨੇੜਲੇ ਕ੍ਰਿਸ਼ੀ ਵਿਗਿਆਨ ਕੇਂਦਰ ਨਾਲ ਸੰਪਰਕ ਕਰੋ।",
    },
    "safety": {
        "en": "Wear gloves and a mask for any chemical spray, and follow the pre-harvest interval printed on the label.",
        "hi": "किसी भी रासायनिक छिड़काव के लिए दस्ताने और मास्क पहनें, और लेबल पर दिया गया कटाई-पूर्व अंतराल पालन करें।",
        "te": "ఏ రసాయన పిచికారీకైనా చేతి తొడుగులు, మాస్క్ ధరించండి; లేబుల్‌పై ఉన్న కోత-ముందు విరామాన్ని పాటించండి.",
        "ta": "எந்த ரசாயனத் தெளிப்புக்கும் கையுறை மற்றும் முகக்கவசம் அணியுங்கள்; லேபிளில் உள்ள அறுவடைக்கு முந்தைய இடைவெளியைப் பின்பற்றுங்கள்.",
        "kn": "ಯಾವುದೇ ರಾಸಾಯನಿಕ ಸಿಂಪಡಣೆಗೆ ಕೈಗವಸು ಮತ್ತು ಮಾಸ್ಕ್ ಧರಿಸಿ; ಲೇಬಲ್‌ನಲ್ಲಿರುವ ಕೊಯ್ಲು-ಪೂರ್ವ ಅಂತರವನ್ನು ಪಾಲಿಸಿ.",
        "mr": "कोणत्याही रासायनिक फवारणीसाठी हातमोजे व मास्क वापरा; लेबलवरील काढणीपूर्व अंतर पाळा.",
        "bn": "যেকোনো রাসায়নিক স্প্রের সময় গ্লাভস ও মাস্ক পরুন; লেবেলে দেওয়া ফসল কাটার আগের বিরতি মেনে চলুন।",
        "pa": "ਕਿਸੇ ਵੀ ਰਸਾਇਣਕ ਛਿੜਕਾਅ ਲਈ ਦਸਤਾਨੇ ਅਤੇ ਮਾਸਕ ਪਾਓ; ਲੇਬਲ ਉੱਤੇ ਦਿੱਤਾ ਵਾਢੀ ਤੋਂ ਪਹਿਲਾਂ ਦਾ ਵਕਫ਼ਾ ਮੰਨੋ।",
    },
    "detected": {
        "en": "In your photo I can see",
        "hi": "आपकी फोटो में दिख रहा है",
        "te": "మీ ఫోటోలో కనిపిస్తున్నది",
        "ta": "உங்கள் புகைப்படத்தில் தெரிவது",
        "kn": "ನಿಮ್ಮ ಫೋಟೋದಲ್ಲಿ ಕಾಣುತ್ತಿರುವುದು",
        "mr": "तुमच्या फोटोत दिसते",
        "bn": "আপনার ছবিতে দেখা যাচ্ছে",
        "pa": "ਤੁਹਾਡੀ ਫੋਟੋ ਵਿੱਚ ਦਿੱਸ ਰਿਹਾ ਹੈ",
    },
    "confidence": {
        "en": "Confidence", "hi": "विश्वास", "te": "నమ్మకం", "ta": "நம்பகத்தன்மை",
        "kn": "ವಿಶ್ವಾಸ", "mr": "विश्वास", "bn": "নির্ভরতা", "pa": "ਭਰੋਸਾ",
    },
    "affected_area": {
        "en": "Affected leaf area", "hi": "प्रभावित पत्ती क्षेत्र", "te": "ప్రభావిత ఆకు విస్తీర్ణం",
        "ta": "பாதிக்கப்பட்ட இலைப் பரப்பு", "kn": "ಬಾಧಿತ ಎಲೆ ಪ್ರದೇಶ", "mr": "बाधित पान क्षेत्र",
        "bn": "আক্রান্ত পাতার অংশ", "pa": "ਪ੍ਰਭਾਵਿਤ ਪੱਤਾ ਖੇਤਰ",
    },
    "severity": {
        "en": "Severity", "hi": "गंभीरता", "te": "తీవ్రత", "ta": "தீவிரம்",
        "kn": "ತೀವ್ರತೆ", "mr": "तीव्रता", "bn": "তীব্রতা", "pa": "ਗੰਭੀਰਤਾ",
    },
    "low": {"en": "low", "hi": "कम", "te": "తక్కువ", "ta": "குறைவு", "kn": "ಕಡಿಮೆ", "mr": "कमी", "bn": "কম", "pa": "ਘੱਟ"},
    "medium": {"en": "medium", "hi": "मध्यम", "te": "మధ్యస్థం", "ta": "நடுத்தரம்", "kn": "ಮಧ್ಯಮ", "mr": "मध्यम", "bn": "মাঝারি", "pa": "ਦਰਮਿਆਨਾ"},
    "high": {"en": "high", "hi": "अधिक", "te": "అధికం", "ta": "அதிகம்", "kn": "ಹೆಚ್ಚು", "mr": "जास्त", "bn": "বেশি", "pa": "ਵੱਧ"},
    "chemical": {
        "en": "Chemical control", "hi": "रासायनिक उपचार", "te": "రసాయన నివారణ",
        "ta": "ரசாயனக் கட்டுப்பாடு", "kn": "ರಾಸಾಯನಿಕ ನಿಯಂತ್ರಣ", "mr": "रासायनिक नियंत्रण",
        "bn": "রাসায়নিক নিয়ন্ত্রণ", "pa": "ਰਸਾਇਣਕ ਇਲਾਜ",
    },
    "organic": {
        "en": "Organic option", "hi": "जैविक विकल्प", "te": "సేంద్రియ ప్రత్యామ్నాయం",
        "ta": "இயற்கை வழி", "kn": "ಸಾವಯವ ಪರ್ಯಾಯ", "mr": "सेंद्रिय पर्याय",
        "bn": "জৈব বিকল্প", "pa": "ਜੈਵਿਕ ਬਦਲ",
    },
    "cultural": {
        "en": "Field practice", "hi": "खेत की पद्धति", "te": "పొలంలో చేయవలసినవి",
        "ta": "வயல் நடைமுறை", "kn": "ಹೊಲದ ಪದ್ಧತಿ", "mr": "शेतातील उपाय",
        "bn": "মাঠের অনুশীলন", "pa": "ਖੇਤ ਦੇ ਅਮਲ",
    },
    "sources": {
        "en": "Sources", "hi": "स्रोत", "te": "మూలాలు", "ta": "ஆதாரங்கள்",
        "kn": "ಆಕರಗಳು", "mr": "स्रोत", "bn": "উৎস", "pa": "ਸਰੋਤ",
    },
    "from_file": {
        "en": "From your attached file", "hi": "आपकी संलग्न फाइल से", "te": "మీరు జతచేసిన ఫైల్ నుండి",
        "ta": "நீங்கள் இணைத்த கோப்பிலிருந்து", "kn": "ನೀವು ಲಗತ್ತಿಸಿದ ಕಡತದಿಂದ",
        "mr": "तुम्ही जोडलेल्या फाइलमधून", "bn": "আপনার সংযুক্ত ফাইল থেকে", "pa": "ਤੁਹਾਡੀ ਨੱਥੀ ਫਾਈਲ ਤੋਂ",
    },
    "healthy_note": {
        "en": "The leaf looks healthy. Keep checking once a week.",
        "hi": "पत्ती स्वस्थ दिख रही है। हर हफ्ते जांच करते रहें।",
        "te": "ఆకు ఆరోగ్యంగా ఉంది. ప్రతి వారం పరిశీలిస్తూ ఉండండి.",
        "ta": "இலை ஆரோக்கியமாக உள்ளது. வாரந்தோறும் கண்காணியுங்கள்.",
        "kn": "ಎಲೆ ಆರೋಗ್ಯವಾಗಿದೆ. ವಾರಕ್ಕೊಮ್ಮೆ ಪರಿಶೀಲಿಸುತ್ತಿರಿ.",
        "mr": "पान निरोगी दिसते. दर आठवड्याला तपासत राहा.",
        "bn": "পাতা সুস্থ দেখাচ্ছে। প্রতি সপ্তাহে পরীক্ষা করুন।",
        "pa": "ਪੱਤਾ ਤੰਦਰੁਸਤ ਲੱਗਦਾ ਹੈ। ਹਰ ਹਫ਼ਤੇ ਜਾਂਚ ਕਰਦੇ ਰਹੋ।",
    },
    "offline_note": {
        "en": "Offline mode - answered from the local reference set.",
        "hi": "ऑफ़लाइन मोड: विस्तृत संदर्भ अंग्रेज़ी में है। पूरे हिन्दी उत्तर के लिए Gemini API key जोड़ें।",
        "te": "ఆఫ్‌లైన్ మోడ్: వివరమైన సూచన ఇంగ్లీషులో ఉంది. పూర్తి తెలుగు సమాధానానికి Gemini API key జోడించండి.",
        "ta": "ஆஃப்லைன் முறை: விரிவான குறிப்பு ஆங்கிலத்தில் உள்ளது. முழு தமிழ் பதிலுக்கு Gemini API key சேர்க்கவும்.",
        "kn": "ಆಫ್‌ಲೈನ್ ಮೋಡ್: ವಿವರವಾದ ಆಕರ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿದೆ. ಪೂರ್ಣ ಕನ್ನಡ ಉತ್ತರಕ್ಕೆ Gemini API key ಸೇರಿಸಿ.",
        "mr": "ऑफलाइन मोड: तपशीलवार संदर्भ इंग्रजीत आहे. संपूर्ण मराठी उत्तरासाठी Gemini API key जोडा.",
        "bn": "অফলাইন মোড: বিস্তারিত তথ্য ইংরেজিতে আছে। সম্পূর্ণ বাংলা উত্তরের জন্য Gemini API key যোগ করুন।",
        "pa": "ਆਫ਼ਲਾਈਨ ਮੋਡ: ਵਿਸਥਾਰਤ ਹਵਾਲਾ ਅੰਗਰੇਜ਼ੀ ਵਿੱਚ ਹੈ। ਪੂਰੇ ਪੰਜਾਬੀ ਜਵਾਬ ਲਈ Gemini API key ਜੋੜੋ।",
    },
    "english_detail": {
        "en": "Detail",
        "hi": "विवरण (अंग्रेज़ी)", "te": "వివరాలు (ఇంగ్లీష్)", "ta": "விவரம் (ஆங்கிலம்)",
        "kn": "ವಿವರ (ಇಂಗ್ಲಿಷ್)", "mr": "तपशील (इंग्रजी)", "bn": "বিস্তারিত (ইংরেজি)", "pa": "ਵੇਰਵਾ (ਅੰਗਰੇਜ਼ੀ)",
    },
}

# Disease names in every supported script - used by both the chat answer and the
# scan report, so a Telugu user never sees "bacterial_leaf_blight".
DISEASE_NAMES: dict[str, dict[str, str]] = {
    "rice_blast": {
        "en": "Rice blast", "hi": "धान का ब्लास्ट", "te": "వరి అగ్గి తెగులు", "ta": "நெல் குலைநோய்",
        "kn": "ಭತ್ತದ ಬೆಂಕಿ ರೋಗ", "mr": "भाताचा करपा", "bn": "ধানের ব্লাস্ট", "pa": "ਝੋਨੇ ਦਾ ਬਲਾਸਟ",
    },
    "bacterial_leaf_blight": {
        "en": "Bacterial leaf blight", "hi": "जीवाणु पत्ती झुलसा", "te": "బాక్టీరియా ఆకు ఎండు తెగులు",
        "ta": "பாக்டீரியா இலை கருகல்", "kn": "ಬ್ಯಾಕ್ಟೀರಿಯಾ ಎಲೆ ಒಣಗು ರೋಗ", "mr": "जिवाणू करपा",
        "bn": "ব্যাকটেরিয়াজনিত পাতা ঝলসা", "pa": "ਬੈਕਟੀਰੀਆ ਪੱਤਾ ਝੁਲਸ",
    },
    "leaf_spot": {
        "en": "Leaf spot", "hi": "पत्ती धब्बा रोग", "te": "ఆకు మచ్చ తెగులు", "ta": "இலைப் புள்ளி நோய்",
        "kn": "ಎಲೆ ಚುಕ್ಕೆ ರೋಗ", "mr": "पानावरील ठिपके", "bn": "পাতার দাগ রোগ", "pa": "ਪੱਤਾ ਧੱਬਾ ਰੋਗ",
    },
    "leaf_rust": {
        "en": "Leaf rust", "hi": "पत्ती रतुआ", "te": "ఆకు తుప్పు తెగులు", "ta": "இலைத் துரு நோய்",
        "kn": "ಎಲೆ ತುಕ್ಕು ರೋಗ", "mr": "पानावरील तांबेरा", "bn": "পাতার মরিচা রোগ", "pa": "ਪੱਤਾ ਕੁੰਗੀ",
    },
    "powdery_mildew": {
        "en": "Powdery mildew", "hi": "चूर्णिल आसिता", "te": "బూడిద తెగులు", "ta": "வெண் பூஞ்சை நோய்",
        "kn": "ಬೂದಿ ರೋಗ", "mr": "भुरी रोग", "bn": "গুঁড়া ছত্রাক রোগ", "pa": "ਚਿੱਟਾ ਧੂੜਾ ਰੋਗ",
    },
    "late_blight": {
        "en": "Late blight", "hi": "पछेती झुलसा", "te": "ఆలస్య ఎండు తెగులు", "ta": "பிந்தைய கருகல் நோய்",
        "kn": "ತಡ ಅಂಗಮಾರಿ ರೋಗ", "mr": "उशिरा येणारा करपा", "bn": "নাবী ধ্বসা", "pa": "ਪਿਛੇਤੀ ਝੁਲਸ",
    },
    "early_blight": {
        "en": "Early blight", "hi": "अगेती झुलसा", "te": "ముందస్తు ఎండు తెగులు", "ta": "முந்தைய கருகல் நோய்",
        "kn": "ಮುಂಚಿನ ಅಂಗಮಾರಿ ರೋಗ", "mr": "लवकर येणारा करपा", "bn": "আগাম ধ্বসা", "pa": "ਅਗੇਤੀ ਝੁਲਸ",
    },
    "pest_damage": {
        "en": "Pest damage", "hi": "कीट क्षति", "te": "పురుగు నష్టం", "ta": "பூச்சி சேதம்",
        "kn": "ಕೀಟ ಹಾನಿ", "mr": "किडीचे नुकसान", "bn": "পোকার ক্ষতি", "pa": "ਕੀੜੇ ਦਾ ਨੁਕਸਾਨ",
    },
    "nutrient_deficiency": {
        "en": "Nutrient deficiency", "hi": "पोषक तत्व की कमी", "te": "పోషక లోపం", "ta": "ஊட்டச்சத்து குறைபாடு",
        "kn": "ಪೋಷಕಾಂಶ ಕೊರತೆ", "mr": "अन्नद्रव्यांची कमतरता", "bn": "পুষ্টির ঘাটতি", "pa": "ਪੌਸ਼ਟਿਕ ਤੱਤ ਦੀ ਘਾਟ",
    },
    "healthy": {
        "en": "Healthy", "hi": "स्वस्थ", "te": "ఆరోగ్యకరం", "ta": "ஆரோக்கியம்",
        "kn": "ಆರೋಗ್ಯಕರ", "mr": "निरोगी", "bn": "সুস্থ", "pa": "ਤੰਦਰੁਸਤ",
    },
}


def t(key: str, lang: str) -> str:
    """Phrase lookup that always returns something usable."""
    entry = PHRASES.get(key, {})
    return entry.get(lang) or entry.get(DEFAULT) or key


def disease_name(key: str, lang: str) -> str:
    entry = DISEASE_NAMES.get(key, {})
    return entry.get(lang) or entry.get(DEFAULT) or key.replace("_", " ").title()
