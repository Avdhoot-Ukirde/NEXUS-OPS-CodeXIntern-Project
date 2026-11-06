from datetime import datetime, date, timedelta
from app import create_app
from app.extensions import db
from app.models.project import Project, ProjectStage, HealthStatus, PriorityLevel
from app.models.design import DesignDoc, EngineeringChangeOrder
from app.models.procurement import BOMItem
from app.models.assembly import PhysicalUnit, AssemblyTravelerStep, AssemblyDefect
from app.models.software import FirmwareRelease, FlashRecord, SoftwareTestCase
from app.models.dispatch import QualityCertification, PackagingItem, ShipmentRecord
from app.models.activity import ActivityLog

def seed_database():
    app = create_app()
    with app.app_context():
        # Clean existing
        db.drop_all()
        db.create_all()

        print("[Seed] Seeding Production Engineering Projects...")

        # ---------------------------------------------------------
        # PROJECT 1: AMR Titan 500 (Autonomous Mobile Robot) - Stage: ASSEMBLY
        # ---------------------------------------------------------
        p1 = Project(
            code="PRJ-ROBOT-01",
            name="AMR Titan 500 Heavy-Payload Logistics Rover",
            description="Autonomous industrial mobile robot with 500kg payload capacity, dual-LiDAR SLAM, STM32 safety PLC, and CANopen motor controllers.",
            lead_engineer="Dr. Elena Rostova (Lead Robotics HW/SW)",
            current_stage=ProjectStage.ASSEMBLY.value,
            health_status=HealthStatus.ON_TRACK.value,
            priority=PriorityLevel.CRITICAL.value,
            target_date=date.today() + timedelta(days=45),
            budget=125000.0,
            actual_cost=78450.0,
        )
        db.session.add(p1)
        db.session.flush()

        # Design Docs for P1
        d1 = DesignDoc(
            project_id=p1.id,
            title="Titan-500 Motherboard Schematic & Layer Stack",
            doc_type="Schematic",
            subsystem="Main Controller PCB",
            version="Rev 2.1",
            file_url="/cad/titan500_main_rev2.1.pdf",
            status="Approved",
            author="David Chen",
            approved_by="Dr. Elena Rostova",
            approved_at=datetime.utcnow() - timedelta(days=25),
            review_notes="Differential pair routing for CAN FD verified. Ground return planes verified for motor noise immunity."
        )
        d2 = DesignDoc(
            project_id=p1.id,
            title="Chassis & Battery Compartment Enclosure 3D CAD",
            doc_type="Mechanical CAD",
            subsystem="Structural Chassis",
            version="Rev 2.0",
            file_url="/cad/titan500_chassis_rev2.step",
            status="Approved",
            author="Marcus Vance",
            approved_by="Dr. Elena Rostova",
            approved_at=datetime.utcnow() - timedelta(days=20),
            review_notes="FEA stress simulation passed for 750kg static load test."
        )
        db.session.add_all([d1, d2])

        # ECO for P1 (Resolved)
        eco1 = EngineeringChangeOrder(
            project_id=p1.id,
            eco_number="ECO-2026-012",
            title="Replace Discontinued 48V Buck Regulator with High-Efficiency LM5164",
            description="Original buck controller obsolete with 40-week lead time. Replaced with LM5164QDDARQ1.",
            reason="Component Obsolescence",
            severity="Medium",
            affected_subsystems="Power Distribution Board",
            status="Implemented",
            requested_by="David Chen",
            approved_by="Dr. Elena Rostova",
            created_at=datetime.utcnow() - timedelta(days=30),
            resolved_at=datetime.utcnow() - timedelta(days=24)
        )
        db.session.add(eco1)

        # BOM for P1
        bom_p1 = [
            BOMItem(
                project_id=p1.id, part_number="IPN-MCU-001", manufacturer_pn="STM32H753IIT6",
                description="High-performance ARM Cortex-M7 480MHz Microcontroller", category="Microcontroller",
                subsystem="Main Controller", quantity_required=4, quantity_received=4, unit_cost=24.50,
                supplier_name="Mouser Electronics", lead_time_days=5, status="Delivered", risk_level="Low"
            ),
            BOMItem(
                project_id=p1.id, part_number="IPN-DRV-002", manufacturer_pn="DRV8353RSRGZR",
                description="3-Phase Smart Gate Driver with Current Sense Amps", category="Power IC",
                subsystem="Motor Inverter", quantity_required=8, quantity_received=8, unit_cost=9.80,
                supplier_name="DigiKey", lead_time_days=7, status="Delivered", risk_level="Low"
            ),
            BOMItem(
                project_id=p1.id, part_number="IPN-LID-001", manufacturer_pn="OS1-32-REV7",
                description="32-Channel Mid-Range Digital LiDAR Sensor", category="Sensor",
                subsystem="Perception", quantity_required=2, quantity_received=2, unit_cost=3200.00,
                supplier_name="Ouster Logistics", lead_time_days=14, status="Delivered", risk_level="Medium"
            ),
            BOMItem(
                project_id=p1.id, part_number="IPN-BAT-001", manufacturer_pn="LP48V-50AH",
                description="48V 50Ah LiFePO4 Smart Battery Pack with RS485 BMS", category="Power IC",
                subsystem="Power Subsystem", quantity_required=2, quantity_received=2, unit_cost=1850.00,
                supplier_name="EnerSys Dynamics", lead_time_days=21, status="Delivered", risk_level="Low"
            ),
            BOMItem(
                project_id=p1.id, part_number="IPN-MEC-005", manufacturer_pn="AL6061-T6-FRAME",
                description="CNC Milled Base Chassis Frame 6061-T6 Black Anodized", category="Mechanical",
                subsystem="Structural", quantity_required=2, quantity_received=2, unit_cost=850.00,
                supplier_name="Xometry Precision", lead_time_days=18, status="Delivered", risk_level="Low"
            ),
            BOMItem(
                project_id=p1.id, part_number="IPN-CON-010", manufacturer_pn="AMPHENOL-AT06-6S",
                description="IP67 Automotive 6-Pin Sealed Connector Plug", category="Connector",
                subsystem="Wiring Harness", quantity_required=24, quantity_received=24, unit_cost=4.20,
                supplier_name="Mouser Electronics", lead_time_days=4, status="Delivered", risk_level="Low"
            ),
        ]
        for item in bom_p1:
            item.calculate_cost()
            db.session.add(item)

        # Physical Units for P1
        u1 = PhysicalUnit(
            project_id=p1.id,
            serial_number="AMR-SN-2026-001",
            batch_number="BATCH-ALPHA-01",
            variant="Titan-500 Rev B",
            build_stage="Power Rail Voltage Check",
            assigned_technician="Sarah Jenkins (Senior Assembly Lead)",
            notes="Chassis integrated. Main board fitted with thermal gap pads."
        )
        db.session.add(u1)
        db.session.flush()

        # Traveler steps for U1
        step1 = AssemblyTravelerStep(
            unit_id=u1.id, step_order=1, name="SMT Stencil & Pick-and-Place Assembly",
            technician="Sarah Jenkins", status="Passed",
            inspection_criteria="IPC-A-610 Class 2 compliance. Verify solder paste height.",
            measured_values="Solder paste height 125µm nominal, zero misaligned 0402 passives.",
            completed_at=datetime.utcnow() - timedelta(days=4)
        )
        step2 = AssemblyTravelerStep(
            unit_id=u1.id, step_order=2, name="Automated Optical Inspection (AOI) & Reflow Check",
            technician="Sarah Jenkins", status="Passed",
            inspection_criteria="Zero solder bridges or tombstoning.",
            measured_values="BGA ball coplanarity checked on X-ray inspection. Zero voids detected.",
            completed_at=datetime.utcnow() - timedelta(days=3)
        )
        step3 = AssemblyTravelerStep(
            unit_id=u1.id, step_order=3, name="Power Rail Voltage & Short-Circuit Verification",
            technician="Sarah Jenkins", status="In Progress",
            inspection_criteria="Verify 3.3V, 5.0V, 12V, 48V rails without thermal spike.",
            measured_values="3.32V (+0.6%), 5.03V (+0.6%), 12.01V nominal. 48V rail test in progress.",
            completed_at=None
        )
        step4 = AssemblyTravelerStep(
            unit_id=u1.id, step_order=4, name="Mechanical Enclosure & Heatsink Integration",
            technician="Sarah Jenkins", status="Pending",
            inspection_criteria="Torque chassis bolts to 1.8 N·m. Inspect thermal gap pad compression."
        )
        step5 = AssemblyTravelerStep(
            unit_id=u1.id, step_order=5, name="Wiring Harness Routing & Strain Relief Test",
            technician="Sarah Jenkins", status="Pending",
            inspection_criteria="Continuous continuity check, crimp pull force > 30N."
        )
        step6 = AssemblyTravelerStep(
            unit_id=u1.id, step_order=6, name="Subsystem Burn-in & Component Validation",
            technician="Sarah Jenkins", status="Pending",
            inspection_criteria="2-hour idle soak test at 45°C ambient."
        )
        db.session.add_all([step1, step2, step3, step4, step5, step6])

        # Software releases & tests for P1
        fw1 = FirmwareRelease(
            project_id=p1.id, target_subsystem="Safety PLC & Motor Driver", version="v1.2.0-rc3",
            git_commit_hash="a89f3c1d942e88b201a4bc591efb045169a8b122",
            binary_checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            release_type="Release Candidate",
            release_notes="Added emergency stop hardware watchdog reset and CANopen PDO heartbeat sync.",
            status="Testing", created_by="Liam O'Connor (Lead Embedded SW)"
        )
        db.session.add(fw1)

        t1_p1 = SoftwareTestCase(
            project_id=p1.id, test_suite="CAN Bus Comms",
            test_name="CAN FD 1Mbps Bus Load & Jitter Verification",
            expected_result="Packet drop < 0.001% at 75% peak bus load",
            result="Passed", is_critical=True, executed_by="Liam O'Connor",
            executed_at=datetime.utcnow() - timedelta(days=2),
            execution_notes="Ran Vector CANoe test bench for 4 hours. Zero frame errors recorded."
        )
        t2_p1 = SoftwareTestCase(
            project_id=p1.id, test_suite="Safety Interlocks",
            test_name="E-Stop Relay Open-Circuit Latency < 15ms",
            expected_result="Emergency stop signal drops motor power stage gate drives in < 15ms",
            result="Passed", is_critical=True, executed_by="Liam O'Connor",
            executed_at=datetime.utcnow() - timedelta(days=1),
            execution_notes="Oscilloscope capture confirmed 8.4ms cutoff delay."
        )
        t3_p1 = SoftwareTestCase(
            project_id=p1.id, test_suite="Hardware-In-The-Loop (HIL)",
            test_name="Dual LiDAR Pointcloud Ingestion & Odometry Sync",
            expected_result="Odometry timestamp synchronization drift < 2ms",
            result="In Progress", is_critical=True, executed_by="Liam O'Connor"
        )
        db.session.add_all([t1_p1, t2_p1, t3_p1])

        # Packaging items for P1
        pkg_p1 = [
            PackagingItem(project_id=p1.id, item_name="Heavy-Duty Wooden Transit Crate with Shock-Watch", category="Primary Enclosure", is_verified=False),
            PackagingItem(project_id=p1.id, item_name="48V 10A Fast Charger & Regional AC Cable", category="Accessory", is_verified=False),
            PackagingItem(project_id=p1.id, item_name="Emergency Stop Wireless Pendant & Key", category="Accessory", is_verified=False),
            PackagingItem(project_id=p1.id, item_name="Commissioning Manual & Calibration Certificate", category="Documentation", is_verified=False),
        ]
        db.session.add_all(pkg_p1)

        # ---------------------------------------------------------
        # PROJECT 2: PRJ-IOT-09 (Industrial Edge Gateway) - Stage: DISPATCH
        # ---------------------------------------------------------
        p2 = Project(
            code="PRJ-IOT-09",
            name="Smart Grid Edge Gateway Pro (LTE-M / Modbus)",
            description="Ruggedized DIN-rail mount gateway for renewable energy substations, supporting dual RS485, WireGuard VPN, and cellular telemetry.",
            lead_engineer="Marcus Vance (Principal Hardware Architect)",
            current_stage=ProjectStage.DISPATCH.value,
            health_status=HealthStatus.ON_TRACK.value,
            priority=PriorityLevel.HIGH.value,
            target_date=date.today() + timedelta(days=5),
            budget=45000.0,
            actual_cost=38200.0,
        )
        db.session.add(p2)
        db.session.flush()

        d3 = DesignDoc(
            project_id=p2.id, title="Substation Gateway Multi-Layer PCB Gerber & Schematics",
            doc_type="Schematic", subsystem="Carrier Board", version="Rev 1.4",
            status="Approved", author="Marcus Vance", approved_by="Marcus Vance",
            approved_at=datetime.utcnow() - timedelta(days=60)
        )
        db.session.add(d3)

        bom_p2 = [
            BOMItem(project_id=p2.id, part_number="IPN-SOM-001", manufacturer_pn="SOM-IMX8M-MINI", description="NXP i.MX 8M Mini Quad-Core System-on-Module", category="Microcontroller", quantity_required=5, quantity_received=5, unit_cost=75.0, supplier_name="Arrow", lead_time_days=7, status="Delivered"),
            BOMItem(project_id=p2.id, part_number="IPN-MOD-001", manufacturer_pn="EG915N-EU", description="LTE-M / NB-IoT Cellular Transceiver Module", category="Sensor", quantity_required=5, quantity_received=5, unit_cost=22.0, supplier_name="Quectel Direct", lead_time_days=10, status="Delivered"),
            BOMItem(project_id=p2.id, part_number="IPN-ENC-001", manufacturer_pn="DIN-CASE-105MM", description="Extruded Aluminum DIN Rail Enclosure IP40", category="Mechanical", quantity_required=5, quantity_received=5, unit_cost=18.5, supplier_name="Phoenix Contact", lead_time_days=5, status="Delivered"),
        ]
        for b in bom_p2:
            b.calculate_cost()
            db.session.add(b)

        u2 = PhysicalUnit(
            project_id=p2.id, serial_number="GW-SN-2026-101", batch_number="PILOT-PROD-01",
            variant="Rev 1.4 DIN-Mount", build_stage="Validation Passed",
            assigned_technician="John Miller", completed_at=datetime.utcnow() - timedelta(days=10)
        )
        db.session.add(u2)
        db.session.flush()

        for idx, step_name in enumerate(["SMT Assembly", "AOI & X-Ray", "Power Rail 3.3V/5V", "DIN Rail Enclosure Assembly", "Harness Wiring", "48h Thermal Soak Test"], 1):
            s = AssemblyTravelerStep(
                unit_id=u2.id, step_order=idx, name=step_name, technician="John Miller",
                status="Passed", measured_values="Nominal specifications verified", completed_at=datetime.utcnow() - timedelta(days=12)
            )
            db.session.add(s)

        fw2 = FirmwareRelease(
            project_id=p2.id, target_subsystem="Embedded Linux OS & Gateway Daemon", version="v2.0.1",
            git_commit_hash="74ef5c029a1b41c098192318e9c0b11234918ef1",
            binary_checksum="d41d8cd98f00b204e9800998ecf8427e01293847586940382910293847586940",
            release_type="Production Stable", release_notes="Final certified firmware image for EU/US grid substations.",
            status="Approved", created_by="Liam O'Connor"
        )
        db.session.add(fw2)

        tc1_p2 = SoftwareTestCase(project_id=p2.id, test_suite="Hardware-In-The-Loop (HIL)", test_name="Substation Modbus-TCP to Cloud MQTT Gateway Bridge", expected_result="10,000 telemetry messages sent with 0 loss", result="Passed", is_critical=True, executed_by="Liam O'Connor", executed_at=datetime.utcnow() - timedelta(days=8))
        tc2_p2 = SoftwareTestCase(project_id=p2.id, test_suite="Safety Interlocks", test_name="Hardware Watchdog Reboot Recovery < 3.2s", expected_result="Watchdog pulse timeout reboots MCU within 3.5s", result="Passed", is_critical=True, executed_by="Liam O'Connor", executed_at=datetime.utcnow() - timedelta(days=7))
        db.session.add_all([tc1_p2, tc2_p2])

        fl1 = FlashRecord(
            project_id=p2.id, unit_serial=u2.serial_number, firmware_version="v2.0.1",
            subsystem="NXP eMMC Bootloader & RootFS", flashed_by="John Miller",
            verification_status="Verified", log_output="Flashing complete. Verified CRC32 on partition mmcblk0p1. Fastboot locked."
        )
        db.session.add(fl1)

        # Dispatch QA Cert for P2
        qc1 = QualityCertification(
            project_id=p2.id, unit_serial=u2.serial_number, certificate_number="QC-CERT-2026-8801",
            inspector="Sarah Jenkins (QA Systems Inspector)", status="Passed",
            hipot_test_passed=True, esd_protection_passed=True, thermal_stress_passed=True,
            compliance_standards="FCC Part 15 Subpart B Class A, CE Mark, IEC 61850-3 Substation Certified",
            calibration_data="ADC Voltage sensor offset: 0.0012V. Real-time Clock drift: 0.12 ppm at 25°C.",
            sign_off_date=datetime.utcnow() - timedelta(days=3),
            notes="Passed rigorous 2.5kV surge withstand test and EFT immunity testing."
        )
        db.session.add(qc1)

        pkg_p2_1 = PackagingItem(project_id=p2.id, item_name="Anti-Static Shielding Bag with Desiccant Pack", category="Primary Enclosure", is_verified=True, checked_by="Sarah Jenkins", verified_at=datetime.utcnow() - timedelta(days=2))
        pkg_p2_2 = PackagingItem(project_id=p2.id, item_name="DIN-Rail Spring Clip & Mounting Hardware Kit", category="Accessory", is_verified=True, checked_by="Sarah Jenkins", verified_at=datetime.utcnow() - timedelta(days=2))
        pkg_p2_3 = PackagingItem(project_id=p2.id, item_name="External High-Gain LTE Blade Antenna", category="Accessory", is_verified=True, checked_by="Sarah Jenkins", verified_at=datetime.utcnow() - timedelta(days=2))
        pkg_p2_4 = PackagingItem(project_id=p2.id, item_name="Factory Calibration & Test Certificate Document", category="Documentation", is_verified=True, checked_by="Sarah Jenkins", verified_at=datetime.utcnow() - timedelta(days=2))
        db.session.add_all([pkg_p2_1, pkg_p2_2, pkg_p2_3, pkg_p2_4])

        shipment1 = ShipmentRecord(
            project_id=p2.id, unit_serial=u2.serial_number, destination_client="Apex Clean Energy Substations LLC",
            destination_address="1400 Renewable Way, Suite 400, Austin, TX 78701", carrier="DHL Express",
            tracking_number="DHL-9482019482-USA", ship_date=date.today() - timedelta(days=1),
            estimated_delivery=date.today() + timedelta(days=2), delivery_status="In Transit",
            customs_declaration="HS Code: 8517.62 (Data Transmission Gateway)"
        )
        db.session.add(shipment1)

        # ---------------------------------------------------------
        # PROJECT 3: PRJ-AERO-04 (Flight Controller) - Stage: DESIGN
        # ---------------------------------------------------------
        p3 = Project(
            code="PRJ-AERO-04",
            name="ApexFlight Tri-Redundant Drone Flight Avionics",
            description="Ultra-reliable avionics stack for commercial beyond-visual-line-of-sight (BVLOS) UAVs, featuring triple IMU lockstep architecture and RTK GPS.",
            lead_engineer="Dr. Elena Rostova",
            current_stage=ProjectStage.DESIGN.value,
            health_status=HealthStatus.AT_RISK.value,
            priority=PriorityLevel.CRITICAL.value,
            target_date=date.today() + timedelta(days=90),
            budget=180000.0,
            actual_cost=21000.0,
        )
        db.session.add(p3)
        db.session.flush()

        d4 = DesignDoc(
            project_id=p3.id, title="Tri-Redundant Sensor Array PCB Schematic",
            doc_type="Schematic", subsystem="Avionics Core", version="Rev 1.0",
            status="Under Review", author="David Chen", review_notes="Thermal isolation for Barometer and IMUs requires verification."
        )
        db.session.add(d4)

        eco2 = EngineeringChangeOrder(
            project_id=p3.id, eco_number="ECO-2026-019",
            title="Thermal Isolation Slot Required Between DC-DC Converter and IMU Sensor 1",
            description="High-frequency switcher inductor heat causes thermal drift in IMU accelerometer bias. Need routed air gap in PCB layout.",
            reason="Thermal Optimization", severity="Critical", affected_subsystems="Avionics Core PCB",
            status="In Review", requested_by="David Chen"
        )
        db.session.add(eco2)

        # ---------------------------------------------------------
        # PROJECT 4: PRJ-MED-02 (Wearable Vital Sensor) - Stage: SOFTWARE
        # ---------------------------------------------------------
        p4 = Project(
            code="PRJ-MED-02",
            name="CardioSync Clinical Continuous Vital Monitor",
            description="Continuous clinical-grade ECG and SpO2 wearable patch with Bluetooth Low Energy 5.3, wireless inductive charging, and medical cloud sync.",
            lead_engineer="Liam O'Connor",
            current_stage=ProjectStage.SOFTWARE.value,
            health_status=HealthStatus.DELAYED.value,
            priority=PriorityLevel.HIGH.value,
            target_date=date.today() + timedelta(days=25),
            budget=95000.0,
            actual_cost=67000.0,
        )
        db.session.add(p4)
        db.session.flush()

        d5 = DesignDoc(
            project_id=p4.id, title="Flexible PCB & Biosensor Circuit Schematic",
            doc_type="Schematic", subsystem="Flex Sensor Board", version="Rev 2.0",
            status="Approved", author="Marcus Vance", approved_by="Liam O'Connor", approved_at=datetime.utcnow() - timedelta(days=40)
        )
        db.session.add(d5)

        bom_p4 = [
            BOMItem(project_id=p4.id, part_number="IPN-BLE-001", manufacturer_pn="NRF5340-CLAA-R", description="Dual-Core ARM Cortex-M33 Bluetooth 5.3 SoC", category="Microcontroller", quantity_required=10, quantity_received=10, unit_cost=7.80, supplier_name="Nordic Semi / Mouser", lead_time_days=6, status="Delivered"),
            BOMItem(project_id=p4.id, part_number="IPN-AFE-001", manufacturer_pn="MAX86176ETD+", description="Ultra-Low-Power Optical Photoplethysmography & ECG Analog Front End", category="Sensor", quantity_required=10, quantity_received=10, unit_cost=11.20, supplier_name="Analog Devices", lead_time_days=9, status="Delivered"),
        ]
        for b in bom_p4:
            b.calculate_cost()
            db.session.add(b)

        u4 = PhysicalUnit(
            project_id=p4.id, serial_number="MED-SN-001-PROTO", batch_number="PROTO-FLEX-01",
            variant="CardioSync Rev B Flex", build_stage="Validation Passed",
            assigned_technician="Sarah Jenkins", completed_at=datetime.utcnow() - timedelta(days=15)
        )
        db.session.add(u4)
        db.session.flush()

        fw4 = FirmwareRelease(
            project_id=p4.id, target_subsystem="Nordic BLE Application Core", version="v1.1.0-beta",
            git_commit_hash="5019a823901bce47102938475869201928374650",
            binary_checksum="4a5c6d7e8f90123456789abcdef0123456789abcdef0123456789abcdef01234",
            release_type="Beta", release_notes="Implemented heart rate variability (HRV) calculation and BLE GATT battery service.",
            status="Testing", created_by="Liam O'Connor"
        )
        db.session.add(fw4)

        t_med_1 = SoftwareTestCase(project_id=p4.id, test_suite="BLE Protocol Verification", test_name="GATT Disconnection & Auto-Reconnect Recovery", expected_result="Reconnects to smartphone app within 1.5s of beacon return", result="Passed", is_critical=True, executed_by="Liam O'Connor", executed_at=datetime.utcnow() - timedelta(days=5))
        t_med_2 = SoftwareTestCase(project_id=p4.id, test_suite="Hardware-In-The-Loop (HIL)", test_name="ECG Signal Noise Rejection at 50Hz/60Hz Mains Hum", expected_result="Common-mode rejection ratio (CMRR) > 100 dB", result="Passed", is_critical=True, executed_by="Liam O'Connor", executed_at=datetime.utcnow() - timedelta(days=4))
        t_med_3 = SoftwareTestCase(project_id=p4.id, test_suite="Battery Life Stress Test", test_name="Continuous 72-Hour Stream on 90mAh Coin Cell", expected_result="Battery drain < 1.2mA average during continuous BLE broadcast", result="Failed", is_critical=True, executed_by="Liam O'Connor", executed_at=datetime.utcnow() - timedelta(days=2), execution_notes="Power profiling showed 2.4mA continuous draw due to DMA SPI driver remaining active during sleep.")
        db.session.add_all([t_med_1, t_med_2, t_med_3])

        # Commit all entities
        db.session.commit()

        # Generate initial activity logs for projects
        log1 = ActivityLog(project_id=p1.id, stage="Assembly", action="TRAVELER_IN_PROGRESS", description="Unit AMR-SN-2026-001 reached Power Rail Verification milestone.", performed_by="Sarah Jenkins")
        log2 = ActivityLog(project_id=p2.id, stage="Dispatch", action="SHIPMENT_DISPATCHED", description="Unit GW-SN-2026-101 dispatched to Apex Clean Energy via DHL Express.", performed_by="Sarah Jenkins")
        log3 = ActivityLog(project_id=p3.id, stage="Design", action="ECO_RAISED", description="Critical ECO-2026-019 raised for thermal isolation slot on PCB.", performed_by="David Chen")
        log4 = ActivityLog(project_id=p4.id, stage="Software", action="TEST_FAILED", description="Battery Life Stress Test failed (2.4mA excessive drain). Investigation underway.", performed_by="Liam O'Connor")
        db.session.add_all([log1, log2, log3, log4])
        db.session.commit()

        print("[Seed] Successfully seeded 4 complex engineering projects spanning all 5 stages!")

if __name__ == "__main__":
    seed_database()
