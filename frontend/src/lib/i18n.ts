import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Dict = Record<string, string>

/** Every string a farmer sees lives here in their own script. Keys missing from a
 *  language fall back to English rather than showing a raw key. */
const en = {
  appName: 'AgriSense AI',
  tagline: 'Answers for your field, in your language',
  dashboard: 'Dashboard', chat: 'Ask AI', disease: 'Crop scan', soil: 'Soil & fertiliser',
  weather: 'Weather', schemes: 'Schemes', yieldp: 'Yield', crops: 'Crop choice',
  notifications: 'Alerts', settings: 'Settings', signOut: 'Sign out',
  phone: 'Mobile number', sendCode: 'Send code', enterCode: 'Enter the 6-digit code',
  verify: 'Verify and continue', resend: 'Resend code', farmScore: 'Farm score',
  cropHealth: 'Crop health', water: 'Water need', todayWeather: "Today's weather",
  // chat
  chatTitle: 'Ask AgriSense',
  chatSubtitle: 'Grounded in ICAR practice notes. Answers include doses and timing.',
  chatPlaceholder: 'Describe what you see in the field…',
  chatStartersIntro: 'Start with one of these, or ask in your own words:',
  send: 'Send', clear: 'Clear', readAloud: 'Read aloud', speakNow: 'Speak',
  attach: 'Attach photo or file',
  attachHint: 'Attach a leaf photo or a soil health card (JPG, PNG, PDF, CSV)',
  remove: 'Remove', thinking: 'Checking the practice notes…',
  loadingChat: 'Loading your conversation…', analysingPhoto: 'Looking at your photo…',
  attachedPhoto: 'Attached photo', attachedFile: 'Attached file',
  offlineAnswer: 'Answered offline',
  voiceUnsupported: 'Voice input is not supported in this browser. Type the question instead.',
  s1: 'My paddy leaves have grey spots with brown edges. What should I spray?',
  s2: 'How much urea per acre for 2 acres of cotton in black soil?',
  s3: 'When should I irrigate maize this week?',
  s4: 'Which crop should I sow after rice this rabi?',
}

const hi: Dict = {
  appName: 'एग्रीसेंस एआई',
  tagline: 'आपके खेत के जवाब, आपकी भाषा में',
  dashboard: 'डैशबोर्ड', chat: 'एआई से पूछें', disease: 'फसल जांच', soil: 'मिट्टी और खाद',
  weather: 'मौसम', schemes: 'योजनाएं', yieldp: 'उपज', crops: 'फसल चयन',
  notifications: 'सूचनाएं', settings: 'सेटिंग्स', signOut: 'साइन आउट',
  phone: 'मोबाइल नंबर', sendCode: 'कोड भेजें', enterCode: '6 अंकों का कोड डालें',
  verify: 'सत्यापित करें', resend: 'कोड फिर भेजें', farmScore: 'खेत स्कोर',
  cropHealth: 'फसल स्वास्थ्य', water: 'पानी की जरूरत', todayWeather: 'आज का मौसम',
  chatTitle: 'एग्रीसेंस से पूछें',
  chatSubtitle: 'आईसीएआर पद्धति नोट्स पर आधारित। जवाब में मात्रा और समय भी मिलेगा।',
  chatPlaceholder: 'खेत में जो दिख रहा है वह बताइए…',
  chatStartersIntro: 'इनमें से कोई चुनें, या अपने शब्दों में पूछें:',
  send: 'भेजें', clear: 'साफ करें', readAloud: 'पढ़कर सुनाएं', speakNow: 'बोलिए',
  attach: 'फोटो या फाइल जोड़ें',
  attachHint: 'पत्ती की फोटो या मृदा स्वास्थ्य कार्ड जोड़ें (JPG, PNG, PDF, CSV)',
  remove: 'हटाएं', thinking: 'पद्धति नोट्स देख रहे हैं…',
  loadingChat: 'आपकी बातचीत लोड हो रही है…', analysingPhoto: 'आपकी फोटो देखी जा रही है…',
  attachedPhoto: 'जोड़ी गई फोटो', attachedFile: 'जोड़ी गई फाइल',
  offlineAnswer: 'ऑफ़लाइन जवाब',
  voiceUnsupported: 'इस ब्राउज़र में आवाज़ समर्थित नहीं है। सवाल टाइप करें।',
  s1: 'मेरे धान के पत्तों पर भूरे किनारों वाले धूसर धब्बे हैं। क्या छिड़कूं?',
  s2: 'काली मिट्टी में 2 एकड़ कपास के लिए प्रति एकड़ कितनी यूरिया?',
  s3: 'इस हफ्ते मक्के में सिंचाई कब करूं?',
  s4: 'इस रबी में धान के बाद कौन सी फसल बोऊं?',
}

