from datetime import datetime

from typing import Literal

from pydantic import BaseModel, Field, field_validator


# ---------- auth ----------
class OtpRequestIn(BaseModel):
    phone: str = Field(min_length=10, max_length=15)

    @field_validator("phone")
    @classmethod
    def normalise(cls, v: str) -> str:
        digits = "".join(ch for ch in v if ch.isdigit())
        if len(digits) < 10:
            raise ValueError("phone number must have at least 10 digits")
        return digits[-10:]


class OtpRequestOut(BaseModel):
    request_id: str
    expires_in: int
    resend_after: int
    max_attempts: int
    dev_otp: str | None = None


class OtpVerifyIn(OtpRequestIn):
    otp: str = Field(min_length=4, max_length=8)
    device: str = ""


class UserOut(BaseModel):
    id: str
    phone: str
    name: str
    role: str
    language: str
    state: str
    district: str
    lat: float
    lon: float

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class RefreshIn(BaseModel):
    refresh_token: str


class SessionOut(BaseModel):
    id: str
    device: str
    ip: str
    created_at: datetime
    last_seen: datetime
    revoked: bool

    class Config:
        from_attributes = True


class ProfileIn(BaseModel):
    name: str | None = None
    language: str | None = None
    state: str | None = None
    district: str | None = None
    lat: float | None = None
    lon: float | None = None


# ---------- chat ----------
class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    language: str = "en"


class ChatOut(BaseModel):
    reply: str
    sources: list[str] = []
    engine: str
    language: str = "en"
    cached: bool = False
    attachment: dict | None = None


# ---------- soil / crop / yield ----------
class SoilIn(BaseModel):
    crop: str = Field(default="rice", min_length=2, max_length=40)
    n: float = Field(ge=0, le=1000, description="available N kg/ha")
    p: float = Field(ge=0, le=500, description="available P2O5 kg/ha")
    k: float = Field(ge=0, le=1500, description="available K2O kg/ha")
    ph: float = Field(ge=2, le=11)
    oc: float = Field(default=0.5, ge=0, le=10, description="organic carbon %")
    moisture: float = Field(default=20, ge=0, le=100)
    area_acres: float = Field(default=1, gt=0, le=1000)


class CropRecommendIn(BaseModel):
    n: float = Field(default=250, ge=0, le=1000, description="available N kg/ha")
    p: float = Field(default=25, ge=0, le=500, description="available P2O5 kg/ha")
    k: float = Field(default=250, ge=0, le=1500, description="available K2O kg/ha")
    ph: float = Field(default=6.8, ge=2, le=11)
    rainfall_mm: float = Field(default=700, ge=0, le=6000)
    # Literals, not free strings: a typo used to fall through to a default and
    # produce a confident recommendation for the wrong season.
    season: Literal["kharif", "rabi", "summer", "annual"] = "kharif"
    irrigation: Literal["rainfed", "borewell", "canal", "drip", "sprinkler", "none"] = "borewell"
    soil_type: Literal["black", "red", "loam", "clay", "sandy", "alluvial"] = "black"


class YieldIn(BaseModel):
    crop: str = Field(default="rice", min_length=2, max_length=40)
    area_acres: float = Field(default=1, gt=0, le=1000)
    soil_score: float = Field(default=70, ge=0, le=100)
    rainfall_mm: float = Field(default=700, ge=0, le=6000)
    irrigation: Literal["rainfed", "borewell", "canal", "drip", "sprinkler", "none"] = "borewell"
    disease_pressure: Literal["low", "medium", "high"] = "low"
    fertilizer_applied: bool = True


# ---------- misc ----------
class FeedbackIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    message: str = ""


class IoTReadingIn(BaseModel):
    device_key: str
    soil_moisture: float | None = None
    soil_temp: float | None = None
    humidity: float | None = None
    ph: float | None = None
