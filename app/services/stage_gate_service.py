from typing import Dict, Any, List
from app.models.project import Project, ProjectStage
from app.models.design import DesignDoc, EngineeringChangeOrder
from app.models.procurement import BOMItem
from app.models.assembly import PhysicalUnit, AssemblyTravelerStep
from app.models.software import SoftwareTestCase, FirmwareRelease
from app.models.dispatch import QualityCertification, PackagingItem, ShipmentRecord

STAGE_ORDER = [
    ProjectStage.DESIGN.value,
    ProjectStage.PURCHASE.value,
    ProjectStage.ASSEMBLY.value,
    ProjectStage.SOFTWARE.value,
    ProjectStage.DISPATCH.value,
    ProjectStage.COMPLETED.value,
]

class StageGateService:

    @staticmethod
    def evaluate_gates(project: Project) -> Dict[str, Any]:
        """
        Evaluates the readiness criteria for transitioning across each stage of the project.
        Returns detailed check results, pass/fail status, and warnings.
        """
        design_checks = StageGateService._check_design_stage(project)
        purchase_checks = StageGateService._check_purchase_stage(project)
        assembly_checks = StageGateService._check_assembly_stage(project)
        software_checks = StageGateService._check_software_stage(project)
        dispatch_checks = StageGateService._check_dispatch_stage(project)

        current_idx = STAGE_ORDER.index(project.current_stage) if project.current_stage in STAGE_ORDER else 0
        next_stage = STAGE_ORDER[current_idx + 1] if current_idx < len(STAGE_ORDER) - 1 else None

        # Determine if can advance to next stage
        can_advance = False
        reasons_blocking = []

        if project.current_stage == ProjectStage.DESIGN.value:
            can_advance = design_checks["passed"]
            reasons_blocking = design_checks["blockers"]
        elif project.current_stage == ProjectStage.PURCHASE.value:
            can_advance = purchase_checks["passed"]
            reasons_blocking = purchase_checks["blockers"]
        elif project.current_stage == ProjectStage.ASSEMBLY.value:
            can_advance = assembly_checks["passed"]
            reasons_blocking = assembly_checks["blockers"]
        elif project.current_stage == ProjectStage.SOFTWARE.value:
            can_advance = software_checks["passed"]
            reasons_blocking = software_checks["blockers"]
        elif project.current_stage == ProjectStage.DISPATCH.value:
            can_advance = dispatch_checks["passed"]
            reasons_blocking = dispatch_checks["blockers"]
        else:
            can_advance = False

        return {
            "current_stage": project.current_stage,
            "next_stage": next_stage,
            "can_advance": can_advance,
            "blocking_reasons": reasons_blocking,
            "stages": {
                ProjectStage.DESIGN.value: design_checks,
                ProjectStage.PURCHASE.value: purchase_checks,
                ProjectStage.ASSEMBLY.value: assembly_checks,
                ProjectStage.SOFTWARE.value: software_checks,
                ProjectStage.DISPATCH.value: dispatch_checks,
            }
        }

    @staticmethod
    def _check_design_stage(project: Project) -> Dict[str, Any]:
        docs = project.design_docs.all()
        approved_docs = [d for d in docs if d.status == "Approved"]
        pending_docs = [d for d in docs if d.status != "Approved"]
        open_critical_ecos = project.ecos.filter(
            EngineeringChangeOrder.status.in_(["Proposed", "In Review"]),
            EngineeringChangeOrder.severity.in_(["Critical", "High"])
        ).all()

        blockers = []
        if not docs:
            blockers.append("No CAD / schematic documentation registered.")
        if len(approved_docs) == 0 and len(docs) > 0:
            blockers.append("No design documents have received engineering sign-off/approval.")
        if open_critical_ecos:
            blockers.append(f"{len(open_critical_ecos)} Critical or High-severity ECO(s) still open.")

        return {
            "passed": len(blockers) == 0,
            "total_docs": len(docs),
            "approved_docs": len(approved_docs),
            "pending_docs": len(pending_docs),
            "open_critical_ecos": len(open_critical_ecos),
            "blockers": blockers
        }

    @staticmethod
    def _check_purchase_stage(project: Project) -> Dict[str, Any]:
        bom_items = project.bom_items.all()
        total_items = len(bom_items)
        delivered_items = [b for b in bom_items if b.status == "Delivered"]
        backordered = [b for b in bom_items if b.status == "Backordered"]
        high_risk = [b for b in bom_items if b.risk_level == "High"]

        readiness_pct = (len(delivered_items) / total_items * 100) if total_items > 0 else 0.0

        blockers = []
        if total_items == 0:
            blockers.append("Bill of Materials (BOM) is empty. Add required components.")
        elif readiness_pct < 80.0:
            blockers.append(f"BOM procurement readiness is at {readiness_pct:.1f}%. Minimum required is 80.0% before assembly.")
        if backordered:
            blockers.append(f"{len(backordered)} critical component(s) are currently backordered.")

        return {
            "passed": len(blockers) == 0,
            "total_items": total_items,
            "delivered_items": len(delivered_items),
            "readiness_pct": round(readiness_pct, 1),
            "backordered_count": len(backordered),
            "high_risk_count": len(high_risk),
            "blockers": blockers
        }

    @staticmethod
    def _check_assembly_stage(project: Project) -> Dict[str, Any]:
        units = project.physical_units.all()
        validated_units = [u for u in units if u.build_stage == "Validation Passed"]
        units_with_open_defects = []
        for u in units:
            open_defects = u.defects.filter(AssemblyDefect.disposition == "Pending").count()
            if open_defects > 0:
                units_with_open_defects.append(u.serial_number)

        blockers = []
        if not units:
            blockers.append("No physical build units registered in the system.")
        elif len(validated_units) == 0:
            blockers.append("No physical units have completed assembly and passed component validation.")
        if units_with_open_defects:
            blockers.append(f"Units with unresolved defects: {', '.join(units_with_open_defects)}")

        return {
            "passed": len(blockers) == 0,
            "total_units": len(units),
            "validated_units": len(validated_units),
            "unresolved_defect_units": len(units_with_open_defects),
            "blockers": blockers
        }

    @staticmethod
    def _check_software_stage(project: Project) -> Dict[str, Any]:
        test_cases = project.test_cases.all()
        critical_tests = [t for t in test_cases if t.is_critical]
        passed_critical = [t for t in critical_tests if t.result == "Passed"]
        failed_critical = [t for t in critical_tests if t.result == "Failed"]
        not_run_critical = [t for t in critical_tests if t.result == "Not Run"]
        releases = project.firmware_releases.all()

        blockers = []
        if not releases:
            blockers.append("No firmware/software release version tagged for this project.")
        if not test_cases:
            blockers.append("No software/firmware test checklists created.")
        elif failed_critical:
            blockers.append(f"{len(failed_critical)} critical software test(s) failed (e.g., HIL / Safety).")
        elif not_run_critical:
            blockers.append(f"{len(not_run_critical)} critical software test(s) not yet executed.")

        total = len(test_cases)
        passed_all = len([t for t in test_cases if t.result == "Passed"])
        pass_rate = (passed_all / total * 100) if total > 0 else 0.0

        return {
            "passed": len(blockers) == 0,
            "firmware_releases_count": len(releases),
            "total_tests": total,
            "passed_tests": passed_all,
            "critical_tests_count": len(critical_tests),
            "critical_passed_count": len(passed_critical),
            "pass_rate_pct": round(pass_rate, 1),
            "blockers": blockers
        }

    @staticmethod
    def _check_dispatch_stage(project: Project) -> Dict[str, Any]:
        certs = project.qa_certs.all()
        passed_certs = [c for c in certs if c.status == "Passed"]
        
        packaging = project.packaging_items.all()
        verified_packaging = [p for p in packaging if p.is_verified]

        shipments = project.shipments.all()

        blockers = []
        if not certs or len(passed_certs) == 0:
            blockers.append("Final QA compliance certification (Hi-Pot, ESD, FCC/CE) missing or not passed.")
        if not packaging:
            blockers.append("Packaging checklist items have not been defined.")
        elif len(verified_packaging) < len(packaging):
            unverified_count = len(packaging) - len(verified_packaging)
            blockers.append(f"{unverified_count} packaging item(s) unverified (e.g. anti-static seal, accessories).")
        if not shipments:
            blockers.append("No shipping details or tracking numbers assigned for dispatch.")

        return {
            "passed": len(blockers) == 0,
            "qa_certs_count": len(certs),
            "qa_passed_count": len(passed_certs),
            "packaging_total": len(packaging),
            "packaging_verified": len(verified_packaging),
            "shipments_count": len(shipments),
            "blockers": blockers
        }

    @staticmethod
    def advance_stage(project: Project, target_stage: str, override: bool = False, override_reason: str = None, performed_by: str = "Systems Lead") -> Dict[str, Any]:
        current_idx = STAGE_ORDER.index(project.current_stage) if project.current_stage in STAGE_ORDER else 0
        if target_stage not in STAGE_ORDER:
            return {"success": False, "error": f"Invalid stage '{target_stage}'."}

        target_idx = STAGE_ORDER.index(target_stage)
        if target_idx <= current_idx:
            # Reverting or staying on same stage is allowed
            old_stage = project.current_stage
            project.current_stage = target_stage
            return {"success": True, "old_stage": old_stage, "new_stage": target_stage}

        # Check gate
        eval_result = StageGateService.evaluate_gates(project)
        if not eval_result["can_advance"] and not override:
            return {
                "success": False,
                "error": "Stage gate validation failed. Prerequisites are not satisfied.",
                "blockers": eval_result["blocking_reasons"]
            }

        old_stage = project.current_stage
        project.current_stage = target_stage
        if target_stage == ProjectStage.COMPLETED.value:
            project.health_status = "On Track"
        return {
            "success": True,
            "old_stage": old_stage,
            "new_stage": target_stage,
            "overridden": override,
            "override_reason": override_reason
        }

from app.models.assembly import AssemblyDefect

