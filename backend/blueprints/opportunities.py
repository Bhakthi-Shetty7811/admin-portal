import os
import jwt
from functools import wraps
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, g
from models import db, Admin, Opportunity

opp_bp = Blueprint("opportunities", __name__, url_prefix="/api")


# ─── Auth middleware ─────────────────────────────────────────────────────────

def require_auth(f):
    """
    Decorator: reads JWT from the Authorization header,
    verifies it, and sets g.current_admin for the route to use.

    Frontend should send:  Authorization: Bearer <token>
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authentication required."}), 401

        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Session expired. Please log in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token."}), 401

        admin = Admin.query.get(payload["sub"])
        if not admin:
            return jsonify({"error": "Admin account not found."}), 401

        g.current_admin = admin
        return f(*args, **kwargs)

    return decorated


# ─── US-2.1 + US-2.3  list all opportunities for logged-in admin ─────────────

@opp_bp.route("/opportunities", methods=["GET"])
@require_auth
def list_opportunities():
    """Returns only the opportunities belonging to the logged-in admin."""
    opps = (
        Opportunity.query
        .filter_by(admin_id=g.current_admin.id)
        .order_by(Opportunity.created_at.desc())
        .all()
    )
    return jsonify([o.to_dict() for o in opps]), 200


# ─── US-2.2  create a new opportunity ────────────────────────────────────────

@opp_bp.route("/opportunities", methods=["POST"])
@require_auth
def create_opportunity():
    data = request.get_json(silent=True) or {}

    # Required fields
    required = ["name", "duration", "start_date", "description", "skills", "category", "future_opportunities"]
    for field in required:
        if not (data.get(field) or "").strip():
            return jsonify({"error": f"'{field}' is required."}), 400

    # Optional: max_applicants (must be a positive integer if provided)
    max_app = data.get("max_applicants")
    if max_app is not None:
        try:
            max_app = int(max_app)
            if max_app <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({"error": "max_applicants must be a positive integer."}), 400

    opp = Opportunity(
        admin_id=g.current_admin.id,
        name=data["name"].strip(),
        duration=data["duration"].strip(),
        start_date=data["start_date"].strip(),
        description=data["description"].strip(),
        skills=data["skills"].strip(),
        category=data["category"].strip(),
        future_opportunities=data["future_opportunities"].strip(),
        max_applicants=max_app,
    )
    db.session.add(opp)
    db.session.commit()

    return jsonify(opp.to_dict()), 201


# ─── US-2.4  get single opportunity (for details modal) ──────────────────────

@opp_bp.route("/opportunities/<int:opp_id>", methods=["GET"])
@require_auth
def get_opportunity(opp_id):
    opp = Opportunity.query.get_or_404(opp_id)

    # Ownership check: admins can only read their own opportunities
    if opp.admin_id != g.current_admin.id:
        return jsonify({"error": "Not found."}), 404

    return jsonify(opp.to_dict()), 200


# ─── US-2.5  edit an opportunity ─────────────────────────────────────────────

@opp_bp.route("/opportunities/<int:opp_id>", methods=["PUT"])
@require_auth
def update_opportunity(opp_id):
    opp = Opportunity.query.get_or_404(opp_id)

    # Ownership check
    if opp.admin_id != g.current_admin.id:
        return jsonify({"error": "Not found."}), 404

    data = request.get_json(silent=True) or {}

    # Only update fields that are present in the request body
    updatable = ["name", "duration", "start_date", "description", "skills", "category", "future_opportunities"]
    for field in updatable:
        if field in data:
            value = (data[field] or "").strip()
            if not value:
                return jsonify({"error": f"'{field}' cannot be empty."}), 400
            setattr(opp, field, value)

    if "max_applicants" in data:
        max_app = data["max_applicants"]
        if max_app is not None:
            try:
                max_app = int(max_app)
                if max_app <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                return jsonify({"error": "max_applicants must be a positive integer."}), 400
        opp.max_applicants = max_app

    db.session.commit()
    return jsonify(opp.to_dict()), 200


# ─── US-2.6  delete an opportunity ───────────────────────────────────────────

@opp_bp.route("/opportunities/<int:opp_id>", methods=["DELETE"])
@require_auth
def delete_opportunity(opp_id):
    opp = Opportunity.query.get_or_404(opp_id)

    # Ownership check: only the creator can delete
    if opp.admin_id != g.current_admin.id:
        return jsonify({"error": "Not found."}), 404

    db.session.delete(opp)
    db.session.commit()

    return jsonify({"message": "Opportunity deleted."}), 200