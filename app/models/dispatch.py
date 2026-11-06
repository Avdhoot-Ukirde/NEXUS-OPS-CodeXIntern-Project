from datetime import datetime, date
from app.extensions import db

class QualityCertification(db.Model):
    __tablename__ = "quality_certifications"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_serial = db.Column(db.String(64), nullable=False)
    certificate_number = db.Column(db.String(64), unique=True, nullable=False)  # 'QC-CERT-2026-901'
    inspector = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(32), nullable=False, default="Passed")  # 'Passed', 'Conditional', 'Failed'
    
    # Critical hardware QA tests
    hipot_test_passed = db.Column(db.Boolean, nullable=False, default=True)  # Dielectric withstand
    esd_protection_passed = db.Column(db.Boolean, nullable=False, default=True)  # ESD strike test
    thermal_stress_passed = db.Column(db.Boolean, nullable=False, default=True)  # Burn-in test chamber
    compliance_standards = db.Column(db.String(128), nullable=False, default="CE, FCC Part 15 Class A, RoHS")
    
    calibration_data = db.Column(db.Text, nullable=True)  # e.g., "IMU offset: 0.002g, ADC ref: 3.3001V"
    sign_off_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "unit_serial": self.unit_serial,
            "certificate_number": self.certificate_number,
            "inspector": self.inspector,
            "status": self.status,
            "hipot_test_passed": self.hipot_test_passed,
            "esd_protection_passed": self.esd_protection_passed,
            "thermal_stress_passed": self.thermal_stress_passed,
            "compliance_standards": self.compliance_standards,
            "calibration_data": self.calibration_data,
            "sign_off_date": self.sign_off_date.isoformat() if self.sign_off_date else None,
            "notes": self.notes,
        }

class PackagingItem(db.Model):
    __tablename__ = "packaging_items"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    item_name = db.Column(db.String(128), nullable=False)  # 'Anti-Static ESD Bag Sealed', '12V Power Brick & AC Cable', 'User Manual & QR Card', 'Mounting Brackets & Screws'
    category = db.Column(db.String(64), nullable=False, default="Accessory")  # 'Primary Enclosure', 'Accessory', 'Documentation', 'Label'
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    checked_by = db.Column(db.String(64), nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "item_name": self.item_name,
            "category": self.category,
            "is_verified": self.is_verified,
            "checked_by": self.checked_by,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
        }

class ShipmentRecord(db.Model):
    __tablename__ = "shipment_records"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_serial = db.Column(db.String(64), nullable=False)
    destination_client = db.Column(db.String(128), nullable=False)
    destination_address = db.Column(db.String(256), nullable=False)
    carrier = db.Column(db.String(64), nullable=False, default="DHL Express")  # 'DHL Express', 'FedEx Priority', 'UPS Freight'
    tracking_number = db.Column(db.String(64), nullable=False)
    ship_date = db.Column(db.Date, nullable=True)
    estimated_delivery = db.Column(db.Date, nullable=True)
    delivery_status = db.Column(db.String(32), nullable=False, default="Ready to Ship")  # 'Ready to Ship', 'Picked Up', 'In Transit', 'Out for Delivery', 'Delivered'
    customs_declaration = db.Column(db.String(64), nullable=True)  # Harmonized Tariff code / invoice #
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "unit_serial": self.unit_serial,
            "destination_client": self.destination_client,
            "destination_address": self.destination_address,
            "carrier": self.carrier,
            "tracking_number": self.tracking_number,
            "ship_date": self.ship_date.isoformat() if self.ship_date else None,
            "estimated_delivery": self.estimated_delivery.isoformat() if self.estimated_delivery else None,
            "delivery_status": self.delivery_status,
            "customs_declaration": self.customs_declaration,
        }

