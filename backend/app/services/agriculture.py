"""Domain inference engines used when a trained model is unavailable or inappropriate.

The recommendations are deterministic, explainable agronomic calculations. Uploaded
datasets can subsequently be used to train and activate statistical model versions.
"""
from __future__ import annotations
from statistics import mean

CROPS = {
    "rice": {"temp": 27, "rain": 1200, "ph": 6.2, "n": 110, "p": 45, "k": 45, "price": 22000},
    "wheat": {"temp": 20, "rain": 550, "ph": 6.8, "n": 120, "p": 50, "k": 40, "price": 24000},
    "maize": {"temp": 25, "rain": 700, "ph": 6.5, "n": 120, "p": 55, "k": 45, "price": 21000},
    "cotton": {"temp": 28, "rain": 750, "ph": 7.2, "n": 100, "p": 50, "k": 50, "price": 68000},
    "chickpea": {"temp": 22, "rain": 450, "ph": 7.0, "n": 35, "p": 50, "k": 30, "price": 56000},
    "sugarcane": {"temp": 28, "rain": 1100, "ph": 7.0, "n": 160, "p": 60, "k": 80, "price": 3500},
}

def bounded(value: float, minimum: float = 0, maximum: float = 100) -> float: return round(max(minimum, min(maximum, value)), 1)
def similarity(value: float, target: float, tolerance: float) -> float: return max(0, 1 - abs(value - target) / tolerance)

def crop_recommendation(data: dict) -> dict:
    ranked = []
    for crop, optimum in CROPS.items():
        score = mean([similarity(data["temperature"], optimum["temp"], 15), similarity(data["rainfall"], optimum["rain"], 900), similarity(data["ph"], optimum["ph"], 2.5), similarity(data["nitrogen"], optimum["n"], 120), similarity(data["phosphorus"], optimum["p"], 80), similarity(data["potassium"], optimum["k"], 80)])
        ranked.append((crop, bounded(score * 100)))
    ranked.sort(key=lambda entry: entry[1], reverse=True)
    crop, confidence = ranked[0]; expected_income = round(CROPS[crop]["price"] * {"rice": 4.2, "wheat": 3.4, "maize": 4.8, "cotton": 2.0, "chickpea": 1.7, "sugarcane": 70}[crop])
    return {"best_crop": crop.title(), "confidence": confidence / 100, "alternatives": [{"crop": name.title(), "suitability": score} for name, score in ranked[1:4]], "expected_income_inr_per_hectare": expected_income, "expected_profit_inr_per_hectare": round(expected_income * .42), "basis": "soil nutrient, climate, rainfall and pH suitability"}

def fertilizer_recommendation(data: dict) -> dict:
    optimum = CROPS.get(data["crop"].lower(), {"n": 100, "p": 45, "k": 40})
    gaps = {"nitrogen": max(0, optimum["n"] - data["nitrogen"]), "phosphorus": max(0, optimum["p"] - data["phosphorus"]), "potassium": max(0, optimum["k"] - data["potassium"])}
    products = []
    if gaps["nitrogen"]: products.append({"name": "Urea", "quantity_kg_per_hectare": round(gaps["nitrogen"] / .46, 1), "purpose": "Correct nitrogen deficiency"})
    if gaps["phosphorus"]: products.append({"name": "DAP", "quantity_kg_per_hectare": round(gaps["phosphorus"] / .46, 1), "purpose": "Correct phosphorus deficiency"})
    if gaps["potassium"]: products.append({"name": "MOP", "quantity_kg_per_hectare": round(gaps["potassium"] / .60, 1), "purpose": "Correct potassium deficiency"})
    ph_note = "Apply agricultural lime after a soil test" if data["ph"] < 5.8 else "Use elemental sulphur only after a soil test" if data["ph"] > 7.8 else "pH is within the productive range"
    return {"recommended_fertilizers": products or [{"name": "No corrective mineral fertilizer", "quantity_kg_per_hectare": 0, "purpose": "NPK level is adequate"}], "deficiency_analysis": {key: round(value, 1) for key, value in gaps.items()}, "organic_alternatives": ["Well-matured farmyard manure (5–10 t/ha)", "Compost with crop-residue mulch", "Neem-coated urea for reduced nitrogen loss"], "ph_guidance": ph_note}

