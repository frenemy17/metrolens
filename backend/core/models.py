import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean, Integer, JSON
from sqlalchemy.orm import relationship

from .database import Base


class Officer(Base):
    __tablename__ = 'officers'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # INSPECTOR, SUPERVISOR, ADMIN
    auth = Column(String, nullable=True)   # Used for custom JWT or mapping to Firebase ID

    inspections = relationship("Inspection", back_populates="officer")


class Inspection(Base):
    __tablename__ = 'inspections'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    officer_id = Column(String(36), ForeignKey('officers.id'), nullable=False)
    status = Column(String, default="DRAFT")
    category = Column(String, nullable=True)
    channel = Column(String, nullable=True)
    verdict = Column(String, nullable=True)
    enforcement_status = Column(String, nullable=True)
    date_created = Column(DateTime, default=datetime.utcnow)

    officer = relationship("Officer", back_populates="inspections")
    evidence_images = relationship("EvidenceImage", back_populates="inspection")
    calibrations = relationship("Calibration", back_populates="inspection")
    measurements = relationship("Measurement", back_populates="inspection")
    rule_evaluations = relationship("RuleEvaluation", back_populates="inspection")
    audit_logs = relationship("AuditLog", back_populates="inspection")


class EvidenceImage(Base):
    __tablename__ = 'evidence_images'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inspection_id = Column(String(36), ForeignKey('inspections.id'), nullable=False)
    image_type = Column(String, nullable=False)  # PRIMARY_PANEL, SIDE, BACK
    storage_path = Column(String, nullable=False)
    gps_lat = Column(Float, nullable=True)
    gps_lng = Column(Float, nullable=True)
    device_session_id = Column(String, nullable=True)
    blur_score = Column(Float, nullable=True)
    glare_score = Column(Float, nullable=True)

    inspection = relationship("Inspection", back_populates="evidence_images")
    measurements = relationship("Measurement", back_populates="image")


class Calibration(Base):
    __tablename__ = 'calibrations'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inspection_id = Column(String(36), ForeignKey('inspections.id'), nullable=False)
    mm_px_scale = Column(Float, nullable=False)
    confidence_flag = Column(String, nullable=True)  # e.g., UNRELIABLE

    inspection = relationship("Inspection", back_populates="calibrations")


class Measurement(Base):
    __tablename__ = 'measurements'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inspection_id = Column(String(36), ForeignKey('inspections.id'), nullable=False)
    image_id = Column(String(36), ForeignKey('evidence_images.id'), nullable=True)
    declaration_type = Column(String, nullable=True)
    printing_method = Column(String, nullable=True)
    text = Column(String, nullable=True)          # From OCR
    height_mm = Column(Float, nullable=True)      # Deterministic
    gps_lat = Column(Float, nullable=True)
    gps_lng = Column(Float, nullable=True)
    device_session_id = Column(String, nullable=True)

    inspection = relationship("Inspection", back_populates="measurements")
    image = relationship("EvidenceImage", back_populates="measurements")


class RuleEvaluation(Base):
    __tablename__ = 'rule_evaluations'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inspection_id = Column(String(36), ForeignKey('inspections.id'), nullable=False)
    rule_id = Column(String, nullable=False)
    status = Column(String, nullable=False)  # PASS, FAIL, CANNOT_DETERMINE, SUSPECTED_NON_STANDARD
    measured_value = Column(String, nullable=True)
    threshold = Column(String, nullable=True)
    uncertainty_used = Column(Float, nullable=True)
    citation = Column(String, nullable=True)
    evidence_link = Column(String, nullable=True)

    inspection = relationship("Inspection", back_populates="rule_evaluations")


class AuditLog(Base):
    __tablename__ = 'audit_log'
    # Append-only
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inspection_id = Column(String(36), ForeignKey('inspections.id'), nullable=False)
    action = Column(String, nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    inspection = relationship("Inspection", back_populates="audit_logs")


class Rulepack(Base):
    __tablename__ = 'rulepacks'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version = Column(String, nullable=False, unique=True)
    effective_from = Column(DateTime, nullable=True)
    payload = Column(JSON, nullable=False)
    status = Column(String, default="DRAFT")  # DRAFT, PUBLISHED

class InspectionRecord(Base):
    __tablename__ = 'inspection_records'
    id = Column(String(36), primary_key=True)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class BatchRecord(Base):
    __tablename__ = 'batch_records'
    id = Column(String(36), primary_key=True)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
