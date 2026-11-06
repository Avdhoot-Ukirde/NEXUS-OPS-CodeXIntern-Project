# NEXUS-OPS | Hardware & Software Integrated Project Management Platform

**NEXUS-OPS** is a production-grade, full-stack platform built specifically to solve the challenge of **fragmented project tracking** across integrated engineering systems (Robotics, IoT, Aerospace, Automotive, Industrial Automation, and Medical Devices).

---

## 🎯 The Core Problem: Fragmented Project Tracking

In integrated hardware-software engineering, teams typically operate in siloed tools:
- **Hardware teams** work in Altium / SolidWorks / PLM.
- **Supply chain & purchasing** manage lead times and MOQ in ERPs and spreadsheets.
- **Manufacturing & shop floor** track physical builds on paper travelers and torque logs.
- **Embedded & software teams** release firmware and run CI/CD in Git/Jira.
- **Operations & QA** handle calibration, compliance certifications, and freight carriers.

When a schematic updates, procurement buys the wrong resistors; assembly builds obsolete boards; firmware crashes on unexpected pinouts; and uncalibrated units ship to clients.

**NEXUS-OPS unites the complete lifecycle in a single platform**, enforcing prerequisite stage gates so hardware and software move in lockstep.

---

## 🏗️ The 5 Integrated Engineering Lifecycle Stages

```
   ┌───────────┐      ┌───────────┐      ┌───────────┐      ┌───────────┐      ┌───────────┐
   │ 1. DESIGN │ ───► │2. PURCHASE│ ───► │3. ASSEMBLY│ ───► │4. SOFTWARE│ ───► │5. DISPATCH│
   └───────────┘      └───────────┘      └───────────┘      └───────────┘      └───────────┘
     CAD & Revs         BOM Readiness      Shop Traveler      Firmware Flashing   Final QA Cert
     Schematics         Supplier Lead      DMM & Torque       HIL Test Suites     Packaging Check
     ECO Tracker        PO Status          Defect Logging     Safety Interlocks   Carrier Logistics
```

### 1. Design Stage (CAD / Schematic Approvals & Documentation)
- **CAD & Schematic Registry**: Tracks schematic revisions (`Rev 1.0`, `Rev 2.1`), CAD 3D models (`.step`), PCB gerbers, and wiring harnesses.
- **Engineering Sign-off Workflow**: Reviewers inspect layer stackups, differential pairs, and thermal planes before granting formal approval.
- **Engineering Change Orders (ECO)**: Tracks ECO numbers (e.g., `ECO-2026-012`), root causes (*Component Obsolescence*, *Thermal Dissipation*, *Signal Integrity*), severity (*Critical*, *High*, *Medium*), and affected subsystems.
- *Stage Gate Rule*: Projects cannot advance to Procurement without at least one approved schematic and zero open Critical ECOs.

### 2. Purchase Stage (Procurement, Supplier Tracking & BOM Readiness)
- **Interactive Bill of Materials (BOM)**: Categorized catalog of Microcontrollers, Sensors, Power ICs, Passives, Mechanical Enclosures, and Connectors.
- **Supplier & Lead Time Risk Scoring**: Automatically flags components with lead times > 28 days as **High Risk**, tracking purchase order numbers and carrier tracking numbers.
- **BOM Readiness KPI**: Live calculation of $\frac{\text{Received Parts}}{\text{Total Required Parts}} \times 100\%$.
- *Stage Gate Rule*: Projects require $\ge 80\%$ BOM readiness before moving to physical assembly.

### 3. Assembly Stage (Physical Build Progress & Component Validation)
- **Physical Unit Registry**: Serial numbers (e.g. `AMR-SN-2026-001`), batch identifiers, and hardware variants.
- **6-Step Shop-Floor Traveler**:
  1. *SMT Stencil & Pick-and-Place Assembly* (IPC-A-610 Class 2)
  2. *Automated Optical Inspection (AOI) & X-ray Reflow Verification*
  3. *Power Rail Voltage & Short-Circuit Verification* (3.3V, 5.0V, 12V tolerance checks)
  4. *Mechanical Enclosure & Heatsink Integration* (Torque verification)
  5. *Wiring Harness Routing & Strain Relief Test*
  6. *Subsystem Burn-in & Thermal Soak Test*
- **Defect Non-Conformance Logging**: Tracks cold solder joints, solder bridges, or damaged harnesses with severity and disposition (*Reworked & Retested*, *Scrapped*).
- **Printable Traveler Sheet**: Instant 1-click printable shop-floor traveler with technician signature and QA stamp blocks (`/units/<id>/traveler`).

### 4. Software Stage (Firmware Releases & Testing Checklists)
- **Firmware Release Artifacts**: Tracks SemVer versions (`v1.4.2-rc1`), 40-character Git commit SHAs, target subsystems (MCU, DSP, Linux SBC), and cryptographic SHA-256 binary checksums.
- **SWD / JTAG Flashing Records**: Logs target unit serial number, flashed firmware version, technician, and CRC verification status.
- **Hardware-In-The-Loop (HIL) & Safety Test Checklists**:
  - CAN Bus / CANopen jitter & bus load benchmarks
  - E-Stop relay open-circuit latency (< 15ms)
  - Emergency watchdog recovery
  - Battery profiling and thermal throttling tests
- *Stage Gate Rule*: All critical safety and HIL tests must be in `Passed` status to transition to Dispatch.

