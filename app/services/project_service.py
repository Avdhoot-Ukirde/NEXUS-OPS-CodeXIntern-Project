from typing import Dict, Any, List
from app.extensions import db
from app.models.project import Project, ProjectStage, HealthStatus
from app.models.procurement import BOMItem
from app.models.software import SoftwareTestCase
from app.models.assembly import PhysicalUnit

class ProjectService:

    @staticmethod
    def get_dashboard_metrics() -> Dict[str, Any]:
        """Calculates global executive KPIs across all projects and stages."""
        projects = Project.query.all()
        total_projects = len(projects)

        stages_count = {
            ProjectStage.DESIGN.value: 0,
            ProjectStage.PURCHASE.value: 0,
            ProjectStage.ASSEMBLY.value: 0,
            ProjectStage.SOFTWARE.value: 0,
            ProjectStage.DISPATCH.value: 0,
            ProjectStage.COMPLETED.value: 0,
        }

        health_count = {
            HealthStatus.ON_TRACK.value: 0,
            HealthStatus.AT_RISK.value: 0,
            HealthStatus.BLOCKED.value: 0,
            HealthStatus.DELAYED.value: 0,
        }

        total_budget = 0.0
        total_actual = 0.0

        for p in projects:
            if p.current_stage in stages_count:
                stages_count[p.current_stage] += 1
            if p.health_status in health_count:
                health_count[p.health_status] += 1
            total_budget += p.budget
            total_actual += p.actual_cost

        # Overall BOM spend and items
        all_bom_items = BOMItem.query.all()
        total_bom_items = len(all_bom_items)
        delivered_bom_items = len([b for b in all_bom_items if b.status == "Delivered"])
        overall_bom_readiness = (delivered_bom_items / total_bom_items * 100) if total_bom_items > 0 else 0.0
        high_risk_lead_times = len([b for b in all_bom_items if b.risk_level == "High"])

        # Overall Software test pass rate
        all_tests = SoftwareTestCase.query.all()
        passed_tests = len([t for t in all_tests if t.result == "Passed"])
        overall_test_pass_rate = (passed_tests / len(all_tests) * 100) if all_tests else 0.0

        # Physical units in assembly
        all_units = PhysicalUnit.query.all()
        completed_units = len([u for u in all_units if u.build_stage == "Validation Passed"])

        return {
            "total_projects": total_projects,
            "stage_distribution": stages_count,
            "health_distribution": health_count,
            "financials": {
                "total_budget": round(total_budget, 2),
                "total_actual": round(total_actual, 2),
                "variance": round(total_budget - total_actual, 2),
            },
            "procurement_kpis": {
                "total_bom_items": total_bom_items,
                "delivered_bom_items": delivered_bom_items,
                "readiness_pct": round(overall_bom_readiness, 1),
                "high_risk_components": high_risk_lead_times,
            },
            "software_kpis": {
                "total_tests": len(all_tests),
                "passed_tests": passed_tests,
                "pass_rate_pct": round(overall_test_pass_rate, 1),
            },
            "assembly_kpis": {
                "total_units": len(all_units),
                "validated_units": completed_units,
            }
        }

