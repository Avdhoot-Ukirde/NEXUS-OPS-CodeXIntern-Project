from datetime import datetime
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.project import Project
from app.models.assembly import PhysicalUnit, AssemblyTravelerStep, AssemblyDefect
from app.schemas.project_schemas import PhysicalUnitCreateSchema, AssemblyStepUpdateSchema, DefectCreateSchema
from app.services.audit_service import log_activity

api_assembly_bp = Blueprint("api_assembly", __name__, url_prefix="/api/v1")

STANDARD_TRAVELER_STEPS = [
    {
        "step_order": 1,
        "name": "SMT Stencil & Pick-and-Place Assembly",
        "criteria": "IPC-A-610 Class 2 compliance. Verify solder paste height and component alignment.",
    },
    {
        "step_order": 2,
        "name": "Automated Optical Inspection (AOI) & Reflow Check",
        "criteria": "Zero solder bridges, tombstoning, or missing passives. X-ray check on BGA/QFN pads.",
    },
    {
        "step_order": 3,
        "name": "Power Rail Voltage & Short-Circuit Verification",
        "criteria": "Verify 3.3V (±2%), 5.0V (±2%), 12V rail without thermal runaway.",
    },
    {
        "step_order": 4,
        "name": "Mechanical Enclosure & Heatsink Integration",
        "criteria": "Torque all M3 chassis screws to 1.8 N·m. Verify thermal pad contact with enclosure.",
    },
    {
        "step_order": 5,
        "name": "Wiring Harness Routing & Strain Relief Test",
        "criteria": "Cable continuity 100%, crimp pull force > 30N, pinout matched to schematic Rev.",
    },
    {
        "step_order": 6,
        "name": "Subsystem Burn-in & Component Validation",
        "criteria": "Continuous 2-hour idle soak test at 45°C ambient. Zero thermal shutdown triggers.",
    }
]

@api_assembly_bp.route("/projects/<int:project_id>/units", methods=["GET"])
def get_units(project_id):
    project = Project.query.get_or_404(project_id)
    units = project.physical_units.order_by(PhysicalUnit.created_at.asc()).all()
    return jsonify([u.to_dict() for u in units])

@api_assembly_bp.route("/projects/<int:project_id>/units", methods=["POST"])
def register_unit(project_id):
    project = Project.query.get_or_404(project_id)
    try:
        data = request.get_json() or {}
        schema = PhysicalUnitCreateSchema(**data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    existing = PhysicalUnit.query.filter_by(serial_number=schema.serial_number).first()
    if existing:
        return jsonify({"error": f"Unit with serial number '{schema.serial_number}' already exists."}), 409

    unit = PhysicalUnit(
        project_id=project.id,
        serial_number=schema.serial_number,
        batch_number=schema.batch_number,
        variant=schema.variant,
        build_stage="SMT Stencil & Pick-and-Place",
        assigned_technician=schema.assigned_technician,
        notes=schema.notes
    )
    db.session.add(unit)
    db.session.flush()

    # Automatically initialize standard manufacturing traveler steps
    for s in STANDARD_TRAVELER_STEPS:
        step = AssemblyTravelerStep(
            unit_id=unit.id,
            step_order=s["step_order"],
            name=s["name"],
            technician=schema.assigned_technician,
            status="Pending",
            inspection_criteria=s["criteria"]
        )
        db.session.add(step)

    db.session.commit()

    log_activity(
        project_id=project.id,
        stage="Assembly",
        action="UNIT_REGISTERED",
        description=f"Physical Unit '{unit.serial_number}' initialized on manufacturing traveler.",
        performed_by=schema.assigned_technician
    )

    return jsonify(unit.to_dict()), 201

@api_assembly_bp.route("/units/<int:unit_id>", methods=["GET"])
def get_unit_detail(unit_id):
    unit = PhysicalUnit.query.get_or_404(unit_id)
    return jsonify(unit.to_dict(include_steps=True))

@api_assembly_bp.route("/assembly-steps/<int:step_id>", methods=["PUT"])
def update_step(step_id):
    step = AssemblyTravelerStep.query.get_or_404(step_id)
    try:
        data = request.get_json() or {}
        schema = AssemblyStepUpdateSchema(**data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    step.status = schema.status
    step.technician = schema.technician
    if schema.measured_values is not None:
        step.measured_values = schema.measured_values
    if schema.notes is not None:
        step.notes = schema.notes
    if schema.status in ["Passed", "Failed", "Rework"]:
        step.completed_at = datetime.utcnow()

    # Update unit overall build stage
    unit = step.unit
    all_steps = unit.traveler_steps.order_by(AssemblyTravelerStep.step_order.asc()).all()
    all_passed = all(s.status == "Passed" for s in all_steps)
    has_failed = any(s.status in ["Failed", "Rework"] for s in all_steps)

    if all_passed:
        unit.build_stage = "Validation Passed"
        unit.completed_at = datetime.utcnow()
    elif has_failed:
        unit.build_stage = "Rework Required"
    else:
        # Find latest in-progress step
        for s in all_steps:
            if s.status != "Passed":
                unit.build_stage = s.name
                break

    db.session.commit()

    log_activity(
        project_id=unit.project_id,
        stage="Assembly",
        action="TRAVELER_STEP_UPDATED",
        description=f"Unit {unit.serial_number} - Step '{step.name}' marked {step.status}.",
        performed_by=schema.technician,
        details=schema.measured_values
    )

    return jsonify(step.to_dict())

@api_assembly_bp.route("/units/<int:unit_id>/defects", methods=["POST"])
def log_defect(unit_id):
    unit = PhysicalUnit.query.get_or_404(unit_id)
    try:
        data = request.get_json() or {}
        schema = DefectCreateSchema(**data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    defect = AssemblyDefect(
        unit_id=unit.id,
        defect_type=schema.defect_type,
        severity=schema.severity,
        description=schema.description,
        logged_by=schema.logged_by,
        disposition=schema.disposition
    )
    unit.build_stage = "Rework Required"
    db.session.add(defect)
    db.session.commit()

    log_activity(
        project_id=unit.project_id,
        stage="Assembly",
        action="DEFECT_LOGGED",
        description=f"Unit {unit.serial_number} logged defect ({defect.severity}): {defect.defect_type}",
        performed_by=schema.logged_by
    )

    return jsonify(defect.to_dict()), 201

@api_assembly_bp.route("/defects/<int:defect_id>", methods=["PUT"])
def resolve_defect(defect_id):
    defect = AssemblyDefect.query.get_or_404(defect_id)
    data = request.get_json() or {}
    disposition = data.get("disposition", "Reworked & Retested")
    
    defect.disposition = disposition
    defect.resolved_at = datetime.utcnow()
    db.session.commit()

    log_activity(
        project_id=defect.unit.project_id,
        stage="Assembly",
        action="DEFECT_RESOLVED",
        description=f"Unit {defect.unit.serial_number} defect '{defect.defect_type}' marked as '{disposition}'.",
        performed_by="Quality Assurance"
    )

    return jsonify(defect.to_dict())