const te: Dict = {
  appName: 'అగ్రిసెన్స్ AI',
  tagline: 'మీ పొలానికి సమాధానాలు, మీ భాషలో',
  dashboard: 'డాష్‌బోర్డ్', chat: 'AI ని అడగండి', disease: 'పంట స్కాన్', soil: 'నేల & ఎరువులు',
  weather: 'వాతావరణం', schemes: 'పథకాలు', yieldp: 'దిగుబడి', crops: 'పంట ఎంపిక',
  notifications: 'హెచ్చరికలు', settings: 'సెట్టింగ్‌లు', signOut: 'సైన్ అవుట్',
  phone: 'మొబైల్ నంబర్', sendCode: 'కోడ్ పంపండి', enterCode: '6 అంకెల కోడ్ ఇవ్వండి',
  verify: 'ధృవీకరించండి', resend: 'కోడ్ మళ్లీ పంపండి', farmScore: 'పొలం స్కోరు',
  cropHealth: 'పంట ఆరోగ్యం', water: 'నీటి అవసరం', todayWeather: 'నేటి వాతావరణం',
  chatTitle: 'అగ్రిసెన్స్‌ను అడగండి',
  chatSubtitle: 'ICAR సాగు మార్గదర్శకాల ఆధారంగా. మోతాదు, సమయం కూడా చెబుతుంది.',
  chatPlaceholder: 'పొలంలో ఏమి కనిపిస్తుందో చెప్పండి…',
  chatStartersIntro: 'వీటిలో ఒకటి ఎంచుకోండి, లేదా మీ మాటల్లో అడగండి:',
  send: 'పంపండి', clear: 'తొలగించండి', readAloud: 'చదివి వినిపించు', speakNow: 'మాట్లాడండి',
  attach: 'ఫోటో లేదా ఫైల్ జోడించండి',
  attachHint: 'ఆకు ఫోటో లేదా భూసార కార్డు జోడించండి (JPG, PNG, PDF, CSV)',
  remove: 'తీసివేయండి', thinking: 'సాగు మార్గదర్శకాలు చూస్తున్నాను…',
  loadingChat: 'మీ సంభాషణ లోడ్ అవుతోంది…', analysingPhoto: 'మీ ఫోటోను పరిశీలిస్తున్నాను…',
  attachedPhoto: 'జోడించిన ఫోటో', attachedFile: 'జోడించిన ఫైల్',
  offlineAnswer: 'ఆఫ్‌లైన్ సమాధానం',
  voiceUnsupported: 'ఈ బ్రౌజర్‌లో వాయిస్ పని చేయదు. ప్రశ్నను టైప్ చేయండి.',
  s1: 'నా వరి ఆకులపై గోధుమ అంచులతో బూడిద మచ్చలు ఉన్నాయి. ఏమి పిచికారీ చేయాలి?',
  s2: 'నల్ల నేలలో 2 ఎకరాల పత్తికి ఎకరానికి ఎంత యూరియా?',
  s3: 'ఈ వారం మొక్కజొన్నకు ఎప్పుడు నీరు పెట్టాలి?',
  s4: 'ఈ రబీలో వరి తర్వాత ఏ పంట వేయాలి?',
}

