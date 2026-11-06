import os
from flask import Flask, jsonify
from app.config import Config
from app.extensions import db
from app.routes import (
    views_bp,
    api_projects_bp,
    api_design_bp,
    api_procurement_bp,
    api_assembly_bp,
    api_software_bp,
    api_dispatch_bp,
    api_analytics_bp,
)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload folder exists
    os.makedirs(app.config.get("UPLOAD_FOLDER", "uploads"), exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(views_bp)
    app.register_blueprint(api_projects_bp)
    app.register_blueprint(api_design_bp)
    app.register_blueprint(api_procurement_bp)
    app.register_blueprint(api_assembly_bp)
    app.register_blueprint(api_software_bp)
    app.register_blueprint(api_dispatch_bp)
    app.register_blueprint(api_analytics_bp)

    # Register error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found", "status_code": 404}), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return jsonify({"error": "Internal server error", "status_code": 500}), 500

    # Create tables
    with app.app_context():
        db.create_all()

    return app

