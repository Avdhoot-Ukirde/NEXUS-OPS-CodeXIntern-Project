from datetime import datetime, date
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.project import Project
from app.models.dispatch import QualityCertification, PackagingItem, ShipmentRecord
from app.schemas.project_schemas import QualityCertCreateSchema, ShipmentCreateSchema
from app.services.audit_service import log_activity

api_dispatch_bp = Blueprint("api_dispatch", __name__, url_prefix="/api/v1")

@api_dispatch_bp.route("/projects/<int:project_id>/dispatch", methods=["GET"])
def get_dispatch_data(project_id):
    project = Project.query.get_or_404(project_id)
    certs = project.qa_certs.order_by(QualityCertification.sign_off_date.desc()).all()
    packaging = project.packaging_items.order_by(PackagingItem.id.asc()).all()
    shipments = project.shipments.order_by(ShipmentRecord.created_at.desc()).all()

    verified_packaging = len([p for p in packaging if p.is_verified])
    total_packaging = len(packaging)
    packaging_complete = (verified_packaging == total_packaging) if total_packaging > 0 else False

    return jsonify({
        "certifications": [c.to_dict() for c in certs],
        "packaging_items": [p.to_dict() for p in packaging],
        "shipments": [s.to_dict() for s in shipments],
        "metrics": {
            "packaging_verified": verified_packaging,
            "packaging_total": total_packaging,
            "packaging_complete": packaging_complete,
            "qa_passed": len([c for c in certs if c.status == "Passed"]),
            "shipments_count": len(shipments),
        }
    })

@api_dispatch_bp.route("/projects/<int:project_id>/qa-cert", methods=["POST"])
def issue_qa_cert(project_id):
    project = Project.query.get_or_404(project_id)
    try:
        data = request.get_json() or {}
        schema = QualityCertCreateSchema(**data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    existing = QualityCertification.query.filter_by(certificate_number=schema.certificate_number).first()
    if existing:
        return jsonify({"error": f"Certificate '{schema.certificate_number}' already exists."}), 409

    cert = QualityCertification(
        project_id=project.id,
        unit_serial=schema.unit_serial,
        certificate_number=schema.certificate_number,
        inspector=schema.inspector,
        status=schema.status,
        hipot_test_passed=schema.hipot_test_passed,
        esd_protection_passed=schema.esd_protection_passed,
        thermal_stress_passed=schema.thermal_stress_passed,
        compliance_standards=schema.compliance_standards,
        calibration_data=schema.calibration_data,
        notes=schema.notes
    )
    db.session.add(cert)
    db.session.commit()

    log_activity(
        project_id=project.id,
        stage="Dispatch",
        action="QA_CERTIFIED",
        description=f"Unit {cert.unit_serial} passed final QA certification ({cert.certificate_number}) by {cert.inspector}.",
        performed_by=cert.inspector
    )

    return jsonify(cert.to_dict()), 201

@api_dispatch_bp.route("/packaging-items/<int:item_id>/toggle", methods=["PUT"])
def toggle_packaging_item(item_id):
    item = PackagingItem.query.get_or_404(item_id)
    data = request.get_json() or {}
    checked_by = data.get("checked_by", "QA Operations Lead")

    item.is_verified = not item.is_verified
    if item.is_verified:
        item.checked_by = checked_by
        item.verified_at = datetime.utcnow()
    else:
        item.checked_by = None
        item.verified_at = None

    db.session.commit()

    status_str = "Verified" if item.is_verified else "Unchecked"
    log_activity(
        project_id=item.project_id,
        stage="Dispatch",
        action="PACKAGING_CHECK",
        description=f"Packaging item '{item.item_name}' marked as {status_str}.",
        performed_by=checked_by
    )

    return jsonify(item.to_dict())

@api_dispatch_bp.route("/projects/<int:project_id>/shipments", methods=["POST"])
def create_shipment(project_id):
    project = Project.query.get_or_404(project_id)
    try:
        data = request.get_json() or {}
        schema = ShipmentCreateSchema(**data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    ship_dt = None
    est_dt = None
    if schema.ship_date:
        try:
            ship_dt = datetime.strptime(schema.ship_date, "%Y-%m-%d").date()
        except ValueError:
            pass
    if schema.estimated_delivery:
        try:
            est_dt = datetime.strptime(schema.estimated_delivery, "%Y-%m-%d").date()
        except ValueError:
            pass

    shipment = ShipmentRecord(
        project_id=project.id,
        unit_serial=schema.unit_serial,
        destination_client=schema.destination_client,
        destination_address=schema.destination_address,
        carrier=schema.carrier,
        tracking_number=schema.tracking_number,
        ship_date=ship_dt or date.today(),
        estimated_delivery=est_dt,
        customs_declaration=schema.customs_declaration or "HS-8479.50 (Robotic / Electronic Systems)",
        delivery_status="In Transit"
    )
    db.session.add(shipment)
    db.session.commit()

    log_activity(
        project_id=project.id,
        stage="Dispatch",
        action="SHIPMENT_DISPATCHED",
        description=f"Unit {shipment.unit_serial} dispatched to {shipment.destination_client} via {shipment.carrier} ({shipment.tracking_number}).",
        performed_by="Logistics Coordinator"
    )

    return jsonify(shipment.to_dict()), 201