const ta: Dict = {
  appName: 'அக்ரிசென்ஸ் AI',
  tagline: 'உங்கள் வயலுக்கான பதில்கள், உங்கள் மொழியில்',
  dashboard: 'டாஷ்போர்டு', chat: 'AI யிடம் கேளுங்கள்', disease: 'பயிர் ஸ்கேன்', soil: 'மண் & உரம்',
  weather: 'வானிலை', schemes: 'திட்டங்கள்', yieldp: 'மகசூல்', crops: 'பயிர் தேர்வு',
  notifications: 'எச்சரிக்கைகள்', settings: 'அமைப்புகள்', signOut: 'வெளியேறு',
  phone: 'கைபேசி எண்', sendCode: 'குறியீடு அனுப்பு', enterCode: '6 இலக்க குறியீட்டை உள்ளிடவும்',
  verify: 'சரிபார்க்கவும்', resend: 'மீண்டும் அனுப்பு', farmScore: 'பண்ணை மதிப்பெண்',
  cropHealth: 'பயிர் ஆரோக்கியம்', water: 'நீர் தேவை', todayWeather: 'இன்றைய வானிலை',
  chatTitle: 'அக்ரிசென்ஸிடம் கேளுங்கள்',
  chatSubtitle: 'ICAR வழிகாட்டி குறிப்புகள் அடிப்படையில். அளவும் நேரமும் சொல்லும்.',
  chatPlaceholder: 'வயலில் என்ன தெரிகிறது என்று சொல்லுங்கள்…',
  chatStartersIntro: 'இவற்றில் ஒன்றைத் தேர்வு செய்யுங்கள், அல்லது உங்கள் சொற்களில் கேளுங்கள்:',
  send: 'அனுப்பு', clear: 'அழி', readAloud: 'படித்துக் காட்டு', speakNow: 'பேசுங்கள்',
  attach: 'புகைப்படம் அல்லது கோப்பு இணைக்கவும்',
  attachHint: 'இலைப் புகைப்படம் அல்லது மண் ஆரோக்கிய அட்டையை இணைக்கவும் (JPG, PNG, PDF, CSV)',
  remove: 'நீக்கு', thinking: 'வழிகாட்டி குறிப்புகளைப் பார்க்கிறேன்…',
  loadingChat: 'உங்கள் உரையாடல் ஏற்றப்படுகிறது…', analysingPhoto: 'உங்கள் புகைப்படத்தைப் பார்க்கிறேன்…',
  attachedPhoto: 'இணைத்த புகைப்படம்', attachedFile: 'இணைத்த கோப்பு',
  offlineAnswer: 'ஆஃப்லைன் பதில்',
  voiceUnsupported: 'இந்த உலாவியில் குரல் ஆதரவு இல்லை. கேள்வியைத் தட்டச்சு செய்யுங்கள்.',
  s1: 'என் நெல் இலைகளில் பழுப்பு விளிம்புடன் சாம்பல் புள்ளிகள் உள்ளன. என்ன தெளிக்க வேண்டும்?',
  s2: 'கரிசல் மண்ணில் 2 ஏக்கர் பருத்திக்கு ஏக்கருக்கு எவ்வளவு யூரியா?',
  s3: 'இந்த வாரம் மக்காச்சோளத்திற்கு எப்போது நீர் பாய்ச்ச வேண்டும்?',
  s4: 'இந்த ரபியில் நெல்லுக்குப் பிறகு எந்தப் பயிர் விதைக்க வேண்டும்?',
}

