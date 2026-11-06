import unittest
import json
from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models.project import Project, ProjectStage

class TestAPIProjects(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_create_and_get_project(self):
        payload = {
            "code": "PRJ-TEST-API",
            "name": "Autonomous Delivery Drone",
            "description": "Heavy-lift delivery drone prototype",
            "lead_engineer": "Dr. Sarah",
            "priority": "High",
            "budget": 50000.0,
            "target_date": "2026-12-31"
        }
        res = self.client.post("/api/v1/projects", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["code"], "PRJ-TEST-API")
        self.assertEqual(data["current_stage"], "Design")

        # Get project
        get_res = self.client.get(f"/api/v1/projects/{data['id']}")
        self.assertEqual(get_res.status_code, 200)
        get_data = get_res.get_json()
        self.assertEqual(get_data["name"], "Autonomous Delivery Drone")

    def test_duplicate_project_code_rejected(self):
        payload = {
            "code": "PRJ-DUP-01",
            "name": "Unit A",
            "lead_engineer": "Engineer A",
            "priority": "Low",
            "budget": 1000.0
        }
        res1 = self.client.post("/api/v1/projects", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res1.status_code, 201)

        res2 = self.client.post("/api/v1/projects", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res2.status_code, 409)

    def test_design_document_workflow(self):
        # Create project
        proj = Project(code="PRJ-DESIGN-01", name="Design System", lead_engineer="Chief Arch")
        db.session.add(proj)
        db.session.commit()

        # Add design doc
        doc_payload = {
            "title": "Main Motherboard Schematic",
            "doc_type": "Schematic",
            "subsystem": "Power & Compute",
            "version": "Rev 1.0",
            "author": "Chief Arch"
        }
        res = self.client.post(f"/api/v1/projects/{proj.id}/design-docs", data=json.dumps(doc_payload), content_type="application/json")
        self.assertEqual(res.status_code, 201)
        doc_data = res.get_json()
        self.assertEqual(doc_data["status"], "Under Review")

        # Approve design doc
        app_res = self.client.put(f"/api/v1/design-docs/{doc_data['id']}/approve", data=json.dumps({
            "status": "Approved",
            "approved_by": "Dr. Lead",
            "notes": "Reviewed and verified."
        }), content_type="application/json")
        self.assertEqual(app_res.status_code, 200)
        self.assertEqual(app_res.get_json()["status"], "Approved")

    def test_assembly_unit_and_defect_logging(self):
        proj = Project(code="PRJ-ASM-01", name="Assembly System", lead_engineer="Tech Lead")
        db.session.add(proj)
        db.session.commit()

        # Register unit
        unit_payload = {
            "serial_number": "SN-UNIT-9001",
            "batch_number": "BATCH-01",
            "variant": "Proto Rev A",
            "assigned_technician": "John Tech"
        }
        res = self.client.post(f"/api/v1/projects/{proj.id}/units", data=json.dumps(unit_payload), content_type="application/json")
        self.assertEqual(res.status_code, 201)
        unit = res.get_json()
        self.assertEqual(len(unit["traveler_steps"]), 6)  # Standard 6-step traveler auto-generated

        # Log defect
        defect_payload = {
            "defect_type": "Cold Solder Joint",
            "severity": "Major",
            "description": "Pins 12-14 on MCU bridge identified during AOI.",
            "logged_by": "John Tech"
        }
        d_res = self.client.post(f"/api/v1/units/{unit['id']}/defects", data=json.dumps(defect_payload), content_type="application/json")
        self.assertEqual(d_res.status_code, 201)
        self.assertEqual(d_res.get_json()["severity"], "Major")

    def test_software_test_execution_and_flashing(self):
        proj = Project(code="PRJ-SW-01", name="Software System", lead_engineer="Firmware Lead")
        db.session.add(proj)
        db.session.commit()

        # Add test case
        tc_payload = {
            "test_suite": "Hardware-In-The-Loop (HIL)",
            "test_name": "Emergency Stop Watchdog",
            "expected_result": "Motor cutoff < 20ms",
            "is_critical": True
        }
        res = self.client.post(f"/api/v1/projects/{proj.id}/tests", data=json.dumps(tc_payload), content_type="application/json")
        self.assertEqual(res.status_code, 201)
        tc_id = res.get_json()["id"]

        # Update test result
        update_res = self.client.put(f"/api/v1/tests/{tc_id}", data=json.dumps({
            "result": "Passed",
            "executed_by": "Firmware Lead",
            "execution_notes": "Cutoff verified at 11ms on oscilloscope."
        }), content_type="application/json")
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.get_json()["result"], "Passed")

if __name__ == "__main__":
    unittest.main()

