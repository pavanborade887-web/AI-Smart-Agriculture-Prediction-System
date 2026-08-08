from app.services.agriculture import crop_recommendation, fertilizer_recommendation, irrigation_recommendation, market_prediction, soil_health, yield_prediction

def test_crop_prediction_ranks_a_crop():
    result = crop_recommendation({"temperature": 26, "rainfall": 900, "ph": 6.5, "nitrogen": 100, "phosphorus": 45, "potassium": 45})
    assert result["best_crop"] and 0 <= result["confidence"] <= 1

def test_fertilizer_reports_deficits():
    result = fertilizer_recommendation({"crop": "wheat", "nitrogen": 20, "phosphorus": 10, "potassium": 10, "ph": 6.5, "moisture": 30})
    assert result["deficiency_analysis"]["nitrogen"] > 0

def test_soil_and_irrigation_are_bounded():
    soil = soil_health({"nitrogen": 80, "phosphorus": 40, "potassium": 40, "organic_carbon": .7, "moisture": 30, "ph": 6.5})
    irrigation = irrigation_recommendation({"crop": "maize", "soil_moisture": 15, "temperature": 32, "humidity": 50, "rainfall_forecast_mm": 0, "area_hectares": 1})
    assert 0 <= soil["health_score"] <= 100 and irrigation["water_volume_litres"] > 0

def test_yield_and_market_prediction():
    yield_result = yield_prediction({"crop": "wheat", "area_hectares": 2, "rainfall": 600, "temperature": 20, "fertilizer_kg": 160, "soil_type": "loam", "historical_yield_tonnes_per_hectare": 3})
    market = market_prediction({"crop": "wheat", "current_price": 2000, "historical_prices": [1800, 1850, 1900], "days_ahead": 5})
    assert yield_result["expected_production_tonnes"] > 0 and len(market["forecast_prices"]) == 5