const kn: Dict = {
  appName: 'ಅಗ್ರಿಸೆನ್ಸ್ AI',
  tagline: 'ನಿಮ್ಮ ಹೊಲಕ್ಕೆ ಉತ್ತರಗಳು, ನಿಮ್ಮ ಭಾಷೆಯಲ್ಲಿ',
  dashboard: 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್', chat: 'AI ಯನ್ನು ಕೇಳಿ', disease: 'ಬೆಳೆ ಸ್ಕ್ಯಾನ್', soil: 'ಮಣ್ಣು & ಗೊಬ್ಬರ',
  weather: 'ಹವಾಮಾನ', schemes: 'ಯೋಜನೆಗಳು', yieldp: 'ಇಳುವರಿ', crops: 'ಬೆಳೆ ಆಯ್ಕೆ',
  notifications: 'ಎಚ್ಚರಿಕೆಗಳು', settings: 'ಸೆಟ್ಟಿಂಗ್‌ಗಳು', signOut: 'ಸೈನ್ ಔಟ್',
  phone: 'ಮೊಬೈಲ್ ಸಂಖ್ಯೆ', sendCode: 'ಕೋಡ್ ಕಳುಹಿಸಿ', enterCode: '6 ಅಂಕಿಯ ಕೋಡ್ ನಮೂದಿಸಿ',
  verify: 'ಪರಿಶೀಲಿಸಿ', resend: 'ಕೋಡ್ ಮತ್ತೆ ಕಳುಹಿಸಿ', farmScore: 'ಹೊಲದ ಅಂಕ',
  cropHealth: 'ಬೆಳೆ ಆರೋಗ್ಯ', water: 'ನೀರಿನ ಅಗತ್ಯ', todayWeather: 'ಇಂದಿನ ಹವಾಮಾನ',
  chatTitle: 'ಅಗ್ರಿಸೆನ್ಸ್‌ಗೆ ಕೇಳಿ',
  chatSubtitle: 'ICAR ಮಾರ್ಗಸೂಚಿಗಳ ಆಧಾರದ ಮೇಲೆ. ಪ್ರಮಾಣ ಮತ್ತು ಸಮಯವನ್ನೂ ಹೇಳುತ್ತದೆ.',
  chatPlaceholder: 'ಹೊಲದಲ್ಲಿ ಏನು ಕಾಣುತ್ತಿದೆ ಎಂದು ತಿಳಿಸಿ…',
  chatStartersIntro: 'ಇವುಗಳಲ್ಲಿ ಒಂದನ್ನು ಆರಿಸಿ, ಅಥವಾ ನಿಮ್ಮ ಮಾತಿನಲ್ಲಿ ಕೇಳಿ:',
  send: 'ಕಳುಹಿಸಿ', clear: 'ಅಳಿಸಿ', readAloud: 'ಓದಿ ಹೇಳು', speakNow: 'ಮಾತನಾಡಿ',
  attach: 'ಫೋಟೋ ಅಥವಾ ಕಡತ ಲಗತ್ತಿಸಿ',
  attachHint: 'ಎಲೆಯ ಫೋಟೋ ಅಥವಾ ಮಣ್ಣು ಆರೋಗ್ಯ ಕಾರ್ಡ್ ಲಗತ್ತಿಸಿ (JPG, PNG, PDF, CSV)',
  remove: 'ತೆಗೆದುಹಾಕಿ', thinking: 'ಮಾರ್ಗಸೂಚಿಗಳನ್ನು ನೋಡುತ್ತಿದ್ದೇನೆ…',
  loadingChat: 'ನಿಮ್ಮ ಸಂಭಾಷಣೆ ಲೋಡ್ ಆಗುತ್ತಿದೆ…', analysingPhoto: 'ನಿಮ್ಮ ಫೋಟೋ ನೋಡುತ್ತಿದ್ದೇನೆ…',
  attachedPhoto: 'ಲಗತ್ತಿಸಿದ ಫೋಟೋ', attachedFile: 'ಲಗತ್ತಿಸಿದ ಕಡತ',
  offlineAnswer: 'ಆಫ್‌ಲೈನ್ ಉತ್ತರ',
  voiceUnsupported: 'ಈ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಧ್ವನಿ ಬೆಂಬಲವಿಲ್ಲ. ಪ್ರಶ್ನೆಯನ್ನು ಟೈಪ್ ಮಾಡಿ.',
  s1: 'ನನ್ನ ಭತ್ತದ ಎಲೆಗಳಲ್ಲಿ ಕಂದು ಅಂಚಿನ ಬೂದು ಚುಕ್ಕೆಗಳಿವೆ. ಏನು ಸಿಂಪಡಿಸಬೇಕು?',
  s2: 'ಕಪ್ಪು ಮಣ್ಣಿನಲ್ಲಿ 2 ಎಕರೆ ಹತ್ತಿಗೆ ಎಕರೆಗೆ ಎಷ್ಟು ಯೂರಿಯಾ?',
  s3: 'ಈ ವಾರ ಮೆಕ್ಕೆಜೋಳಕ್ಕೆ ಯಾವಾಗ ನೀರು ಹಾಯಿಸಬೇಕು?',
  s4: 'ಈ ಹಿಂಗಾರಿನಲ್ಲಿ ಭತ್ತದ ನಂತರ ಯಾವ ಬೆಳೆ ಬಿತ್ತಬೇಕು?',
}

