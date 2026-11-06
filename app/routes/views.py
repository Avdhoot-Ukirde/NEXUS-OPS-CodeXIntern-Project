from flask import Blueprint, render_template, abort
from app.models.project import Project
from app.models.assembly import PhysicalUnit

views_bp = Blueprint("views", __name__)

@views_bp.route("/")
def dashboard():
    return render_template("dashboard.html")

@views_bp.route("/projects/<int:project_id>")
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template("project_detail.html", project=project)

@views_bp.route("/units/<int:unit_id>/traveler")
def physical_traveler_sheet(unit_id):
    unit = PhysicalUnit.query.get_or_404(unit_id)
    return render_template("traveler_sheet.html", unit=unit, project=unit.project)

