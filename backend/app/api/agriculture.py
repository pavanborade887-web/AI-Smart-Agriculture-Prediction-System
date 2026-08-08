from datetime import UTC, datetime
from pathlib import Path
import shutil
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from app.api.deps import DbSession, get_current_user, require_admin
from app.core.config import get_settings
from app.models import ChatMessage, Dataset, DiseaseDetection, ModelVersion, Notification, Prediction, Report, Role, User, WeatherLog
from app.schemas import ChatRequest, CropInput, FertilizerInput, IrrigationInput, MarketInput, SoilInput, WeatherRequest, YieldInput
from app.services import agriculture as engine
from app.services.disease import analyse_leaf
from app.services.reports import build_report
from app.services.weather import fetch_weather, weather_advice
from app.ml.training import train_regressor
from app.services.chatbot import answer as chatbot_answer

router = APIRouter(tags=["Agriculture"])
settings = get_settings()

def save_prediction(db: DbSession, user_id: int, prediction_type: str, input_data: dict, result: dict, confidence: float | None = None) -> dict:
    record = Prediction(user_id=user_id, prediction_type=prediction_type, input_data=input_data, result_data=result, confidence=confidence)
    db.add(record); db.commit(); db.refresh(record); return {"id": record.id, "result": result}

@router.post("/crop-predictions", status_code=status.HTTP_201_CREATED)
def predict_crop(payload: CropInput, db: DbSession, user: User = Depends(get_current_user)):
    result = engine.crop_recommendation(payload.model_dump()); return save_prediction(db, user.id, "crop", payload.model_dump(), result, result["confidence"])

@router.post("/fertilizer-recommendations", status_code=status.HTTP_201_CREATED)
def recommend_fertilizer(payload: FertilizerInput, db: DbSession, user: User = Depends(get_current_user)):
    result = engine.fertilizer_recommendation(payload.model_dump()); return save_prediction(db, user.id, "fertilizer", payload.model_dump(), result)

@router.post("/yield-predictions", status_code=status.HTTP_201_CREATED)
def predict_yield(payload: YieldInput, db: DbSession, user: User = Depends(get_current_user)):
    result = engine.yield_prediction(payload.model_dump()); return save_prediction(db, user.id, "yield", payload.model_dump(), result, result["confidence"])

@router.post("/soil-health", status_code=status.HTTP_201_CREATED)
def analyze_soil(payload: SoilInput, db: DbSession, user: User = Depends(get_current_user)):
    result = engine.soil_health(payload.model_dump()); return save_prediction(db, user.id, "soil_health", payload.model_dump(), result, result["health_score"] / 100)

@router.post("/irrigation-recommendations", status_code=status.HTTP_201_CREATED)
def recommend_irrigation(payload: IrrigationInput, db: DbSession, user: User = Depends(get_current_user)):
    result = engine.irrigation_recommendation(payload.model_dump()); return save_prediction(db, user.id, "irrigation", payload.model_dump(), result)

@router.post("/market-price-predictions", status_code=status.HTTP_201_CREATED)
def predict_market(payload: MarketInput, db: DbSession, user: User = Depends(get_current_user)):
    result = engine.market_prediction(payload.model_dump()); return save_prediction(db, user.id, "market_price", payload.model_dump(), result)

@router.post("/weather")
async def weather(payload: WeatherRequest, db: DbSession, user: User = Depends(get_current_user)):
    try: data = await fetch_weather(payload.city, payload.country_code)
    except ValueError as exc: raise HTTPException(status_code=503, detail=str(exc))
    except Exception: raise HTTPException(status_code=502, detail="Weather provider did not return a valid response")
    data["advice"] = weather_advice(data); db.add(WeatherLog(user_id=user.id, location=data["location"], observed_at=datetime.now(UTC), data=data)); db.commit(); return data

@router.post("/disease-detections", status_code=status.HTTP_201_CREATED)
async def detect_disease(db: DbSession, image: UploadFile = File(...), crop: str | None = Form(default=None), user: User = Depends(get_current_user)):
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}: raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, or WebP leaf image")
    contents = await image.read()
    if len(contents) > settings.max_upload_size_mb * 1024 * 1024: raise HTTPException(status_code=413, detail="Image exceeds the configured upload limit")
    extension = Path(image.filename or "leaf.jpg").suffix.lower() or ".jpg"; folder = Path(settings.uploads_dir) / "disease"; folder.mkdir(parents=True, exist_ok=True); path = folder / f"{uuid.uuid4()}{extension}"; path.write_bytes(contents)
    try: result = analyse_leaf(path)
    except ValueError as exc: path.unlink(missing_ok=True); raise HTTPException(status_code=422, detail=str(exc))
    record = DiseaseDetection(user_id=user.id, image_path=str(path), crop=crop, disease_name=result["disease_name"], confidence=result["confidence"], treatment=result); db.add(record)
    if result["disease_name"] != "No visible disease pattern": db.add(Notification(user_id=user.id, category="disease", title=result["disease_name"], message="A leaf scan needs your attention."))
    db.commit(); return {"id": record.id, "image_path": str(path), **result}

@router.post("/chat")
def chat(payload: ChatRequest, db: DbSession, user: User = Depends(get_current_user)):
    history = list(db.scalars(select(ChatMessage).where(ChatMessage.user_id == user.id).order_by(ChatMessage.created_at.desc()).limit(10)))
    context = [{"role": item.role, "content": item.content} for item in reversed(history)]
    db.add(ChatMessage(user_id=user.id, role="user", content=payload.message)); response = chatbot_answer(payload.message, context); db.add(ChatMessage(user_id=user.id, role="assistant", content=response)); db.commit(); return {"answer": response}