const mr: Dict = {
  appName: 'अ‍ॅग्रीसेन्स एआय',
  tagline: 'तुमच्या शेतासाठी उत्तरे, तुमच्या भाषेत',
  dashboard: 'डॅशबोर्ड', chat: 'एआयला विचारा', disease: 'पीक तपासणी', soil: 'माती व खत',
  weather: 'हवामान', schemes: 'योजना', yieldp: 'उत्पादन', crops: 'पीक निवड',
  notifications: 'सूचना', settings: 'सेटिंग्ज', signOut: 'साइन आउट',
  phone: 'मोबाईल नंबर', sendCode: 'कोड पाठवा', enterCode: '6 अंकी कोड टाका',
  verify: 'पडताळणी करा', resend: 'कोड पुन्हा पाठवा', farmScore: 'शेत गुण',
  cropHealth: 'पीक आरोग्य', water: 'पाण्याची गरज', todayWeather: 'आजचे हवामान',
  chatTitle: 'अ‍ॅग्रीसेन्सला विचारा',
  chatSubtitle: 'ICAR मार्गदर्शक नोंदींवर आधारित. मात्रा आणि वेळही सांगते.',
  chatPlaceholder: 'शेतात काय दिसते ते सांगा…',
  chatStartersIntro: 'यापैकी एक निवडा, किंवा तुमच्या शब्दांत विचारा:',
  send: 'पाठवा', clear: 'साफ करा', readAloud: 'वाचून दाखवा', speakNow: 'बोला',
  attach: 'फोटो किंवा फाइल जोडा',
  attachHint: 'पानाचा फोटो किंवा मृदा आरोग्य पत्रिका जोडा (JPG, PNG, PDF, CSV)',
  remove: 'काढा', thinking: 'मार्गदर्शक नोंदी पाहत आहे…',
  loadingChat: 'तुमचे संभाषण लोड होत आहे…', analysingPhoto: 'तुमचा फोटो पाहत आहे…',
  attachedPhoto: 'जोडलेला फोटो', attachedFile: 'जोडलेली फाइल',
  offlineAnswer: 'ऑफलाइन उत्तर',
  voiceUnsupported: 'या ब्राउझरमध्ये आवाज चालत नाही. प्रश्न टाइप करा.',
  s1: 'माझ्या भाताच्या पानांवर तपकिरी कडा असलेले करडे ठिपके आहेत. काय फवारावे?',
  s2: 'काळ्या मातीत 2 एकर कापसासाठी एकरी किती युरिया?',
  s3: 'या आठवड्यात मक्याला पाणी कधी द्यावे?',
  s4: 'या रब्बीत भातानंतर कोणते पीक घ्यावे?',
}

const bn: Dict = {
  appName: 'অ্যাগ্রিসেন্স এআই',
  tagline: 'আপনার জমির উত্তর, আপনার ভাষায়',
  dashboard: 'ড্যাশবোর্ড', chat: 'এআইকে জিজ্ঞাসা করুন', disease: 'ফসল স্ক্যান', soil: 'মাটি ও সার',
  weather: 'আবহাওয়া', schemes: 'প্রকল্প', yieldp: 'ফলন', crops: 'ফসল নির্বাচন',
  notifications: 'সতর্কতা', settings: 'সেটিংস', signOut: 'সাইন আউট',
  phone: 'মোবাইল নম্বর', sendCode: 'কোড পাঠান', enterCode: '৬ সংখ্যার কোড দিন',
  verify: 'যাচাই করুন', resend: 'আবার কোড পাঠান', farmScore: 'জমির স্কোর',
  cropHealth: 'ফসলের স্বাস্থ্য', water: 'জলের প্রয়োজন', todayWeather: 'আজকের আবহাওয়া',
  chatTitle: 'অ্যাগ্রিসেন্সকে জিজ্ঞাসা করুন',
  chatSubtitle: 'ICAR নির্দেশিকার ভিত্তিতে। মাত্রা ও সময়ও জানায়।',
  chatPlaceholder: 'জমিতে যা দেখছেন তা বলুন…',
  chatStartersIntro: 'এর একটি বেছে নিন, বা নিজের ভাষায় জিজ্ঞাসা করুন:',
  send: 'পাঠান', clear: 'মুছুন', readAloud: 'পড়ে শোনান', speakNow: 'বলুন',
  attach: 'ছবি বা ফাইল যোগ করুন',
  attachHint: 'পাতার ছবি বা মাটি স্বাস্থ্য কার্ড যোগ করুন (JPG, PNG, PDF, CSV)',
  remove: 'সরান', thinking: 'নির্দেশিকা দেখছি…',
  loadingChat: 'আপনার কথোপকথন লোড হচ্ছে…', analysingPhoto: 'আপনার ছবি দেখছি…',
  attachedPhoto: 'যুক্ত ছবি', attachedFile: 'যুক্ত ফাইল',
  offlineAnswer: 'অফলাইন উত্তর',
  voiceUnsupported: 'এই ব্রাউজারে কণ্ঠস্বর কাজ করে না। প্রশ্নটি টাইপ করুন।',
  s1: 'আমার ধানের পাতায় বাদামি কিনারাসহ ধূসর দাগ। কী স্প্রে করব?',
  s2: 'কালো মাটিতে ২ একর তুলার জন্য একরপ্রতি কত ইউরিয়া?',
  s3: 'এই সপ্তাহে ভুট্টায় কখন সেচ দেব?',
  s4: 'এই রবিতে ধানের পরে কোন ফসল বুনব?',
}

