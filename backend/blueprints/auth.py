import os
import uuid
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta

from flask import Blueprint, request, jsonify
from models import db, Admin, PasswordResetToken

auth_bp = Blueprint("auth", __name__, url_prefix="/api")


# ─── helpers ────────────────────────────────────────────────────────────────

def _make_token(admin_id: int, remember_me: bool) -> str:
    """
    Create a signed JWT for the admin.
    If remember_me is True, the token lasts 30 days.
    Otherwise it expires in 8 hours (effectively session-length).
    """
    expiry = timedelta(days=30) if remember_me else timedelta(hours=8)
    payload = {
        "sub": admin_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + expiry,
    }
    return jwt.encode(payload, os.environ["JWT_SECRET"], algorithm="HS256")


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _check_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ─── US-1.1 sign up ─────────────────────────────────────────────────────────

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}

    full_name = (data.get("full_name") or "").strip()
    email     = (data.get("email")     or "").strip().lower()
    password  = (data.get("password")  or "").strip()
    confirm   = (data.get("confirm_password") or "").strip()

    # --- server-side validation (mirrors frontend rules) ---
    if not full_name:
        return jsonify({"error": "Full name is required."}), 400
    if not email or "@" not in email:
        return jsonify({"error": "A valid email address is required."}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400
    if password != confirm:
        return jsonify({"error": "Passwords do not match."}), 400

    # --- check duplicate email ---
    if Admin.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists."}), 409

    admin = Admin(
        full_name=full_name,
        email=email,
        password_hash=_hash_password(password),
    )
    db.session.add(admin)
    db.session.commit()

    return jsonify({"message": "Account created successfully."}), 201


# ─── US-1.2 login ────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email       = (data.get("email")    or "").strip().lower()
    password    = (data.get("password") or "").strip()
    remember_me = bool(data.get("remember_me", False))

    if not email or not password:
        return jsonify({"error": "Invalid email or password."}), 401

    admin = Admin.query.filter_by(email=email).first()

    # Use the same generic message for missing user AND wrong password.
    # This prevents user enumeration (you can't tell which was wrong).
    if not admin or not _check_password(password, admin.password_hash):
        return jsonify({"error": "Invalid email or password."}), 401

    token = _make_token(admin.id, remember_me)

    return jsonify({
        "token": token,
        "admin": admin.to_dict(),
    }), 200


# ─── US-1.3 forgot password ──────────────────────────────────────────────────

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data  = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    # Always return the same success response (protects privacy).
    # We only do real work if the email exists.
    admin = Admin.query.filter_by(email=email).first()
    if admin:
        # Delete any old unused tokens for this email first
        PasswordResetToken.query.filter_by(email=email, used=False).delete()
        db.session.commit()

        token = PasswordResetToken(
            token=uuid.uuid4().hex,
            email=email,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db.session.add(token)
        db.session.commit()

        # In production you'd email this link.
        # For now, log it so you can see it in the terminal during dev/demo.
        reset_link = f"http://localhost:5000/api/reset-password/{token.token}"
        print(f"\n[DEV] Password reset link for {email}:\n  {reset_link}\n")

    return jsonify({"message": "If this email is registered, a reset link has been sent."}), 200


# ─── (bonus) validate reset token ────────────────────────────────────────────

@auth_bp.route("/reset-password/<token_str>", methods=["GET"])
def validate_reset_token(token_str):
    """
    Used to check if a reset link is still valid.
    The frontend would hit this when the user clicks the reset link.
    """
    record = PasswordResetToken.query.filter_by(token=token_str, used=False).first()

    if not record:
        return jsonify({"error": "Reset link is invalid or has already been used."}), 400
    if record.is_expired():
        return jsonify({"error": "Reset link has expired. Please request a new one."}), 400

    return jsonify({"email": record.email, "valid": True}), 200