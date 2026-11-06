from datetime import datetime
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.project import Project
from app.models.design import DesignDoc, EngineeringChangeOrder
from app.schemas.project_schemas import DesignDocCreateSchema, ECOCreateSchema
from app.services.audit_service import log_activity

api_design_bp = Blueprint("api_design", __name__, url_prefix="/api/v1")

@api_design_bp.route("/projects/<int:project_id>/design-docs", methods=["GET"])
def get_design_docs(project_id):
    project = Project.query.get_or_404(project_id)
    docs = project.design_docs.order_by(DesignDoc.created_at.desc()).all()
    return jsonify([d.to_dict() for d in docs])

@api_design_bp.route("/projects/<int:project_id>/design-docs", methods=["POST"])
def add_design_doc(project_id):
    project = Project.query.get_or_404(project_id)
    try:
        data = request.get_json() or {}
        schema = DesignDocCreateSchema(**data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    doc = DesignDoc(
        project_id=project.id,
        title=schema.title,
        doc_type=schema.doc_type,
        subsystem=schema.subsystem,
        version=schema.version,
        file_url=schema.file_url or f"/uploads/cad/{schema.subsystem.lower().replace(' ', '_')}_{schema.version}.step",
        author=schema.author,
        review_notes=schema.review_notes,
        status="Under Review"
    )
    db.session.add(doc)
    db.session.commit()

    log_activity(
        project_id=project.id,
        stage="Design",
        action="DESIGN_DOC_ADDED",
        description=f"New design document '{doc.title}' ({doc.version}) added for review.",
        performed_by=schema.author
    )

    return jsonify(doc.to_dict()), 201

@api_design_bp.route("/design-docs/<int:doc_id>/approve", methods=["PUT"])
def approve_design_doc(doc_id):
    doc = DesignDoc.query.get_or_404(doc_id)
    data = request.get_json() or {}
    new_status = data.get("status", "Approved")  # 'Approved' or 'Rejected'
    approved_by = data.get("approved_by", "Lead Systems Architect")
    notes = data.get("notes")

    doc.status = new_status
    doc.approved_by = approved_by
    doc.approved_at = datetime.utcnow()
    if notes:
        doc.review_notes = notes

    db.session.commit()

    log_activity(
        project_id=doc.project_id,
        stage="Design",
        action="DESIGN_DOC_REVIEW",
        description=f"Design doc '{doc.title}' {new_status} by {approved_by}.",
        performed_by=approved_by
    )

    return jsonify(doc.to_dict())

@api_design_bp.route("/projects/<int:project_id>/ecos", methods=["GET"])
def get_ecos(project_id):
    project = Project.query.get_or_404(project_id)
    ecos = project.ecos.order_by(EngineeringChangeOrder.created_at.desc()).all()
    return jsonify([e.to_dict() for e in ecos])

@api_design_bp.route("/projects/<int:project_id>/ecos", methods=["POST"])
def create_eco(project_id):
    project = Project.query.get_or_404(project_id)
    try:
        data = request.get_json() or {}
        schema = ECOCreateSchema(**data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    existing = EngineeringChangeOrder.query.filter_by(eco_number=schema.eco_number).first()
    if existing:
        return jsonify({"error": f"ECO number '{schema.eco_number}' already exists."}), 409

    eco = EngineeringChangeOrder(
        project_id=project.id,
        eco_number=schema.eco_number,
        title=schema.title,
        description=schema.description,
        reason=schema.reason,
        severity=schema.severity,
        affected_subsystems=schema.affected_subsystems,
        status="In Review",
        requested_by=schema.requested_by
    )
    db.session.add(eco)
    
    # If critical ECO, flag project health as At Risk
    if schema.severity in ["Critical", "High"]:
        project.health_status = "At Risk"

    db.session.commit()

    log_activity(
        project_id=project.id,
        stage="Design",
        action="ECO_RAISED",
        description=f"ECO '{eco.eco_number}' ({eco.severity}) raised: {eco.title}",
        performed_by=schema.requested_by
    )

    return jsonify(eco.to_dict()), 201

@api_design_bp.route("/ecos/<int:eco_id>/resolve", methods=["PUT"])
def resolve_eco(eco_id):
    eco = EngineeringChangeOrder.query.get_or_404(eco_id)
    data = request.get_json() or {}
    new_status = data.get("status", "Implemented")  # 'Approved', 'Implemented', 'Closed'
    approved_by = data.get("approved_by", "Chief Engineer")

    eco.status = new_status
    eco.approved_by = approved_by
    if new_status in ["Implemented", "Closed"]:
        eco.resolved_at = datetime.utcnow()

    db.session.commit()

    log_activity(
        project_id=eco.project_id,
        stage="Design",
        action="ECO_RESOLVED",
        description=f"ECO '{eco.eco_number}' transitioned to '{new_status}' by {approved_by}.",
        performed_by=approved_by
    )

    return jsonify(eco.to_dict())