const pa: Dict = {
  appName: 'ਐਗਰੀਸੈਂਸ ਏਆਈ',
  tagline: 'ਤੁਹਾਡੇ ਖੇਤ ਦੇ ਜਵਾਬ, ਤੁਹਾਡੀ ਭਾਸ਼ਾ ਵਿੱਚ',
  dashboard: 'ਡੈਸ਼ਬੋਰਡ', chat: 'ਏਆਈ ਤੋਂ ਪੁੱਛੋ', disease: 'ਫ਼ਸਲ ਜਾਂਚ', soil: 'ਮਿੱਟੀ ਤੇ ਖਾਦ',
  weather: 'ਮੌਸਮ', schemes: 'ਸਕੀਮਾਂ', yieldp: 'ਝਾੜ', crops: 'ਫ਼ਸਲ ਚੋਣ',
  notifications: 'ਚੇਤਾਵਨੀਆਂ', settings: 'ਸੈਟਿੰਗਾਂ', signOut: 'ਸਾਈਨ ਆਉਟ',
  phone: 'ਮੋਬਾਈਲ ਨੰਬਰ', sendCode: 'ਕੋਡ ਭੇਜੋ', enterCode: '6 ਅੰਕਾਂ ਦਾ ਕੋਡ ਪਾਓ',
  verify: 'ਪੁਸ਼ਟੀ ਕਰੋ', resend: 'ਕੋਡ ਮੁੜ ਭੇਜੋ', farmScore: 'ਖੇਤ ਸਕੋਰ',
  cropHealth: 'ਫ਼ਸਲ ਸਿਹਤ', water: 'ਪਾਣੀ ਦੀ ਲੋੜ', todayWeather: 'ਅੱਜ ਦਾ ਮੌਸਮ',
  chatTitle: 'ਐਗਰੀਸੈਂਸ ਤੋਂ ਪੁੱਛੋ',
  chatSubtitle: 'ICAR ਹਦਾਇਤਾਂ ਉੱਤੇ ਆਧਾਰਿਤ। ਮਾਤਰਾ ਅਤੇ ਸਮਾਂ ਵੀ ਦੱਸਦਾ ਹੈ।',
  chatPlaceholder: 'ਖੇਤ ਵਿੱਚ ਜੋ ਦਿੱਸ ਰਿਹਾ ਹੈ ਦੱਸੋ…',
  chatStartersIntro: 'ਇਹਨਾਂ ਵਿੱਚੋਂ ਇੱਕ ਚੁਣੋ, ਜਾਂ ਆਪਣੇ ਸ਼ਬਦਾਂ ਵਿੱਚ ਪੁੱਛੋ:',
  send: 'ਭੇਜੋ', clear: 'ਸਾਫ਼ ਕਰੋ', readAloud: 'ਪੜ੍ਹ ਕੇ ਸੁਣਾਓ', speakNow: 'ਬੋਲੋ',
  attach: 'ਫੋਟੋ ਜਾਂ ਫਾਈਲ ਜੋੜੋ',
  attachHint: 'ਪੱਤੇ ਦੀ ਫੋਟੋ ਜਾਂ ਮਿੱਟੀ ਸਿਹਤ ਕਾਰਡ ਜੋੜੋ (JPG, PNG, PDF, CSV)',
  remove: 'ਹਟਾਓ', thinking: 'ਹਦਾਇਤਾਂ ਵੇਖ ਰਿਹਾ ਹਾਂ…',
  loadingChat: 'ਤੁਹਾਡੀ ਗੱਲਬਾਤ ਲੋਡ ਹੋ ਰਹੀ ਹੈ…', analysingPhoto: 'ਤੁਹਾਡੀ ਫੋਟੋ ਵੇਖ ਰਿਹਾ ਹਾਂ…',
  attachedPhoto: 'ਜੋੜੀ ਫੋਟੋ', attachedFile: 'ਜੋੜੀ ਫਾਈਲ',
  offlineAnswer: 'ਆਫ਼ਲਾਈਨ ਜਵਾਬ',
  voiceUnsupported: 'ਇਸ ਬ੍ਰਾਊਜ਼ਰ ਵਿੱਚ ਆਵਾਜ਼ ਨਹੀਂ ਚੱਲਦੀ। ਸਵਾਲ ਟਾਈਪ ਕਰੋ।',
  s1: 'ਮੇਰੇ ਝੋਨੇ ਦੇ ਪੱਤਿਆਂ ਉੱਤੇ ਭੂਰੇ ਕਿਨਾਰਿਆਂ ਵਾਲੇ ਸਲੇਟੀ ਧੱਬੇ ਹਨ। ਕੀ ਛਿੜਕਾਂ?',
  s2: 'ਕਾਲੀ ਮਿੱਟੀ ਵਿੱਚ 2 ਏਕੜ ਨਰਮੇ ਲਈ ਪ੍ਰਤੀ ਏਕੜ ਕਿੰਨੀ ਯੂਰੀਆ?',
  s3: 'ਇਸ ਹਫ਼ਤੇ ਮੱਕੀ ਨੂੰ ਪਾਣੀ ਕਦੋਂ ਲਾਵਾਂ?',
  s4: 'ਇਸ ਹਾੜ੍ਹੀ ਵਿੱਚ ਝੋਨੇ ਤੋਂ ਬਾਅਦ ਕਿਹੜੀ ਫ਼ਸਲ ਬੀਜਾਂ?',
}

