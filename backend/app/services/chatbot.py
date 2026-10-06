from app.core.config import get_settings
from app.services.agriculture import local_agriculture_answer
import httpx

SYSTEM_PROMPT = """You are AgriSense, a concise agriculture assistant. Give safe, practical, climate-aware guidance. Do not invent local regulations, pesticide labels, or diagnoses. Recommend soil tests or qualified local advice when decisions have high risk."""
MARATHI_FALLBACKS = {
    "Check root-zone soil moisture before irrigating. If moisture is low and meaningful rain is not forecast, irrigate early morning or evening. Use mulch to reduce evaporation and avoid standing water around roots. The Smart Irrigation tool can calculate the water amount from your field values.": "सिंचनापूर्वी मुळांच्या परिसरातील ओलावा तपासा. ओलावा कमी असेल आणि पावसाचा अंदाज नसेल तर सकाळी लवकर किंवा संध्याकाळी पाणी द्या. बाष्पीभवन कमी करण्यासाठी आच्छादन वापरा आणि मुळांजवळ पाणी साचू देऊ नका. तुमच्या शेतासाठी पाण्याचे प्रमाण काढण्यासाठी स्मार्ट सिंचन साधन वापरा.",
    "Base fertilizer on a recent soil test. Apply nitrogen in split doses, place phosphorus near the root zone at planting, and use potassium where soil levels are low. Add mature compost or farmyard manure to improve organic carbon and nutrient retention.": "अलीकडील माती परीक्षणानुसार खत ठरवा. नत्राचे हप्त्यांमध्ये नियोजन करा, लागवडीवेळी स्फुरद मुळांच्या जवळ द्या आणि मातीतील पालाश कमी असल्यास त्याची भर घाला. सेंद्रिय कर्ब व अन्नद्रव्ये टिकवण्यासाठी चांगले कुजलेले कंपोस्ट किंवा शेणखत वापरा.",
    "First identify the crop and visible symptom, then isolate badly affected plants and avoid working with wet leaves. Use clean tools, improve airflow, and upload a clear leaf image in Disease Detection for a visible-stress assessment before choosing treatment.": "आधी पीक आणि दिसणारी लक्षणे ओळखा. जास्त बाधित झाडे वेगळी ठेवा आणि ओली पाने हाताळणे टाळा. स्वच्छ साधने वापरा, हवा खेळती ठेवा आणि उपचार ठरवण्यापूर्वी रोग ओळख साधनात पानाचा स्पष्ट फोटो तपासा.",
    "Use the Weather Analysis tool for current conditions and forecast. Avoid spraying in strong wind or before rain, postpone irrigation when useful rainfall is expected, and increase disease scouting during prolonged high humidity.": "सध्याची स्थिती आणि अंदाजासाठी हवामान विश्लेषण साधन वापरा. जोराच्या वाऱ्यात किंवा पावसाआधी फवारणी करू नका. उपयुक्त पाऊस अपेक्षित असल्यास सिंचन पुढे ढकला आणि जास्त आर्द्रता टिकल्यास रोगांची अधिक तपासणी करा.",
    "A productive soil usually has balanced NPK, adequate organic carbon, good drainage, and crop-appropriate pH. Add compost and crop residue where organic carbon is low, and use a laboratory soil test before applying lime or sulphur to correct pH.": "उत्पादक मातीमध्ये NPK संतुलन, पुरेसा सेंद्रिय कर्ब, चांगला निचरा आणि पिकास योग्य pH असतो. सेंद्रिय कर्ब कमी असल्यास कंपोस्ट व पीक अवशेष मिसळा. pH सुधारण्यासाठी चुना किंवा गंधक देण्यापूर्वी प्रयोगशाळेत माती तपासा.",
    "Yield depends on crop variety, area, historical yield, weather, soil, and nutrient management. Use the Yield Prediction tool with your actual field values for an estimated production, income range, and confidence score.": "उत्पादन हे वाण, क्षेत्रफळ, मागील उत्पादन, हवामान, माती आणि अन्नद्रव्य व्यवस्थापनावर अवलंबून असते. अंदाजे उत्पादन, उत्पन्नाची मर्यादा आणि विश्वास पातळीसाठी प्रत्यक्ष शेतमाहितीसह उत्पादन अंदाज साधन वापरा.",
    "Track verified local mandi prices and avoid selling solely on a single-day movement. Enter recent prices in Market Price Prediction to see the trend and the estimated stronger selling window.": "स्थानिक बाजार समितीतील पडताळलेले भाव पाहा आणि एका दिवसाच्या बदलावरच विक्रीचा निर्णय घेऊ नका. भावांचा कल आणि विक्रीची संभाव्य योग्य वेळ पाहण्यासाठी बाजारभाव अंदाज साधनात अलीकडील भाव भरा.",
    "Tell me the crop name and your location, soil type, irrigation availability, and season. I will suggest spacing, soil preparation, fertilizer timing, irrigation, and disease-prevention steps for that crop.": "पिकाचे नाव, तुमचे ठिकाण, मातीचा प्रकार, सिंचनाची उपलब्धता आणि हंगाम सांगा. त्या पिकासाठी अंतर, जमीन तयारी, खत देण्याची वेळ, सिंचन आणि रोगप्रतिबंधक उपाय सुचवेन.",
    "I can help with crop choice, soil health, fertilizer, irrigation, weather, disease prevention, yield, and market timing. Share your crop, location, and current field conditions for a more specific answer.": "मी पीक निवड, मातीचे आरोग्य, खत, सिंचन, हवामान, रोगप्रतिबंध, उत्पादन आणि बाजारभावाबाबत मदत करू शकतो. अधिक नेमक्या सल्ल्यासाठी पीक, ठिकाण आणि सध्याची शेतस्थिती सांगा.",
}

