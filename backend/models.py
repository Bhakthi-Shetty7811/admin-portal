from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Admin(db.Model):
    """One row per registered admin account."""
    __tablename__ = "admins"

    id            = db.Column(db.Integer, primary_key=True)
    full_name     = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship: one admin → many opportunities
    opportunities = db.relationship("Opportunity", back_populates="admin", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id":        self.id,
            "full_name": self.full_name,
            "email":     self.email,
        }


class Opportunity(db.Model):
    """One row per opportunity created by an admin."""
    __tablename__ = "opportunities"

    id                  = db.Column(db.Integer, primary_key=True)
    admin_id            = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=False)
    name                = db.Column(db.String(255), nullable=False)
    duration            = db.Column(db.String(100), nullable=False)
    start_date          = db.Column(db.String(50),  nullable=False)   # stored as ISO string "YYYY-MM-DD"
    description         = db.Column(db.Text,        nullable=False)
    skills              = db.Column(db.Text,        nullable=False)   # comma-separated
    category            = db.Column(db.String(100), nullable=False)
    future_opportunities = db.Column(db.Text,       nullable=False)
    max_applicants      = db.Column(db.Integer,     nullable=True)    # optional
    created_at          = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship back to admin
    admin = db.relationship("Admin", back_populates="opportunities")

    def to_dict(self):
        return {
            "id":                    self.id,
            "admin_id":              self.admin_id,
            "name":                  self.name,
            "duration":              self.duration,
            "start_date":            self.start_date,
            "description":           self.description,
            "skills":                [s.strip() for s in self.skills.split(",") if s.strip()],
            "category":              self.category,
            "future_opportunities":  self.future_opportunities,
            "max_applicants":        self.max_applicants,
            "created_at":            self.created_at.isoformat(),
        }


class PasswordResetToken(db.Model):
    """
    One row per active password-reset request.
    Tokens expire after 1 hour and are single-use.
    """
    __tablename__ = "password_reset_tokens"

    id         = db.Column(db.Integer, primary_key=True)
    token      = db.Column(db.String(64), unique=True, nullable=False)
    email      = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used       = db.Column(db.Boolean, default=False)

    def is_expired(self):
        return datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc)