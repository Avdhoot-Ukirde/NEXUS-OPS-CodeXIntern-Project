import unittest
from datetime import date
from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models.project import Project, ProjectStage
from app.models.design import DesignDoc, EngineeringChangeOrder
from app.models.procurement import BOMItem
from app.models.assembly import PhysicalUnit, AssemblyTravelerStep
from app.models.software import SoftwareTestCase, FirmwareRelease
from app.services.stage_gate_service import StageGateService

class TestStageGates(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_design_gate_blocks_without_approved_docs(self):
        project = Project(
            code="PRJ-TEST-01",
            name="Test Drone Controller",
            lead_engineer="Alex Test",
            current_stage=ProjectStage.DESIGN.value
        )
        db.session.add(project)
        db.session.commit()

        # Gate check should block because no CAD docs exist
        eval_result = StageGateService.evaluate_gates(project)
        self.assertFalse(eval_result["can_advance"])
        self.assertTrue(any("No CAD" in b for b in eval_result["blocking_reasons"]))

        # Add unapproved doc
        doc = DesignDoc(
            project_id=project.id,
            title="Main Schematic",
            doc_type="Schematic",
            subsystem="Core",
            author="Alex Test",
            status="Under Review"
        )
        db.session.add(doc)
        db.session.commit()

        eval_result = StageGateService.evaluate_gates(project)
        self.assertFalse(eval_result["can_advance"])
        self.assertTrue(any("sign-off" in b for b in eval_result["blocking_reasons"]))

        # Now approve doc
        doc.status = "Approved"
        db.session.commit()

        eval_result = StageGateService.evaluate_gates(project)
        self.assertTrue(eval_result["can_advance"])

    def test_design_gate_blocks_with_critical_eco(self):
        project = Project(
            code="PRJ-TEST-02",
            name="Test Telemetry Unit",
            lead_engineer="Alex Test",
            current_stage=ProjectStage.DESIGN.value
        )
        db.session.add(project)
        db.session.commit()
        doc = DesignDoc(
            project_id=project.id,
            title="Main Schematic",
            doc_type="Schematic",
            subsystem="Core",
            author="Alex Test",
            status="Approved"
        )
        db.session.add(doc)
        db.session.commit()

        # Add critical ECO
        eco = EngineeringChangeOrder(
            project_id=project.id,
            eco_number="ECO-T-01",
            title="Thermal runaway detected",
            description="High heat",
            reason="Design Flaw",
            severity="Critical",
            affected_subsystems="Core",
            status="In Review",
            requested_by="Alex Test"
        )
        db.session.add(eco)
        db.session.commit()

        eval_result = StageGateService.evaluate_gates(project)
        self.assertFalse(eval_result["can_advance"])
        self.assertTrue(any("Critical or High-severity ECO" in b for b in eval_result["blocking_reasons"]))

    def test_purchase_gate_enforces_readiness_threshold(self):
        project = Project(
            code="PRJ-TEST-03",
            name="Test Inverter",
            lead_engineer="Alex Test",
            current_stage=ProjectStage.PURCHASE.value
        )
        db.session.add(project)
        db.session.commit()

        # Add 2 items, only 1 delivered (50% readiness)
        b1 = BOMItem(
            project_id=project.id, part_number="P1", manufacturer_pn="MPN1",
            description="Resistor", category="Passive", supplier_name="Mouser",
            quantity_required=10, quantity_received=10, status="Delivered"
        )
        b2 = BOMItem(
            project_id=project.id, part_number="P2", manufacturer_pn="MPN2",
            description="MCU", category="Microcontroller", supplier_name="DigiKey",
            quantity_required=1, quantity_received=0, status="PO Placed"
        )
        db.session.add_all([b1, b2])
        db.session.commit()

        eval_result = StageGateService.evaluate_gates(project)
        self.assertFalse(eval_result["can_advance"])
        self.assertTrue(any("readiness is at 50.0%" in b for b in eval_result["blocking_reasons"]))

        # Mark b2 as delivered (100% readiness)
        b2.status = "Delivered"
        b2.quantity_received = 1
        db.session.commit()

        eval_result = StageGateService.evaluate_gates(project)
        self.assertTrue(eval_result["can_advance"])

    def test_advance_stage_with_override(self):
        project = Project(
            code="PRJ-TEST-04",
            name="Test Fast-track Unit",
            lead_engineer="Alex Test",
            current_stage=ProjectStage.DESIGN.value
        )
        db.session.add(project)
        db.session.commit()

        # Gate is unfulfilled, standard advance should fail
        res = StageGateService.advance_stage(project, ProjectStage.PURCHASE.value, override=False)
        self.assertFalse(res["success"])

        # Override advance should succeed
        res_override = StageGateService.advance_stage(
            project,
            ProjectStage.PURCHASE.value,
            override=True,
            override_reason="Executive fast-track authorization for prototype pilot."
        )
        self.assertTrue(res_override["success"])
        self.assertEqual(project.current_stage, ProjectStage.PURCHASE.value)

if __name__ == "__main__":
    unittest.main()
