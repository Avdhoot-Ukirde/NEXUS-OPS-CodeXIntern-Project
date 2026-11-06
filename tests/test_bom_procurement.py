import unittest
from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models.project import Project
from app.models.procurement import BOMItem

class TestBOMProcurement(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        self.project = Project(
            code="PRJ-BOM-01",
            name="Robotics Arm Board",
            lead_engineer="Dr. Elena",
            budget=5000.0
        )
        db.session.add(self.project)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_bom_cost_and_risk_calculation(self):
        # Long lead time (> 28 days) -> High risk
        item1 = BOMItem(
            project_id=self.project.id,
            part_number="IPN-FPGA-01",
            manufacturer_pn="XCKU040-1FFVA1156E",
            description="UltraScale FPGA",
            category="Microcontroller",
            quantity_required=2,
            unit_cost=1450.00,
            supplier_name="Arrow",
            lead_time_days=35,
            status="PO Placed"
        )
        item1.calculate_cost()
        self.assertEqual(item1.total_cost, 2900.00)
        self.assertEqual(item1.risk_level, "High")

        # Medium lead time (15 days) -> Medium risk
        item2 = BOMItem(
            project_id=self.project.id,
            part_number="IPN-CAP-01",
            manufacturer_pn="GRM155R71C104KA88D",
            description="0.1uF 16V Ceramic Cap",
            category="Passive",
            quantity_required=100,
            unit_cost=0.05,
            supplier_name="Mouser",
            lead_time_days=15,
            status="PO Placed"
        )
        item2.calculate_cost()
        self.assertEqual(item2.total_cost, 5.00)
        self.assertEqual(item2.risk_level, "Medium")

        # Short lead time (3 days) -> Low risk
        item3 = BOMItem(
            project_id=self.project.id,
            part_number="IPN-RES-01",
            manufacturer_pn="RC0402FR-0710KL",
            description="10k Resistor",
            category="Passive",
            quantity_required=50,
            unit_cost=0.02,
            supplier_name="DigiKey",
            lead_time_days=3,
            status="PO Placed"
        )
        item3.calculate_cost()
        self.assertEqual(item3.risk_level, "Low")

if __name__ == "__main__":
    unittest.main()