const DICTS: Record<string, Dict> = { en, hi, te, ta, kn, mr, bn, pa }

export const LANGUAGES = [
  { code: 'en', native: 'English' },
  { code: 'hi', native: 'हिन्दी' },
  { code: 'te', native: 'తెలుగు' },
  { code: 'ta', native: 'தமிழ்' },
  { code: 'kn', native: 'ಕನ್ನಡ' },
  { code: 'mr', native: 'मराठी' },
  { code: 'bn', native: 'বাংলা' },
  { code: 'pa', native: 'ਪੰਜਾਬੀ' },
]

/** BCP-47 tags for Web Speech. One place, so voice in and voice out agree. */
export const SPEECH_TAG: Record<string, string> = {
  en: 'en-IN', hi: 'hi-IN', te: 'te-IN', ta: 'ta-IN',
  kn: 'kn-IN', mr: 'mr-IN', bn: 'bn-IN', pa: 'pa-IN',
}

type LangState = { lang: string; setLang: (l: string) => void }
export const useLang = create<LangState>()(
  persist((set) => ({ lang: 'en', setLang: (lang) => set({ lang }) }), { name: 'agrisense-lang' })
)

export type TKey = keyof typeof en

export const useT = () => {
  const lang = useLang((s) => s.lang)
  const dict = DICTS[lang] ?? en
  return (key: TKey) => dict[key] ?? en[key] ?? String(key)
}

export const speak = (text: string, lang: string) => {
  if (!('speechSynthesis' in window)) return
  // Strip the markdown we use for headings so the voice does not read asterisks.
  const clean = text.replace(/[*_#`]/g, '')
  const u = new SpeechSynthesisUtterance(clean)
  u.lang = SPEECH_TAG[lang] ?? 'en-IN'
  u.rate = 0.95
  speechSynthesis.cancel()
  speechSynthesis.speak(u)
}
