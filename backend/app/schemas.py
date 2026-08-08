from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.models import Role


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=32, max_length=128)
    password: str = Field(min_length=8, max_length=128)


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: Role
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class CropInput(BaseModel):
    state: str = Field(min_length=2, max_length=80); district: str = Field(min_length=2, max_length=80); soil_type: str
    nitrogen: float = Field(ge=0, le=300); phosphorus: float = Field(ge=0, le=200); potassium: float = Field(ge=0, le=300)
    temperature: float = Field(ge=-10, le=60); humidity: float = Field(ge=0, le=100); rainfall: float = Field(ge=0, le=2000); ph: float = Field(ge=0, le=14)
class FertilizerInput(BaseModel):
    crop: str; nitrogen: float = Field(ge=0, le=300); phosphorus: float = Field(ge=0, le=200); potassium: float = Field(ge=0, le=300); ph: float = Field(ge=0, le=14); moisture: float = Field(ge=0, le=100)
class YieldInput(BaseModel):
    crop: str; area_hectares: float = Field(gt=0, le=100000); rainfall: float = Field(ge=0, le=3000); temperature: float = Field(ge=-10, le=60); fertilizer_kg: float = Field(ge=0, le=2000); soil_type: str; historical_yield_tonnes_per_hectare: float = Field(gt=0, le=100)
class SoilInput(BaseModel):
    nitrogen: float = Field(ge=0, le=300); phosphorus: float = Field(ge=0, le=200); potassium: float = Field(ge=0, le=300); organic_carbon: float = Field(ge=0, le=20); moisture: float = Field(ge=0, le=100); ph: float = Field(ge=0, le=14)
class IrrigationInput(BaseModel):
    crop: str; soil_moisture: float = Field(ge=0, le=100); temperature: float = Field(ge=-10, le=60); humidity: float = Field(ge=0, le=100); rainfall_forecast_mm: float = Field(ge=0, le=1000); area_hectares: float = Field(gt=0, le=100000)
class MarketInput(BaseModel):
    crop: str; current_price: float = Field(gt=0); historical_prices: list[float] = Field(min_length=3, max_length=365); days_ahead: int = Field(default=7, ge=1, le=90)
class WeatherRequest(BaseModel):
    city: str = Field(min_length=2, max_length=100); country_code: str = Field(default="IN", min_length=2, max_length=2)
class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=3000)
