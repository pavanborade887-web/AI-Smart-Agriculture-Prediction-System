from collections import Counter
from datetime import UTC, datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select
from app.api.deps import DbSession, get_current_user
from app.models import DiseaseDetection, Notification, Prediction, User, WeatherLog

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def serialize_prediction(prediction: Prediction) -> dict:
    return {
        "id": prediction.id,
        "type": prediction.prediction_type,
        "result": prediction.result_data,
        "confidence": prediction.confidence,
        "created_at": prediction.created_at.isoformat(),
    }


@router.get("/summary")
def summary(db: DbSession, user: User = Depends(get_current_user)):
    predictions = list(db.scalars(select(Prediction).where(Prediction.user_id == user.id).order_by(Prediction.created_at.desc()).limit(100)))
    notifications = list(db.scalars(select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(6)))
    latest_weather = db.scalar(select(WeatherLog).where(WeatherLog.user_id == user.id).order_by(WeatherLog.observed_at.desc()))
    disease_count = db.scalar(select(DiseaseDetection).where(DiseaseDetection.user_id == user.id).order_by(DiseaseDetection.created_at.desc()).limit(1))
    recent = [serialize_prediction(item) for item in predictions[:5]]
    since = datetime.now(UTC) - timedelta(days=6)
    per_day = Counter(item.created_at.date().isoformat() for item in predictions if item.created_at.replace(tzinfo=UTC) >= since)
    timeline = [{"date": (since + timedelta(days=index)).date().isoformat(), "count": per_day.get((since + timedelta(days=index)).date().isoformat(), 0)} for index in range(7)]
    latest_crop = next((item for item in predictions if item.prediction_type == "crop"), None)
    latest_soil = next((item for item in predictions if item.prediction_type == "soil_health"), None)
    return {
        "user_name": user.full_name,
        "stats": {
            "total_predictions": len(predictions),
            "unread_notifications": sum(not item.is_read for item in notifications),
            "latest_crop": latest_crop.result_data if latest_crop else None,
            "soil_health": latest_soil.result_data if latest_soil else None,
            "disease_status": disease_count.disease_name if disease_count else None,
        },
        "weather": latest_weather.data if latest_weather else None,
        "notifications": [{"id": item.id, "category": item.category, "title": item.title, "message": item.message, "is_read": item.is_read, "created_at": item.created_at.isoformat()} for item in notifications],
        "recent_predictions": recent,
        "timeline": timeline,
    }