def answer(message: str, history: list[dict], language: str = "en", offline_attachment: dict | None = None) -> str:
    settings = get_settings()
    system_prompt = SYSTEM_PROMPT if language == "en" else f"{SYSTEM_PROMPT} Reply in Marathi (मराठी) throughout, using clear language for an Indian farmer."
    if settings.gemini_api_key:
        try:
            contents = [{"role": "user" if item["role"] == "user" else "model", "parts": [{"text": item["content"]}]} for item in history[-10:]]
            contents.append({"role": "user", "parts": [{"text": message}]})
            response = httpx.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent",
                params={"key": settings.gemini_api_key},
                json={"system_instruction": {"parts": [{"text": system_prompt}]}, "contents": contents, "generationConfig": {"temperature": 0.3, "maxOutputTokens": 500}},
                timeout=20,
            )
            response.raise_for_status()
            text = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            if text:
                return text
        except (httpx.HTTPError, KeyError, IndexError, TypeError):
            pass
    if not settings.openai_api_key:
        if offline_attachment:
            return _offline_document_reply(offline_attachment, language)
        return _localized_fallback(message, language)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        messages = [{"role": "system", "content": system_prompt}, *history[-10:], {"role": "user", "content": message}]
        response = client.chat.completions.create(model=settings.openai_model, messages=messages, temperature=.3, max_tokens=500)
        response_text = response.choices[0].message.content
        if response_text:
            return response_text
        if offline_attachment:
            return _offline_document_reply(offline_attachment, language)
        return _localized_fallback(message, language)
    except Exception:
        if offline_attachment:
            return _offline_document_reply(offline_attachment, language)
        return _localized_fallback(message, language)


def _localized_fallback(message: str, language: str) -> str:
    answer_text = local_agriculture_answer(message)
    return MARATHI_FALLBACKS.get(answer_text, answer_text) if language == "mr" else answer_text


def _offline_document_reply(attachment: dict, language: str) -> str:
    lines = [line.strip() for line in attachment["text"].splitlines() if line.strip()]
    excerpt = "\n".join(lines[:6])[:1200]
    if language == "mr":
        return (
            f"{attachment['filename']} फाइल वाचून मजकूर काढला आहे. एआय सेवा सध्या उपलब्ध नसल्यामुळे हा पूर्ण विश्लेषणाऐवजी मजकूराचा नमुना आहे:\n\n"
            f"{excerpt}\n\n"
            "फाइलचे पूर्ण विश्लेषण मिळवण्यासाठी कार्यरत Gemini किंवा OpenAI API key आवश्यक आहे."
        )
    return (
        f"I received and extracted {attachment['filename']}. "
        "The AI provider is unavailable, so this is a text preview rather than a full analysis:\n\n"
        f"{excerpt}\n\n"
        "Configure a working Gemini or OpenAI API key to get a full answer about the document."
    )
