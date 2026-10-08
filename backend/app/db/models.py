"""All persisted tables for AgriSense AI."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def uid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), default="Farmer")
    role: Mapped[str] = mapped_column(String(20), default="farmer")  # farmer|expert|admin
    language: Mapped[str] = mapped_column(String(8), default="en")
    state: Mapped[str] = mapped_column(String(64), default="Telangana")
    district: Mapped[str] = mapped_column(String(64), default="")
    lat: Mapped[float] = mapped_column(Float, default=17.385)
    lon: Mapped[float] = mapped_column(Float, default=78.4867)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class OtpRequest(Base, TimestampMixin):
    """Audit trail. The live OTP itself lives in Redis with a 5-minute TTL."""
    __tablename__ = "otp_requests"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    phone: Mapped[str] = mapped_column(String(20), index=True)
    channel: Mapped[str] = mapped_column(String(20), default="sms")
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ip: Mapped[str] = mapped_column(String(64), default="")


class Session(Base, TimestampMixin):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    refresh_hash: Mapped[str] = mapped_column(String(128))
    device: Mapped[str] = mapped_column(String(255), default="")
    ip: Mapped[str] = mapped_column(String(64), default="")
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Farm(Base, TimestampMixin):
    __tablename__ = "farms"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120), default="My Farm")
    area_acres: Mapped[float] = mapped_column(Float, default=2.0)
    soil_type: Mapped[str] = mapped_column(String(40), default="black")
    irrigation: Mapped[str] = mapped_column(String(40), default="borewell")
    lat: Mapped[float] = mapped_column(Float, default=17.385)
    lon: Mapped[float] = mapped_column(Float, default=78.4867)
    crops: Mapped[dict] = mapped_column(JSON, default=list)


class CropImage(Base, TimestampMixin):
    __tablename__ = "crop_images"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    path: Mapped[str] = mapped_column(String(255))
    filename: Mapped[str] = mapped_column(String(255), default="")


class DiseaseReport(Base, TimestampMixin):
    __tablename__ = "disease_reports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    image_id: Mapped[str] = mapped_column(String(36), default="")
    crop: Mapped[str] = mapped_column(String(64), default="unknown")
    disease: Mapped[str] = mapped_column(String(120), default="unknown")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    severity: Mapped[str] = mapped_column(String(20), default="low")
    model: Mapped[str] = mapped_column(String(64), default="")
    advisory: Mapped[dict] = mapped_column(JSON, default=dict)


class WeatherCache(Base):
    __tablename__ = "weather_cache"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class GovernmentScheme(Base):
    __tablename__ = "government_schemes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(40), default="income")
    state: Mapped[str] = mapped_column(String(64), default="All India")
    benefit: Mapped[str] = mapped_column(Text, default="")
    eligibility: Mapped[str] = mapped_column(Text, default="")
    documents: Mapped[dict] = mapped_column(JSON, default=list)
    how_to_apply: Mapped[str] = mapped_column(Text, default="")
    link: Mapped[str] = mapped_column(String(255), default="")
    # Freshness, so the UI can show how current this entry is instead of
    # implying every scheme detail is live.
    last_verified: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    link_status: Mapped[str | None] = mapped_column(String(24), nullable=True)  # ok|unreachable|unchecked
    source_note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class ChatMessage(Base, TimestampMixin):
    __tablename__ = "chat_history"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(16))  # user|assistant
    content: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(8), default="en")
    sources: Mapped[dict] = mapped_column(JSON, default=list)
    # {"kind": "image"|"file", "url": ..., "name": ..., "summary": ...}
    attachment: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    engine: Mapped[str | None] = mapped_column(String(48), nullable=True)


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text, default="")
    kind: Mapped[str] = mapped_column(String(24), default="info")  # info|weather|disease|scheme
    read: Mapped[bool] = mapped_column(Boolean, default=False)


class SoilReport(Base, TimestampMixin):
    __tablename__ = "soil_reports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    crop: Mapped[str] = mapped_column(String(64), default="rice")
    n: Mapped[float] = mapped_column(Float, default=0)
    p: Mapped[float] = mapped_column(Float, default=0)
    k: Mapped[float] = mapped_column(Float, default=0)
    ph: Mapped[float] = mapped_column(Float, default=7.0)
    oc: Mapped[float] = mapped_column(Float, default=0.5)
    moisture: Mapped[float] = mapped_column(Float, default=20.0)
    score: Mapped[float] = mapped_column(Float, default=0)
    recommendation: Mapped[dict] = mapped_column(JSON, default=dict)


class YieldPrediction(Base, TimestampMixin):
    __tablename__ = "yield_predictions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    crop: Mapped[str] = mapped_column(String(64))
    area_acres: Mapped[float] = mapped_column(Float, default=1)
    predicted_quintals: Mapped[float] = mapped_column(Float, default=0)
    confidence: Mapped[float] = mapped_column(Float, default=0)
    factors: Mapped[dict] = mapped_column(JSON, default=dict)


class ActivityLog(Base, TimestampMixin):
    __tablename__ = "activity_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(String(36), default="")
    action: Mapped[str] = mapped_column(String(64))
    meta: Mapped[dict] = mapped_column(JSON, default=dict)


class Feedback(Base, TimestampMixin):
    __tablename__ = "feedback"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(String(36), default="")
    rating: Mapped[int] = mapped_column(Integer, default=5)
    message: Mapped[str] = mapped_column(Text, default="")


class IoTDevice(Base, TimestampMixin):
    __tablename__ = "iot_devices"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(String(36), index=True, default="")
    device_key: Mapped[str] = mapped_column(String(64), unique=True)
    label: Mapped[str] = mapped_column(String(80), default="Field sensor")
    last_reading: Mapped[dict] = mapped_column(JSON, default=dict)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, default=dict)


class Language(Base):
    __tablename__ = "languages"
    code: Mapped[str] = mapped_column(String(8), primary_key=True)
    label: Mapped[str] = mapped_column(String(40))
    native: Mapped[str] = mapped_column(String(40))
