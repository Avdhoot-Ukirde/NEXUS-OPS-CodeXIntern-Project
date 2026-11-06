from app.routes.views import views_bp
from app.routes.api_projects import api_projects_bp
from app.routes.api_design import api_design_bp
from app.routes.api_procurement import api_procurement_bp
from app.routes.api_assembly import api_assembly_bp
from app.routes.api_software import api_software_bp
from app.routes.api_dispatch import api_dispatch_bp
from app.routes.api_analytics import api_analytics_bp

__all__ = [
    "views_bp",
    "api_projects_bp",
    "api_design_bp",
    "api_procurement_bp",
    "api_assembly_bp",
    "api_software_bp",
    "api_dispatch_bp",
    "api_analytics_bp",
]

