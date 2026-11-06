from datetime import datetime
import enum
from app.extensions import db

class ProjectStage(str, enum.Enum):
    DESIGN = "Design"
    PURCHASE = "Purchase"
    ASSEMBLY = "Assembly"
    SOFTWARE = "Software"
    DISPATCH = "Dispatch"
    COMPLETED = "Completed"

class HealthStatus(str, enum.Enum):
    ON_TRACK = "On Track"
    AT_RISK = "At Risk"
    BLOCKED = "Blocked"
    DELAYED = "Delayed"

class PriorityLevel(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True, nullable=False, index=True)  # e.g., 'PRJ-AMR-01'
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    lead_engineer = db.Column(db.String(64), nullable=False, default="Lead Systems Engineer")
    current_stage = db.Column(db.String(32), nullable=False, default=ProjectStage.DESIGN.value)
    health_status = db.Column(db.String(32), nullable=False, default=HealthStatus.ON_TRACK.value)
    priority = db.Column(db.String(32), nullable=False, default=PriorityLevel.HIGH.value)
    
    target_date = db.Column(db.Date, nullable=True)
    budget = db.Column(db.Float, nullable=False, default=0.0)
    actual_cost = db.Column(db.Float, nullable=False, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships across 5 stages
    design_docs = db.relationship("DesignDoc", backref="project", cascade="all, delete-orphan", lazy="dynamic")
    ecos = db.relationship("EngineeringChangeOrder", backref="project", cascade="all, delete-orphan", lazy="dynamic")
    bom_items = db.relationship("BOMItem", backref="project", cascade="all, delete-orphan", lazy="dynamic")
    physical_units = db.relationship("PhysicalUnit", backref="project", cascade="all, delete-orphan", lazy="dynamic")
    firmware_releases = db.relationship("FirmwareRelease", backref="project", cascade="all, delete-orphan", lazy="dynamic")
    test_cases = db.relationship("SoftwareTestCase", backref="project", cascade="all, delete-orphan", lazy="dynamic")
    qa_certs = db.relationship("QualityCertification", backref="project", cascade="all, delete-orphan", lazy="dynamic")
    packaging_items = db.relationship("PackagingItem", backref="project", cascade="all, delete-orphan", lazy="dynamic")
    shipments = db.relationship("ShipmentRecord", backref="project", cascade="all, delete-orphan", lazy="dynamic")
    activities = db.relationship("ActivityLog", backref="project", cascade="all, delete-orphan", lazy="dynamic", order_by="ActivityLog.timestamp.desc()")

    def to_dict(self, include_summary=True):
        data = {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "lead_engineer": self.lead_engineer,
            "current_stage": self.current_stage,
            "health_status": self.health_status,
            "priority": self.priority,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "budget": self.budget,
            "actual_cost": self.actual_cost,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_summary:
            data["summary"] = self.compute_summary()
        return data

    def compute_summary(self):
        # Design Summary
        total_docs = self.design_docs.count()
        approved_docs = self.design_docs.filter_by(status="Approved").count()
        open_ecos = self.ecos.filter(EngineeringChangeOrder.status.in_(["Proposed", "In Review"])).count()
        
        # Procurement Summary
        bom_total = self.bom_items.count()
        bom_received = self.bom_items.filter_by(status="Delivered").count()
        bom_spend = sum(item.total_cost for item in self.bom_items.all())
        bom_readiness_pct = round((bom_received / bom_total * 100), 1) if bom_total > 0 else 0.0

        # Assembly Summary
        units_total = self.physical_units.count()
        units_assembled = self.physical_units.filter_by(build_stage="Validation Passed").count()
        
        # Software Summary
        tests_total = self.test_cases.count()
        tests_passed = self.test_cases.filter_by(result="Passed").count()
        fw_releases_count = self.firmware_releases.count()

        # Dispatch Summary
        qa_certified_count = self.qa_certs.filter_by(status="Passed").count()
        packaging_total = self.packaging_items.count()
        packaging_verified = self.packaging_items.filter_by(is_verified=True).count()
        shipments_dispatched = self.shipments.filter(ShipmentRecord.delivery_status != "Pending").count()

        stage_order = [
            ProjectStage.DESIGN.value,
            ProjectStage.PURCHASE.value,
            ProjectStage.ASSEMBLY.value,
            ProjectStage.SOFTWARE.value,
            ProjectStage.DISPATCH.value,
            ProjectStage.COMPLETED.value
        ]
        curr_index = stage_order.index(self.current_stage) if self.current_stage in stage_order else 0
        overall_progress = round((curr_index / 5) * 100, 1)

        return {
            "overall_progress_pct": overall_progress,
            "design": {
                "total_docs": total_docs,
                "approved_docs": approved_docs,
                "open_ecos": open_ecos,
                "ready": approved_docs > 0 and open_ecos == 0
            },
            "procurement": {
                "total_parts": bom_total,
                "received_parts": bom_received,
                "readiness_pct": bom_readiness_pct,
                "bom_spend": round(bom_spend, 2),
                "ready": bom_readiness_pct >= 90.0
            },
            "assembly": {
                "total_units": units_total,
                "completed_units": units_assembled,
                "ready": units_assembled > 0
            },
            "software": {
                "total_tests": tests_total,
                "passed_tests": tests_passed,
                "fw_releases_count": fw_releases_count,
                "test_pass_pct": round((tests_passed / tests_total * 100), 1) if tests_total > 0 else 0.0,
                "ready": tests_total > 0 and tests_passed == tests_total
            },
            "dispatch": {
                "qa_certified_count": qa_certified_count,
                "packaging_total": packaging_total,
                "packaging_verified": packaging_verified,
                "shipments_count": shipments_dispatched,
                "ready": qa_certified_count > 0 and packaging_total > 0 and packaging_verified == packaging_total
            }
        }

from app.models.design import EngineeringChangeOrder
from app.models.dispatch import ShipmentRecord