### 5. Dispatch Stage (Final QA, Packaging & Shipping Details)
- **Quality Assurance Compliance Certification**: Records Hi-Pot (dielectric withstand), ESD strike immunity, thermal chamber burn-in, calibration offsets, and regulatory standards (*FCC Part 15, CE Mark, RoHS*).
- **Packaging Checklist**: Verifies anti-static ESD shielding bags, regional AC power adapters, mounting brackets, calibration certs, and tamper-evident seals.
- **Carrier Logistics Integration**: Tracks destination client, address, carrier (*DHL Express, FedEx Priority, Freight*), and tracking numbers with live delivery statuses.

---

## ⚡ Stage-Gate Enforcement Engine

NEXUS-OPS incorporates a built-in gate evaluation engine (`StageGateService`) that audits project readiness prior to any stage transition:
- **Automated Validation**: Displays checklist items satisfying or violating prerequisites.
- **Engineering Overrides**: In agile prototype cycles, authorized leads can override gate blocks by providing a mandatory **Audit Justification & Risk Mitigation Plan**.
- **Unified Audit Trail**: Every stage transition, approval, defect logged, or test verdict is immutably timestamped in the project activity history.

---

## 🛠️ Technology Architecture

- **Backend**: Python 3.13 / Flask 3.1 WSGI Application
- **ORM & Data Layer**: SQLAlchemy 2.0 with SQLite (zero external setup required; PostgreSQL compatible)
- **Schema Validation**: Pydantic v2 schemas for all payload validation
- **Frontend**: Clean Vanilla JavaScript SPA architecture, custom responsive CSS design system (engineered for aerospace/industrial dark mode), zero node build step required.
- **Testing**: Automated Python unit & integration test suite (`tests/`).

---

## 🚀 Quickstart Guide

### 1. Requirements
- Python 3.10+ (tested with Python 3.13)
- No Node.js or npm required!

### 2. Run the Application
```bash
# Optional: Seed the database with 4 realistic engineering projects
python seed_data.py

# Launch the server
python run.py
```

The server starts at: **http://127.0.0.1:5000**

### 3. Running Automated Tests
```bash
python -m unittest discover -s tests
```

---

## 📡 RESTful API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/projects` | `GET` | List projects (supports `?stage=`, `?health=`, `?q=`) |
| `/api/v1/projects` | `POST` | Initialize a new engineering project |
| `/api/v1/projects/<id>` | `GET` | Get project detail and summary metrics |
| `/api/v1/projects/<id>/gate-status` | `GET` | Evaluate stage gate prerequisites |
| `/api/v1/projects/<id>/advance-stage`| `POST` | Advance lifecycle stage (with override support) |
| `/api/v1/projects/<id>/design-docs` | `GET`, `POST` | List and register CAD / Schematics |
| `/api/v1/design-docs/<id>/approve` | `PUT` | Approve or reject design documentation |
| `/api/v1/projects/<id>/ecos` | `GET`, `POST` | List and raise Engineering Change Orders |
| `/api/v1/ecos/<id>/resolve` | `PUT` | Resolve and implement ECO |
| `/api/v1/projects/<id>/bom` | `GET`, `POST` | List Bill of Materials and add components |
| `/api/v1/bom-items/<id>` | `PUT`, `DELETE`| Update delivery status or remove component |
| `/api/v1/projects/<id>/units` | `GET`, `POST` | Register physical build units with 6-step traveler |
| `/api/v1/assembly-steps/<id>` | `PUT` | Record milestone status and DMM/torque readings |
| `/api/v1/units/<id>/defects` | `POST` | Log non-conformance assembly defect |
| `/api/v1/projects/<id>/firmware` | `GET`, `POST` | List and tag SemVer firmware releases |
| `/api/v1/projects/<id>/tests` | `GET`, `POST` | List and add HIL/Safety test cases |
| `/api/v1/tests/<id>` | `PUT` | Update test execution verdict (`Passed` / `Failed`) |
| `/api/v1/projects/<id>/dispatch` | `GET` | Get QA certs, packaging items, and shipments |
| `/api/v1/projects/<id>/qa-cert` | `POST` | Issue regulatory QA certification |
| `/api/v1/packaging-items/<id>/toggle`| `PUT`| Toggle packaging checklist item |
| `/api/v1/projects/<id>/shipments` | `POST` | Book dispatch carrier shipment |
| `/api/v1/analytics/dashboard` | `GET` | Global executive metrics and pipeline counts |
| `/api/v1/analytics/export/<id>` | `GET` | Export full project traveler and stage archive (JSON) |

---

## 🏢 Included Sample Projects (Pre-loaded)

1. **AMR Titan 500 Heavy-Payload Logistics Rover (`PRJ-ROBOT-01`)**:
   - Current Stage: **Assembly**
   - Autonomous mobile robot with dual-LiDAR, STM32 safety PLC, and CANopen motor controllers. Physical unit `AMR-SN-2026-001` actively undergoing power rail voltage checks.
2. **Smart Grid Edge Gateway Pro (`PRJ-IOT-09`)**:
   - Current Stage: **Dispatch**
   - Ruggedized DIN-rail gateway with FCC/CE certifications, verified packaging, and shipment actively in transit via DHL Express.
3. **ApexFlight Tri-Redundant Drone Flight Avionics (`PRJ-AERO-04`)**:
   - Current Stage: **Design**
   - High-reliability avionics stack with an open Critical ECO regarding PCB thermal dissipation.
4. **CardioSync Clinical Continuous Vital Monitor (`PRJ-MED-02`)**:
   - Current Stage: **Software**
   - BLE 5.3 and ECG wearable patch with HIL tests in progress (investigating battery sleep current non-conformance).