def soil_health(data: dict) -> dict:
    components = [similarity(data["nitrogen"], 100, 100), similarity(data["phosphorus"], 45, 55), similarity(data["potassium"], 45, 65), similarity(data["organic_carbon"], .75, 1), similarity(data["moisture"], 35, 40), similarity(data["ph"], 6.8, 2)]
    score = bounded(mean(components) * 100); grade = "Excellent" if score >= 80 else "Good" if score >= 65 else "Moderate" if score >= 45 else "Needs attention"
    suggestions = []
    if data["organic_carbon"] < .5: suggestions.append("Incorporate compost, green manure, and cover crops to improve organic carbon.")
    if data["ph"] < 5.8: suggestions.append("Confirm acidity with a laboratory test before applying agricultural lime.")
    if data["ph"] > 7.8: suggestions.append("Use organic matter and seek a local soil test before sulphur treatment.")
    if not suggestions: suggestions.append("Maintain residue cover and retest soil before the next crop cycle.")
    return {"health_score": score, "grade": grade, "color": "#4e8732" if score >= 65 else "#d59d2a" if score >= 45 else "#d45c4c", "suggestions": suggestions}

def yield_prediction(data: dict) -> dict:
    rain_factor = similarity(data["rainfall"], 800, 900); temp_factor = similarity(data["temperature"], 25, 15); fertilizer_factor = min(1.15, .65 + data["fertilizer_kg"] / 500)
    per_ha = round(data["historical_yield_tonnes_per_hectare"] * (.55 + .25 * rain_factor + .20 * temp_factor) * fertilizer_factor, 2); production = round(per_ha * data["area_hectares"], 2)
    price = CROPS.get(data["crop"].lower(), {}).get("price", 25000)
    return {"expected_production_tonnes": production, "expected_yield_tonnes_per_hectare": per_ha, "expected_income_inr": round(production * price), "confidence": bounded((rain_factor + temp_factor) * 50) / 100, "drivers": {"rainfall_suitability": bounded(rain_factor * 100), "temperature_suitability": bounded(temp_factor * 100)}}

def irrigation_recommendation(data: dict) -> dict:
    threshold = 38 if data["crop"].lower() in {"rice", "sugarcane"} else 30; deficit = max(0, threshold - data["soil_moisture"]); hotness = max(0, data["temperature"] - 24) * 1.5; rain_credit = min(30, data["rainfall_forecast_mm"])
    mm = max(0, round(deficit + hotness - rain_credit)); irrigate = mm >= 8
    return {"irrigate_today": irrigate, "next_irrigation": "Today before 9 AM or after 5 PM" if irrigate else "Reassess after the forecast rain or within 48 hours", "water_amount_mm": mm, "water_volume_litres": round(mm * data["area_hectares"] * 10000), "reason": "Soil moisture deficit adjusted for heat stress and forecast rainfall"}

def market_prediction(data: dict) -> dict:
    prices = data["historical_prices"]; n = len(prices); x_mean = (n - 1) / 2; y_mean = mean(prices); denominator = sum((i - x_mean) ** 2 for i in range(n)) or 1; slope = sum((i - x_mean) * (price - y_mean) for i, price in enumerate(prices)) / denominator
    forecast = [round(max(1, prices[-1] + slope * day), 2) for day in range(1, data["days_ahead"] + 1)]; best = max(range(len(forecast)), key=forecast.__getitem__) + 1
    return {"forecast_prices": forecast, "trend": "rising" if slope > 0 else "falling" if slope < 0 else "stable", "daily_change_inr": round(slope, 2), "best_selling_day": best, "expected_profit_change_percent": round((forecast[best - 1] / data["current_price"] - 1) * 100, 2)}

