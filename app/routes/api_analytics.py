from flask import Blueprint, jsonify
from app.models.project import Project
from app.services.project_service import ProjectService

api_analytics_bp = Blueprint("api_analytics", __name__, url_prefix="/api/v1/analytics")

@api_analytics_bp.route("/dashboard", methods=["GET"])
def get_dashboard_data():
    metrics = ProjectService.get_dashboard_metrics()
    return jsonify(metrics)

@api_analytics_bp.route("/export/<int:project_id>", methods=["GET"])
def export_project_data(project_id):
    project = Project.query.get_or_404(project_id)
    
    full_data = project.to_dict(include_summary=True)
    full_data["design_docs"] = [d.to_dict() for d in project.design_docs.all()]
    full_data["ecos"] = [e.to_dict() for e in project.ecos.all()]
    full_data["bom_items"] = [b.to_dict() for b in project.bom_items.all()]
    full_data["physical_units"] = [u.to_dict(include_steps=True) for u in project.physical_units.all()]
    full_data["firmware_releases"] = [f.to_dict() for f in project.firmware_releases.all()]
    full_data["test_cases"] = [t.to_dict() for t in project.test_cases.all()]
    full_data["qa_certifications"] = [q.to_dict() for q in project.qa_certs.all()]
    full_data["packaging_items"] = [p.to_dict() for p in project.packaging_items.all()]
    full_data["shipments"] = [s.to_dict() for s in project.shipments.all()]
    full_data["audit_history"] = [a.to_dict() for a in project.activities.all()]

    return jsonify(full_data)

