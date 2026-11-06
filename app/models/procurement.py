from datetime import datetime, date
from app.extensions import db

class BOMItem(db.Model):
    __tablename__ = "bom_items"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    part_number = db.Column(db.String(64), nullable=False)  # Internal part number e.g. 'IPN-RES-0402'
    manufacturer_pn = db.Column(db.String(64), nullable=False)  # MPN e.g. 'STM32H753IIT6'
    description = db.Column(db.String(256), nullable=False)
    category = db.Column(db.String(64), nullable=False)  # 'Microcontroller', 'Passive', 'Power IC', 'Sensor', 'Mechanical', 'Connector'
    subsystem = db.Column(db.String(64), nullable=False, default="General")
    quantity_required = db.Column(db.Integer, nullable=False, default=1)
    quantity_received = db.Column(db.Integer, nullable=False, default=0)
    unit_cost = db.Column(db.Float, nullable=False, default=0.0)
    total_cost = db.Column(db.Float, nullable=False, default=0.0)
    
    supplier_name = db.Column(db.String(128), nullable=False)  # 'Mouser', 'DigiKey', 'LCSC', 'Arrow', 'Custom Machining Ltd'
    lead_time_days = db.Column(db.Integer, nullable=False, default=7)
    status = db.Column(db.String(32), nullable=False, default="Draft")  # 'Draft', 'PO Placed', 'In Transit', 'Delivered', 'Backordered'
    risk_level = db.Column(db.String(32), nullable=False, default="Low")  # 'Low', 'Medium', 'High'
    po_reference = db.Column(db.String(64), nullable=True)
    tracking_number = db.Column(db.String(64), nullable=True)
    expected_delivery = db.Column(db.Date, nullable=True)
    actual_delivery = db.Column(db.Date, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def calculate_cost(self):
        self.total_cost = round((self.quantity_required or 0) * (self.unit_cost or 0.0), 2)
        lead_days = self.lead_time_days if self.lead_time_days is not None else 7
        if lead_days > 28 or self.status == "Backordered":
            self.risk_level = "High"
        elif lead_days > 14:
            self.risk_level = "Medium"
        else:
            self.risk_level = "Low"

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "part_number": self.part_number,
            "manufacturer_pn": self.manufacturer_pn,
            "description": self.description,
            "category": self.category,
            "subsystem": self.subsystem,
            "quantity_required": self.quantity_required,
            "quantity_received": self.quantity_received,
            "unit_cost": self.unit_cost,
            "total_cost": self.total_cost,
            "supplier_name": self.supplier_name,
            "lead_time_days": self.lead_time_days,
            "status": self.status,
            "risk_level": self.risk_level,
            "po_reference": self.po_reference,
            "tracking_number": self.tracking_number,
            "expected_delivery": self.expected_delivery.isoformat() if self.expected_delivery else None,
            "actual_delivery": self.actual_delivery.isoformat() if self.actual_delivery else None,
        }
