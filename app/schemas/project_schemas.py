from typing import Optional, List
from pydantic import BaseModel, Field

class ProjectCreateSchema(BaseModel):
    code: str = Field(..., min_length=2, max_length=32)
    name: str = Field(..., min_length=2, max_length=128)
    description: Optional[str] = None
    lead_engineer: str = Field("Lead Systems Engineer", max_length=64)
    priority: str = Field("High", max_length=32)
    target_date: Optional[str] = None
    budget: float = Field(0.0, ge=0.0)

class ProjectUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    lead_engineer: Optional[str] = None
    priority: Optional[str] = None
    health_status: Optional[str] = None
    target_date: Optional[str] = None
    budget: Optional[float] = None
    actual_cost: Optional[float] = None

class StageAdvanceSchema(BaseModel):
    target_stage: str
    override_checks: bool = False
    override_reason: Optional[str] = None
    performed_by: str = "Systems Lead"

class DesignDocCreateSchema(BaseModel):
    title: str
    doc_type: str
    subsystem: str
    version: str = "Rev 1.0"
    file_url: Optional[str] = None
    author: str
    review_notes: Optional[str] = None

class ECOCreateSchema(BaseModel):
    eco_number: str
    title: str
    description: str
    reason: str
    severity: str = "Medium"
    affected_subsystems: str
    requested_by: str

class BOMItemCreateSchema(BaseModel):
    part_number: str
    manufacturer_pn: str
    description: str
    category: str
    subsystem: str = "General"
    quantity_required: int = Field(1, ge=1)
    unit_cost: float = Field(0.0, ge=0.0)
    supplier_name: str
    lead_time_days: int = Field(7, ge=0)
    status: str = "PO Placed"
    po_reference: Optional[str] = None

class BOMItemUpdateSchema(BaseModel):
    quantity_received: Optional[int] = None
    status: Optional[str] = None
    tracking_number: Optional[str] = None
    lead_time_days: Optional[int] = None

class PhysicalUnitCreateSchema(BaseModel):
    serial_number: str
    batch_number: str = "BATCH-A"
    variant: str = "Rev B"
    assigned_technician: str = "Lead Assembly Tech"
    notes: Optional[str] = None

class AssemblyStepUpdateSchema(BaseModel):
    status: str
    technician: str
    measured_values: Optional[str] = None
    notes: Optional[str] = None

class DefectCreateSchema(BaseModel):
    defect_type: str
    severity: str = "Medium"
    description: str
    logged_by: str
    disposition: str = "Pending"

class FirmwareReleaseCreateSchema(BaseModel):
    target_subsystem: str
    version: str
    git_commit_hash: str
    binary_checksum: str
    release_type: str = "Release Candidate"
    release_notes: Optional[str] = None
    created_by: str

class TestCaseUpdateSchema(BaseModel):
    result: str
    executed_by: str
    execution_notes: Optional[str] = None

class FlashRecordCreateSchema(BaseModel):
    unit_serial: str
    firmware_version: str
    subsystem: str
    flashed_by: str
    verification_status: str = "Verified"
    log_output: Optional[str] = None

class QualityCertCreateSchema(BaseModel):
    unit_serial: str
    certificate_number: str
    inspector: str
    status: str = "Passed"
    hipot_test_passed: bool = True
    esd_protection_passed: bool = True
    thermal_stress_passed: bool = True
    compliance_standards: str = "CE, FCC Part 15 Class A, RoHS"
    calibration_data: Optional[str] = None
    notes: Optional[str] = None

class ShipmentCreateSchema(BaseModel):
    unit_serial: str
    destination_client: str
    destination_address: str
    carrier: str = "DHL Express"
    tracking_number: str
    ship_date: Optional[str] = None
    estimated_delivery: Optional[str] = None
    customs_declaration: Optional[str] = None

