import os
import sys
from app import create_app
from seed_data import seed_database
from app.models.project import Project

app = create_app()

def main():
    # If database is empty, automatically seed with realistic projects
    with app.app_context():
        if Project.query.count() == 0:
            print("[NEXUS-OPS] Initializing database with realistic engineering projects...")
            seed_database()

    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

    print("\n" + "=" * 68)
    print("  🚀 NEXUS-OPS | Hardware & Software Integrated Engineering Platform")
    print("=" * 68)
    print(f"  Stage 1: Design     -> CAD / Schematic Approvals & ECOs")
    print(f"  Stage 2: Purchase   -> Procurement, Supplier Lead Times & BOM")
    print(f"  Stage 3: Assembly   -> Shop Traveler Milestones & Defect Tracking")
    print(f"  Stage 4: Software   -> Firmware Releases, Flashing & HIL Tests")
    print(f"  Stage 5: Dispatch   -> Final QA Certification, Packaging & Carrier")
    print("-" * 68)
    print(f"  Server listening at: http://127.0.0.1:{port}")
    print("=" * 68 + "\n")

    app.run(host="0.0.0.0", port=port, debug=debug)

if __name__ == "__main__":
    main()

