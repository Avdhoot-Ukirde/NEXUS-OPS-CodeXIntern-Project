from datetime import datetime, date
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.project import Project, ProjectStage, HealthStatus, PriorityLevel
from app.schemas.project_schemas import ProjectCreateSchema, ProjectUpdateSchema, StageAdvanceSchema
from app.services.stage_gate_service import StageGateService
from app.services.audit_service import log_activity

api_projects_bp = Blueprint("api_projects", __name__, url_prefix="/api/v1/projects")

@api_projects_bp.route("", methods=["GET"])
def list_projects():
    stage_filter = request.args.get("stage")
    health_filter = request.args.get("health")
    priority_filter = request.args.get("priority")
    query_str = request.args.get("q", "").strip().lower()

    query = Project.query
    if stage_filter:
        query = query.filter(Project.current_stage == stage_filter)
    if health_filter:
        query = query.filter(Project.health_status == health_filter)
    if priority_filter:
        query = query.filter(Project.priority == priority_filter)
    if query_str:
        query = query.filter(
            db.or_(
                Project.code.ilike(f"%{query_str}%"),
                Project.name.ilike(f"%{query_str}%"),
                Project.lead_engineer.ilike(f"%{query_str}%")
            )
        )

    projects = query.order_by(Project.updated_at.desc()).all()
    return jsonify([p.to_dict() for p in projects])

@api_projects_bp.route("", methods=["POST"])
def create_project():
    try:
        data = request.get_json() or {}
        schema = ProjectCreateSchema(**data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    existing = Project.query.filter_by(code=schema.code.upper()).first()
    if existing:
        return jsonify({"error": f"Project code '{schema.code.upper()}' already exists."}), 409

    target_dt = None
    if schema.target_date:
        try:
            target_dt = datetime.strptime(schema.target_date, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Expected YYYY-MM-DD"}), 400

    project = Project(
        code=schema.code.upper(),
        name=schema.name,
        description=schema.description,
        lead_engineer=schema.lead_engineer,
        priority=schema.priority,
        target_date=target_dt,
        budget=schema.budget,
        current_stage=ProjectStage.DESIGN.value,
        health_status=HealthStatus.ON_TRACK.value,
    )
    db.session.add(project)
    db.session.commit()

    log_activity(
        project_id=project.id,
        stage="System",
        action="PROJECT_CREATED",
        description=f"Project '{project.name}' ({project.code}) initialized by {project.lead_engineer}.",
        performed_by=project.lead_engineer
    )

    return jsonify(project.to_dict()), 201

@api_projects_bp.route("/<int:project_id>", methods=["GET"])
def get_project(project_id):
    project = Project.query.get_or_404(project_id)
    return jsonify(project.to_dict())

@api_projects_bp.route("/<int:project_id>", methods=["PUT"])
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    try:
        data = request.get_json() or {}
        schema = ProjectUpdateSchema(**data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    if schema.name is not None:
        project.name = schema.name
    if schema.description is not None:
        project.description = schema.description
    if schema.lead_engineer is not None:
        project.lead_engineer = schema.lead_engineer
    if schema.priority is not None:
        project.priority = schema.priority
    if schema.health_status is not None:
        project.health_status = schema.health_status
    if schema.budget is not None:
        project.budget = schema.budget
    if schema.actual_cost is not None:
        project.actual_cost = schema.actual_cost
    if schema.target_date is not None:
        try:
            project.target_date = datetime.strptime(schema.target_date, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid target_date format. Expected YYYY-MM-DD"}), 400

    project.updated_at = datetime.utcnow()
    db.session.commit()

    log_activity(
        project_id=project.id,
        stage=project.current_stage,
        action="PROJECT_UPDATED",
        description="Project metadata updated.",
        performed_by=project.lead_engineer
    )

    return jsonify(project.to_dict())

@api_projects_bp.route("/<int:project_id>", methods=["DELETE"])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    code = project.code
    db.session.delete(project)
    db.session.commit()
    return jsonify({"message": f"Project {code} deleted successfully."})

@api_projects_bp.route("/<int:project_id>/gate-status", methods=["GET"])
def get_gate_status(project_id):
    project = Project.query.get_or_404(project_id)
    eval_result = StageGateService.evaluate_gates(project)
    return jsonify(eval_result)

@api_projects_bp.route("/<int:project_id>/advance-stage", methods=["POST"])
def advance_stage(project_id):
    project = Project.query.get_or_404(project_id)
    try:
        data = request.get_json() or {}
        schema = StageAdvanceSchema(**data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    result = StageGateService.advance_stage(
        project=project,
        target_stage=schema.target_stage,
        override=schema.override_checks,
        override_reason=schema.override_reason,
        performed_by=schema.performed_by
    )

    if not result["success"]:
        return jsonify(result), 400

    project.updated_at = datetime.utcnow()
    db.session.commit()

    log_desc = f"Stage transitioned from '{result['old_stage']}' to '{result['new_stage']}'."
    if result.get("overridden"):
        log_desc += f" (Engineering Override: {schema.override_reason})"

    log_activity(
        project_id=project.id,
        stage=result["new_stage"],
        action="STAGE_TRANSITION",
        description=log_desc,
        performed_by=schema.performed_by,
        details=str(result)
    )

    return jsonify({
        "success": True,
        "project": project.to_dict(),
        "transition": result
    })

@api_projects_bp.route("/<int:project_id>/activity", methods=["GET"])
def get_project_activity(project_id):
    project = Project.query.get_or_404(project_id)
    logs = project.activities.all()
    return jsonify([l.to_dict() for l in logs])