@router.get("/chat/history")
def chat_history(db: DbSession, user: User = Depends(get_current_user)):
    messages = list(db.scalars(select(ChatMessage).where(ChatMessage.user_id == user.id).order_by(ChatMessage.created_at.desc()).limit(50))); return [{"role": message.role, "content": message.content, "created_at": message.created_at.isoformat()} for message in reversed(messages)]

@router.post("/reports/{report_type}", status_code=status.HTTP_201_CREATED)
def create_report(report_type: str, db: DbSession, user: User = Depends(get_current_user)):
    if report_type not in {"pdf", "xlsx", "csv"}: raise HTTPException(status_code=400, detail="Report type must be pdf, xlsx, or csv")
    records = list(db.scalars(select(Prediction).where(Prediction.user_id == user.id).order_by(Prediction.created_at.desc()).limit(200))); rows = [{"created_at": record.created_at.isoformat(), "type": record.prediction_type, "confidence": record.confidence, "result": record.result_data} for record in records]
    path = Path(settings.uploads_dir) / "reports" / f"farm-report-{user.id}-{uuid.uuid4()}.{report_type}"; build_report(report_type, path, "AgriSense Farm Intelligence Report", rows or [{"message": "No prediction records available for this reporting period."}]); report = Report(user_id=user.id, report_type=report_type, file_path=str(path), parameters={"prediction_count": len(rows)}); db.add(report); db.commit(); db.refresh(report); return {"id": report.id, "download_url": f"/api/v1/reports/{report.id}/download"}

@router.get("/reports/{report_id}/download")
def download_report(report_id: int, db: DbSession, user: User = Depends(get_current_user)):
    report = db.get(Report, report_id)
    if not report or report.user_id != user.id: raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(report.file_path, filename=Path(report.file_path).name)

@router.get("/admin/users")
def admin_users(db: DbSession, _: User = Depends(require_admin)):
    users = list(db.scalars(select(User).order_by(User.created_at.desc()).limit(200))); return [{"id": user.id, "name": user.full_name, "email": user.email, "role": user.role.value, "active": user.is_active, "created_at": user.created_at.isoformat()} for user in users]

@router.patch("/admin/users/{user_id}/status")
def set_user_status(user_id: int, active: bool, db: DbSession, _: User = Depends(require_admin)):
    target = db.get(User, user_id)
    if not target: raise HTTPException(status_code=404, detail="User not found")
    target.is_active = active; db.commit(); return {"id": target.id, "is_active": target.is_active}

@router.get("/admin/analytics")
def admin_analytics(db: DbSession, _: User = Depends(require_admin)):
    return {"users": db.scalar(select(func.count(User.id))), "predictions": db.scalar(select(func.count(Prediction.id))), "datasets": db.scalar(select(func.count(Dataset.id))), "disease_detections": db.scalar(select(func.count(DiseaseDetection.id)))}

@router.post("/admin/datasets", status_code=status.HTTP_201_CREATED)
async def upload_dataset(db: DbSession, name: str = Form(...), domain: str = Form(...), file: UploadFile = File(...), admin: User = Depends(require_admin)):
    if not (file.filename or "").lower().endswith(".csv"): raise HTTPException(status_code=415, detail="Only CSV datasets are supported")
    existing = db.scalar(select(Dataset).where(Dataset.name == name))
    if existing: raise HTTPException(status_code=409, detail="A dataset with this name already exists")
    path = Path(settings.uploads_dir) / "datasets" / f"{uuid.uuid4()}.csv"; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as output: shutil.copyfileobj(file.file, output)
    try:
        import pandas as pd
        frame = pd.read_csv(path).drop_duplicates(); frame.to_csv(path, index=False)
    except Exception:
        path.unlink(missing_ok=True); raise HTTPException(status_code=422, detail="The uploaded file is not a readable CSV dataset")
    dataset = Dataset(uploaded_by=admin.id, name=name, domain=domain, file_path=str(path), row_count=len(frame), metadata_json={"columns": frame.columns.tolist(), "missing_values": frame.isna().sum().to_dict()}); db.add(dataset); db.commit(); db.refresh(dataset)
    return {"id": dataset.id, "rows": dataset.row_count, "columns": dataset.metadata_json["columns"]}

@router.post("/admin/datasets/{dataset_id}/train", status_code=status.HTTP_201_CREATED)
def train_dataset(dataset_id: int, target_column: str, db: DbSession, admin: User = Depends(require_admin)):
    dataset = db.get(Dataset, dataset_id)
    if not dataset: raise HTTPException(status_code=404, detail="Dataset not found")
    artifact = Path(settings.model_dir) / f"{dataset.domain}-{uuid.uuid4()}.joblib"
    try: outcome = train_regressor(dataset.file_path, target_column, str(artifact))
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc))
    except Exception: raise HTTPException(status_code=422, detail="Dataset could not be trained; ensure it has enough valid rows and a numeric target")
    for old in db.scalars(select(ModelVersion).where(ModelVersion.model_type == dataset.domain)): old.is_active = False
    version = ModelVersion(dataset_id=dataset.id, model_type=dataset.domain, version=str(uuid.uuid4())[:8], artifact_path=str(artifact), metrics=outcome["metrics"], is_active=True); db.add(version); db.commit(); db.refresh(version)
    return {"id": version.id, "version": version.version, "metrics": version.metrics, "rows": outcome["rows"]}