def local_agriculture_answer(question: str) -> str:
    q = question.lower()
    if "irrig" in q or "water" in q:
        return "Check root-zone soil moisture before irrigating. If moisture is low and meaningful rain is not forecast, irrigate early morning or evening. Use mulch to reduce evaporation and avoid standing water around roots. The Smart Irrigation tool can calculate the water amount from your field values."
    if "fertili" in q or "npk" in q or "urea" in q:
        return "Base fertilizer on a recent soil test. Apply nitrogen in split doses, place phosphorus near the root zone at planting, and use potassium where soil levels are low. Add mature compost or farmyard manure to improve organic carbon and nutrient retention."
    if "disease" in q or "leaf" in q or "pest" in q:
        return "First identify the crop and visible symptom, then isolate badly affected plants and avoid working with wet leaves. Use clean tools, improve airflow, and upload a clear leaf image in Disease Detection for a visible-stress assessment before choosing treatment."
    if "weather" in q or "rain" in q or "temperature" in q:
        return "Use the Weather Analysis tool for current conditions and forecast. Avoid spraying in strong wind or before rain, postpone irrigation when useful rainfall is expected, and increase disease scouting during prolonged high humidity."
    if "soil" in q or "ph" in q or "organic carbon" in q:
        return "A productive soil usually has balanced NPK, adequate organic carbon, good drainage, and crop-appropriate pH. Add compost and crop residue where organic carbon is low, and use a laboratory soil test before applying lime or sulphur to correct pH."
    if "yield" in q or "production" in q:
        return "Yield depends on crop variety, area, historical yield, weather, soil, and nutrient management. Use the Yield Prediction tool with your actual field values for an estimated production, income range, and confidence score."
    if "market" in q or "price" in q or "sell" in q:
        return "Track verified local mandi prices and avoid selling solely on a single-day movement. Enter recent prices in Market Price Prediction to see the trend and the estimated stronger selling window."
    if "tomato" in q:
        return "For tomato cultivation, use well-drained soil with pH 6.0–6.8, transplant healthy seedlings 45–60 cm apart, and provide 6–8 hours of sun. Keep soil evenly moist, mulch to reduce water loss, and apply compost before planting. Inspect leaves twice weekly for whiteflies, leaf spots, and curling."
    if "rice" in q or "paddy" in q:
        return "For rice, use a field with reliable water management, transplant vigorous seedlings at the locally recommended spacing, and split nitrogen into multiple applications rather than applying it all at once. Maintain water according to crop stage and drain before harvest so the field can dry safely."
    if "wheat" in q:
        return "For wheat, sow into a fine, well-drained seedbed during the locally recommended season. Use a soil-test-based fertilizer plan, avoid excess nitrogen early in the season, irrigate at critical crown-root, tillering, flowering, and grain-filling stages, and monitor for rust symptoms."
    if "maize" in q or "corn" in q:
        return "For maize, plant in warm soil with good drainage and adequate spacing for sunlight. Split nitrogen applications around early growth and knee-high stages, remove weeds early, and irrigate during tasseling and grain filling if rainfall is insufficient."
    if "make" in q or "grow" in q or "cultivat" in q or "plant" in q:
        return "Tell me the crop name and your location, soil type, irrigation availability, and season. I will suggest spacing, soil preparation, fertilizer timing, irrigation, and disease-prevention steps for that crop."
    if "irrig" in q: return "Irrigate based on measured root-zone moisture, forecast rainfall, and crop stage. Water early morning or evening; avoid irrigation before meaningful forecast rain."
    if "fertili" in q or "npk" in q: return "Use a soil test to match NPK applications to the crop and field. Split nitrogen applications to reduce losses, and add compost to support soil organic carbon."
    if "disease" in q or "leaf" in q: return "Isolate affected plants, remove severely infected leaves hygienically, and confirm the disease before applying treatment. Avoid spraying in wind or heat."
    if "crop" in q: return "Choose crops using soil pH, nutrient status, season, expected rainfall, local market access, and irrigation availability. The Crop Prediction page combines these field inputs."
    return "I can help with crop choice, soil health, fertilizer, irrigation, weather, disease prevention, yield, and market timing. Share your crop, location, and current field conditions for a more specific answer."
