from datetime import datetime, date
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.project import Project
from app.models.procurement import BOMItem
from app.schemas.project_schemas import BOMItemCreateSchema, BOMItemUpdateSchema
from app.services.audit_service import log_activity

api_procurement_bp = Blueprint("api_procurement", __name__, url_prefix="/api/v1")

@api_procurement_bp.route("/projects/<int:project_id>/bom", methods=["GET"])
def get_bom(project_id):
    project = Project.query.get_or_404(project_id)
    items = project.bom_items.order_by(BOMItem.category.asc(), BOMItem.part_number.asc()).all()
    
    total_parts = len(items)
    delivered = len([i for i in items if i.status == "Delivered"])
    total_cost = sum(i.total_cost for i in items)
    readiness_pct = (delivered / total_parts * 100) if total_parts > 0 else 0.0
    
    return jsonify({
        "items": [i.to_dict() for i in items],
        "metrics": {
            "total_line_items": total_parts,
            "delivered_count": delivered,
            "readiness_pct": round(readiness_pct, 1),
            "total_bom_cost": round(total_cost, 2),
            "high_risk_items": len([i for i in items if i.risk_level == "High"])
        }
    })

@api_procurement_bp.route("/projects/<int:project_id>/bom", methods=["POST"])
def add_bom_item(project_id):
    project = Project.query.get_or_404(project_id)
    try:
        data = request.get_json() or {}
        schema = BOMItemCreateSchema(**data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    item = BOMItem(
        project_id=project.id,
        part_number=schema.part_number,
        manufacturer_pn=schema.manufacturer_pn,
        description=schema.description,
        category=schema.category,
        subsystem=schema.subsystem,
        quantity_required=schema.quantity_required,
        quantity_received=0,
        unit_cost=schema.unit_cost,
        supplier_name=schema.supplier_name,
        lead_time_days=schema.lead_time_days,
        status=schema.status,
        po_reference=schema.po_reference
    )
    item.calculate_cost()
    db.session.add(item)
    
    # Update project actual cost
    project.actual_cost += item.total_cost
    db.session.commit()

    log_activity(
        project_id=project.id,
        stage="Purchase",
        action="BOM_ITEM_ADDED",
        description=f"Added component {item.manufacturer_pn} ({item.quantity_required}x) from {item.supplier_name}.",
        performed_by="Procurement Specialist"
    )

    return jsonify(item.to_dict()), 201

@api_procurement_bp.route("/bom-items/<int:item_id>", methods=["PUT"])
def update_bom_item(item_id):
    item = BOMItem.query.get_or_404(item_id)
    try:
        data = request.get_json() or {}
        schema = BOMItemUpdateSchema(**data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    if schema.quantity_received is not None:
        item.quantity_received = schema.quantity_received
        if item.quantity_received >= item.quantity_required:
            item.status = "Delivered"
            item.actual_delivery = date.today()
    if schema.status is not None:
        item.status = schema.status
        if schema.status == "Delivered":
            item.quantity_received = item.quantity_required
            item.actual_delivery = date.today()
    if schema.tracking_number is not None:
        item.tracking_number = schema.tracking_number
    if schema.lead_time_days is not None:
        item.lead_time_days = schema.lead_time_days

    item.calculate_cost()
    db.session.commit()

    log_activity(
        project_id=item.project_id,
        stage="Purchase",
        action="BOM_STATUS_UPDATED",
        description=f"Component {item.manufacturer_pn} status changed to '{item.status}' ({item.quantity_received}/{item.quantity_required} received).",
        performed_by="Procurement Specialist"
    )

    return jsonify(item.to_dict())

@api_procurement_bp.route("/bom-items/<int:item_id>", methods=["DELETE"])
def delete_bom_item(item_id):
    item = BOMItem.query.get_or_404(item_id)
    project_id = item.project_id
    part = item.manufacturer_pn
    
    # Adjust cost
    project = Project.query.get(project_id)
    if project:
        project.actual_cost = max(0.0, project.actual_cost - item.total_cost)

    db.session.delete(item)
    db.session.commit()

    log_activity(
        project_id=project_id,
        stage="Purchase",
        action="BOM_ITEM_REMOVED",
        description=f"Component {part} removed from Bill of Materials.",
        performed_by="Procurement Specialist"
    )

    return jsonify({"message": f"BOM item {part} removed successfully."})

