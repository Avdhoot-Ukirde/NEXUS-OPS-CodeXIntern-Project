// Project Cockpit: 5-Stage Lifecycle Controller

let activeTab = 'design';
let projectId = null;

document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('project-cockpit-root');
  if (container) {
    projectId = parseInt(container.getAttribute('data-project-id'), 10);
    loadAllStageData();
    setupTabSwitching();
  }
});

function setupTabSwitching() {
  const tabBtns = document.querySelectorAll('.cockpit-tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active-tab'));
      btn.classList.add('active-tab');
      activeTab = btn.getAttribute('data-tab');
      document.querySelectorAll('.stage-panel').forEach(p => p.style.display = 'none');
      const targetPanel = document.getElementById(`panel-${activeTab}`);
      if (targetPanel) targetPanel.style.display = 'block';
    });
  });
}

async function loadAllStageData() {
  if (!projectId) return;
  loadDesignDocs();
  loadECOs();
  loadBOM();
  loadUnits();
  loadFirmwareAndTests();
  loadDispatchData();
  loadActivityLog();
}

// ---------------- STAGE 1: DESIGN ----------------
async function loadDesignDocs() {
  try {
    const res = await fetch(`/api/v1/projects/${projectId}/design-docs`);
    const docs = await res.json();
    const tableBody = document.getElementById('cad-docs-tbody');
    if (!tableBody) return;

    if (docs.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--text-dim); padding: 24px;">No CAD or Schematic documents registered yet.</td></tr>`;
      return;
    }

    tableBody.innerHTML = docs.map(d => {
      let statusBadge = d.status === 'Approved' 
        ? `<span style="color:#10b981; font-weight:600; background:rgba(16,185,129,0.1); padding:2px 8px; border-radius:4px;">✓ Approved</span>`
        : `<span style="color:#f59e0b; font-weight:600; background:rgba(245,158,11,0.1); padding:2px 8px; border-radius:4px;">Under Review</span>`;
      
      return `
        <tr>
          <td><strong style="color:var(--text-main);">${d.title}</strong><div style="font-size:0.75rem; color:var(--text-dim);">${d.subsystem}</div></td>
          <td><span style="font-family:monospace; background:var(--bg-primary); padding:2px 6px; border-radius:4px;">${d.version}</span></td>
          <td>${d.doc_type}</td>
          <td>${d.author}</td>
          <td>${statusBadge}</td>
          <td style="text-align:right;">
            ${d.status !== 'Approved' ? `
              <button class="nexus-btn nexus-btn-primary" style="padding:4px 10px; font-size:0.75rem;" onclick="approveDoc(${d.id}, 'Approved')">Approve Sign-off</button>
            ` : `
              <span style="font-size:0.75rem; color:var(--text-dim);">Signed by ${d.approved_by || 'Lead'}</span>
            `}
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error(err);
  }
}

async function approveDoc(docId, status) {
  try {
    const res = await fetch(`/api/v1/design-docs/${docId}/approve`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: status, approved_by: 'Chief Systems Engineer' })
    });
    if (res.ok) {
      showToast('Document sign-off updated!', 'success');
      loadDesignDocs();
      loadActivityLog();
    }
  } catch (err) {
    showToast('Failed to update sign-off', 'error');
  }
}

async function loadECOs() {
  try {
    const res = await fetch(`/api/v1/projects/${projectId}/ecos`);
    const ecos = await res.json();
    const list = document.getElementById('eco-list');
    if (!list) return;

    if (ecos.length === 0) {
      list.innerHTML = `<div style="text-align:center; color: var(--text-dim); padding: 20px;">No Engineering Change Orders raised.</div>`;
      return;
    }

    list.innerHTML = ecos.map(e => {
      let sevBg = e.severity === 'Critical' ? '#ef4444' : (e.severity === 'High' ? '#f59e0b' : '#3b82f6');
      let isResolved = e.status === 'Implemented' || e.status === 'Closed';
      return `
        <div style="background:var(--bg-primary); border:1px solid var(--border-subtle); border-radius:8px; padding:12px; margin-bottom:8px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="font-family:monospace; font-weight:700; color:#38bdf8;">${e.eco_number}</span>
              <span style="font-size:0.7rem; font-weight:600; background:${sevBg}20; color:${sevBg}; padding:2px 6px; border-radius:4px; border:1px solid ${sevBg}40;">${e.severity}</span>
              <strong style="font-size:0.9rem;">${e.title}</strong>
            </div>
            <div>
              ${!isResolved ? `
                <button class="nexus-btn nexus-btn-secondary" style="padding:3px 8px; font-size:0.75rem;" onclick="resolveECO(${e.id})">Mark Resolved</button>
              ` : `
                <span style="color:#10b981; font-size:0.75rem; font-weight:600;">✓ ${e.status}</span>
              `}
            </div>
          </div>
          <p style="font-size:0.8rem; color:var(--text-muted);">${e.description}</p>
          <div style="font-size:0.72rem; color:var(--text-dim); margin-top:4px;">Affected: ${e.affected_subsystems} | Raised by: ${e.requested_by}</div>
        </div>
      `;
    }).join('');
  } catch (err) {
    console.error(err);
  }
}

async function resolveECO(ecoId) {
  try {
    const res = await fetch(`/api/v1/ecos/${ecoId}/resolve`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'Implemented', approved_by: 'Chief Systems Architect' })
    });
    if (res.ok) {
      showToast('ECO resolved & implemented!', 'success');
      loadECOs();
      loadActivityLog();
    }
  } catch (err) {
    showToast('Failed to resolve ECO', 'error');
  }
}

// ---------------- STAGE 2: PURCHASE & BOM ----------------
async function loadBOM() {
  try {
    const res = await fetch(`/api/v1/projects/${projectId}/bom`);
    const data = await res.json();
    const items = data.items || [];
    const metrics = data.metrics || {};

    const readinessEl = document.getElementById('bom-metric-readiness');
    const costEl = document.getElementById('bom-metric-cost');
    const partsEl = document.getElementById('bom-metric-parts');
    const tbody = document.getElementById('bom-tbody');

    if (readinessEl) readinessEl.textContent = `${metrics.readiness_pct}%`;
    if (costEl) costEl.textContent = `$${(metrics.total_bom_cost || 0).toLocaleString()}`;
    if (partsEl) partsEl.textContent = `${metrics.delivered_count || 0} / ${metrics.total_line_items || 0}`;

    if (!tbody) return;
    if (items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color: var(--text-dim); padding: 24px;">Bill of Materials is empty. Add components to begin procurement.</td></tr>`;
      return;
    }

    tbody.innerHTML = items.map(item => {
      let statusColor = item.status === 'Delivered' ? '#10b981' : (item.status === 'Backordered' ? '#ef4444' : '#f59e0b');
      let riskPill = item.risk_level === 'High' 
        ? `<span style="background:rgba(239,68,68,0.15); color:#ef4444; padding:2px 6px; border-radius:4px; font-size:0.7rem;">High Risk</span>` 
        : `<span style="color:var(--text-dim); font-size:0.7rem;">Nominal</span>`;

      return `
        <tr>
          <td><strong style="color:var(--text-main); font-family:monospace;">${item.manufacturer_pn}</strong><div style="font-size:0.72rem; color:var(--text-dim);">${item.description}</div></td>
          <td><span style="font-size:0.75rem; background:var(--bg-primary); padding:2px 6px; border-radius:4px;">${item.category}</span></td>
          <td>${item.quantity_received} / <strong>${item.quantity_required}</strong></td>
          <td>$${item.unit_cost.toFixed(2)}</td>
          <td><strong style="color:#38bdf8;">$${item.total_cost.toFixed(2)}</strong></td>
          <td>${item.supplier_name} <div style="font-size:0.72rem; color:var(--text-dim);">${item.lead_time_days} days lead</div></td>
          <td>
            <span style="font-weight:600; color:${statusColor}; font-size:0.75rem;">${item.status}</span>
            <div>${riskPill}</div>
          </td>
          <td style="text-align:right;">
            ${item.status !== 'Delivered' ? `
              <button class="nexus-btn nexus-btn-primary" style="padding:3px 8px; font-size:0.72rem;" onclick="markBOMDelivered(${item.id})">Mark Delivered</button>
            ` : `
              <span style="color:#10b981; font-size:0.75rem;">✓ Stocked</span>
            `}
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error(err);
  }
}

async function markBOMDelivered(itemId) {
  try {
    const res = await fetch(`/api/v1/bom-items/${itemId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'Delivered' })
    });
    if (res.ok) {
      showToast('Component marked as delivered & received!', 'success');
      loadBOM();
      loadActivityLog();
    }
  } catch (err) {
    showToast('Failed to update component status', 'error');
  }
}

// ---------------- STAGE 3: ASSEMBLY & TRAVELER ----------------
async function loadUnits() {
  try {
    const res = await fetch(`/api/v1/projects/${projectId}/units`);
    const units = await res.json();
    const container = document.getElementById('assembly-units-container');
    if (!container) return;

    if (units.length === 0) {
      container.innerHTML = `<div style="text-align:center; color: var(--text-dim); padding: 32px;">No physical build units registered. Register a serial number unit to start manufacturing traveler.</div>`;
      return;
    }

    container.innerHTML = units.map(u => {
      const steps = u.traveler_steps || [];
      const passedSteps = steps.filter(s => s.status === 'Passed').length;
      const progressPct = steps.length ? Math.round((passedSteps / steps.length) * 100) : 0;

      const stepsHtml = steps.map(s => {
        let stColor = s.status === 'Passed' ? '#10b981' : (s.status === 'Failed' ? '#ef4444' : (s.status === 'In Progress' ? '#38bdf8' : 'var(--text-dim)'));
        let icon = s.status === 'Passed' ? '✓' : (s.status === 'Failed' ? '✕' : (s.status === 'In Progress' ? '⚙' : '○'));
        
        return `
          <div style="background:var(--bg-primary); border:1px solid var(--border-subtle); border-radius:6px; padding:10px; margin-bottom:8px;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:8px;">
              <div>
                <div style="display:flex; align-items:center; gap:6px;">
                  <span style="color:${stColor}; font-weight:700;">${icon} Step ${s.step_order}:</span>
                  <strong style="font-size:0.85rem; color:var(--text-main);">${s.name}</strong>
                  <span style="font-size:0.7rem; color:${stColor}; font-weight:600; text-transform:uppercase;">[${s.status}]</span>
                </div>
                <div style="font-size:0.75rem; color:var(--text-muted); margin-top:2px;">${s.inspection_criteria || ''}</div>
                ${s.measured_values ? `<div style="font-size:0.75rem; color:#38bdf8; font-family:monospace; margin-top:4px;">Readings: ${s.measured_values}</div>` : ''}
              </div>
              <div style="display:flex; gap:4px;">
                ${s.status !== 'Passed' ? `
                  <button class="nexus-btn nexus-btn-primary" style="padding:2px 8px; font-size:0.7rem;" onclick="openStepModal(${s.id}, '${s.name.replace(/'/g, "\\'")}')">Log Reading / Pass</button>
                ` : `
                  <span style="font-size:0.7rem; color:#10b981;">✓ Verified</span>
                `}
              </div>
            </div>
          </div>
        `;
      }).join('');

      return `
        <div class="nexus-card" style="padding:16px; margin-bottom:16px;">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:12px; border-bottom:1px solid var(--border-subtle); padding-bottom:10px;">
            <div>
              <span style="font-family:monospace; font-size:0.9rem; font-weight:700; color:#38bdf8;">${u.serial_number}</span>
              <span style="font-size:0.75rem; color:var(--text-muted); margin-left:8px;">Batch: ${u.batch_number} (${u.variant})</span>
            </div>
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="font-size:0.75rem; font-weight:600; color:#38bdf8;">${progressPct}% Completed</span>
              <a href="/units/${u.id}/traveler" target="_blank" class="nexus-btn nexus-btn-secondary" style="padding:3px 8px; font-size:0.72rem; text-decoration:none;">Print Traveler Sheet 🖨️</a>
              <button class="nexus-btn nexus-btn-danger" style="padding:3px 8px; font-size:0.72rem;" onclick="openDefectModal(${u.id}, '${u.serial_number}')">+ Defect</button>
            </div>
          </div>
          <div style="margin-top:8px;">
            ${stepsHtml}
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    console.error(err);
  }
}

let activeStepId = null;
function openStepModal(stepId, stepName) {
  activeStepId = stepId;
  const nameEl = document.getElementById('step-modal-name');
  if (nameEl) nameEl.textContent = stepName;
  openModal('modal-update-step');
}

async function handleUpdateStep(e) {
  e.preventDefault();
  if (!activeStepId) return;
  const form = e.target;
  const status = form.status.value;
  const readings = form.measured_values.value.trim();
  const tech = form.technician.value.trim() || 'Assembly Tech';

  try {
    const res = await fetch(`/api/v1/assembly-steps/${activeStepId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        status: status,
        technician: tech,
        measured_values: readings
      })
    });
    if (res.ok) {
      showToast('Traveler milestone recorded!', 'success');
      closeModal('modal-update-step');
      form.reset();
      loadUnits();
      loadActivityLog();
    }
  } catch (err) {
    showToast('Failed to update traveler step', 'error');
  }
}

let activeDefectUnitId = null;
function openDefectModal(unitId, serial) {
  activeDefectUnitId = unitId;
  const titleEl = document.getElementById('defect-modal-serial');
  if (titleEl) titleEl.textContent = serial;
  openModal('modal-log-defect');
}

async function handleLogDefect(e) {
  e.preventDefault();
  if (!activeDefectUnitId) return;
  const form = e.target;
  const payload = {
    defect_type: form.defect_type.value,
    severity: form.severity.value,
    description: form.description.value.trim(),
    logged_by: form.logged_by.value.trim() || 'Quality Tech'
  };

  try {
    const res = await fetch(`/api/v1/units/${activeDefectUnitId}/defects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      showToast('Assembly defect logged & rework queued', 'warning');
      closeModal('modal-log-defect');
      form.reset();
      loadUnits();
      loadActivityLog();
    }
  } catch (err) {
    showToast('Failed to log defect', 'error');
  }
}

// ---------------- STAGE 4: SOFTWARE & TESTS ----------------
async function loadFirmwareAndTests() {
  try {
    // Load firmware releases & flashing
    const fwRes = await fetch(`/api/v1/projects/${projectId}/firmware`);
    const fwData = await fwRes.json();
    const releases = fwData.releases || [];
    const flashes = fwData.flashes || [];

    const fwContainer = document.getElementById('firmware-releases-container');
    if (fwContainer) {
      if (releases.length === 0) {
        fwContainer.innerHTML = `<div style="text-align:center; color: var(--text-dim); padding: 16px;">No firmware releases registered.</div>`;
      } else {
        fwContainer.innerHTML = releases.map(r => `
          <div style="background:var(--bg-primary); border:1px solid var(--border-subtle); border-radius:6px; padding:10px; margin-bottom:8px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div>
                <strong style="color:#34d399; font-size:0.95rem;">${r.version}</strong>
                <span style="font-size:0.75rem; color:var(--text-muted); margin-left:6px;">(${r.target_subsystem})</span>
              </div>
              <span style="font-size:0.7rem; font-family:monospace; background:var(--bg-secondary); padding:2px 6px; border-radius:4px;">Git: ${r.git_commit_hash.substring(0, 7)}</span>
            </div>
            <div style="font-size:0.75rem; color:var(--text-dim); margin-top:4px;">${r.release_notes || 'No release notes'}</div>
            <div style="font-size:0.7rem; color:var(--text-dim); font-family:monospace; margin-top:2px;">SHA-256: ${r.binary_checksum.substring(0, 24)}...</div>
          </div>
        `).join('');
      }
    }

    // Load software test cases
    const testRes = await fetch(`/api/v1/projects/${projectId}/tests`);
    const testData = await testRes.json();
    const tests = testData.tests || [];
    const metrics = testData.metrics || {};

    const passRateEl = document.getElementById('sw-metric-passrate');
    const testsEl = document.getElementById('sw-metric-tests');
    const tbody = document.getElementById('software-tests-tbody');

    if (passRateEl) passRateEl.textContent = `${metrics.pass_pct}%`;
    if (testsEl) testsEl.textContent = `${metrics.passed} / ${metrics.total_tests}`;

    if (!tbody) return;
    if (tests.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--text-dim); padding: 24px;">No test cases found.</td></tr>`;
      return;
    }

    tbody.innerHTML = tests.map(t => {
      let resColor = t.result === 'Passed' ? '#10b981' : (t.result === 'Failed' ? '#ef4444' : 'var(--text-dim)');
      let critBadge = t.is_critical 
        ? `<span style="color:#ef4444; font-size:0.7rem; font-weight:600; background:rgba(239,68,68,0.1); padding:2px 6px; border-radius:4px;">CRITICAL</span>` 
        : `<span style="color:var(--text-dim); font-size:0.7rem;">Normal</span>`;

      return `
        <tr>
          <td><strong style="color:var(--text-main);">${t.test_name}</strong><div style="font-size:0.72rem; color:var(--text-dim);">${t.test_suite}</div></td>
          <td>${critBadge}</td>
          <td style="font-size:0.75rem; color:var(--text-muted);">${t.expected_result}</td>
          <td><span style="font-weight:700; color:${resColor}; font-size:0.8rem;">${t.result}</span></td>
          <td style="font-size:0.75rem; color:var(--text-dim); font-family:monospace;">${t.execution_notes || '-'}</td>
          <td style="text-align:right;">
            <div style="display:inline-flex; gap:4px;">
              <button class="nexus-btn" style="background:rgba(16,185,129,0.2); color:#10b981; padding:2px 8px; font-size:0.72rem;" onclick="setTestResult(${t.id}, 'Passed')">Pass ✓</button>
              <button class="nexus-btn" style="background:rgba(239,68,68,0.2); color:#ef4444; padding:2px 8px; font-size:0.72rem;" onclick="setTestResult(${t.id}, 'Failed')">Fail ✕</button>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error(err);
  }
}

async function setTestResult(testId, result) {
  let notes = prompt(`Enter execution notes for ${result} verdict:`, result === 'Passed' ? 'Nominal telemetry verified on bench test.' : 'Failure detected during execution.');
  if (notes === null) return;

  try {
    const res = await fetch(`/api/v1/tests/${testId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        result: result,
        executed_by: 'Embedded Test Engineer',
        execution_notes: notes
      })
    });
    if (res.ok) {
      showToast(`Test marked as ${result}!`, result === 'Passed' ? 'success' : 'warning');
      loadFirmwareAndTests();
      loadActivityLog();
    }
  } catch (err) {
    showToast('Failed to update test', 'error');
  }
}

// ---------------- STAGE 5: DISPATCH ----------------
async function loadDispatchData() {
  try {
    const res = await fetch(`/api/v1/projects/${projectId}/dispatch`);
    const data = await res.json();
    const certs = data.certifications || [];
    const packaging = data.packaging_items || [];
    const shipments = data.shipments || [];

    // Render QA Certs
    const certsContainer = document.getElementById('dispatch-certs-container');
    if (certsContainer) {
      if (certs.length === 0) {
        certsContainer.innerHTML = `<div style="text-align:center; color: var(--text-dim); padding: 16px;">No QA certification issued yet.</div>`;
      } else {
        certsContainer.innerHTML = certs.map(c => `
          <div style="background:var(--bg-primary); border:1px solid #10b981; border-radius:8px; padding:12px; margin-bottom:8px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div>
                <span style="font-family:monospace; font-weight:700; color:#10b981;">${c.certificate_number}</span>
                <span style="font-size:0.8rem; margin-left:8px; color:var(--text-muted);">Unit: <strong>${c.unit_serial}</strong></span>
              </div>
              <span style="font-size:0.75rem; color:#10b981; font-weight:600;">✓ ${c.status}</span>
            </div>
            <div style="font-size:0.75rem; color:var(--text-dim); margin-top:4px;">Standards: ${c.compliance_standards}</div>
            <div style="font-size:0.75rem; color:var(--text-muted); margin-top:2px;">Calibration: ${c.calibration_data || 'N/A'}</div>
          </div>
        `).join('');
      }
    }

    // Render Packaging Items
    const pkgList = document.getElementById('packaging-checklist-container');
    if (pkgList) {
      if (packaging.length === 0) {
        pkgList.innerHTML = `<div style="text-align:center; color: var(--text-dim); padding: 16px;">No packaging items defined.</div>`;
      } else {
        pkgList.innerHTML = packaging.map(p => `
          <div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-primary); border:1px solid var(--border-subtle); border-radius:6px; padding:10px; margin-bottom:6px;">
            <div style="display:flex; align-items:center; gap:10px;">
              <input type="checkbox" ${p.is_verified ? 'checked' : ''} style="cursor:pointer; width:18px; height:18px;" onchange="togglePackagingItem(${p.id})">
              <span style="${p.is_verified ? 'text-decoration:line-through; color:var(--text-dim);' : 'color:var(--text-main); font-weight:500; font-size:0.85rem;'}">${p.item_name}</span>
            </div>
            <span style="font-size:0.72rem; color:var(--text-dim);">${p.is_verified ? `Verified by ${p.checked_by || 'QA'}` : 'Pending'}</span>
          </div>
        `).join('');
      }
    }

    // Render Shipments
    const shipmentsContainer = document.getElementById('dispatch-shipments-container');
    if (shipmentsContainer) {
      if (shipments.length === 0) {
        shipmentsContainer.innerHTML = `<div style="text-align:center; color: var(--text-dim); padding: 16px;">No shipment booked yet.</div>`;
      } else {
        shipmentsContainer.innerHTML = shipments.map(s => `
          <div style="background:var(--bg-primary); border:1px solid var(--border-subtle); border-radius:8px; padding:12px; margin-bottom:8px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div>
                <strong style="color:var(--text-main); font-size:0.9rem;">${s.destination_client}</strong>
                <div style="font-size:0.75rem; color:var(--text-muted);">${s.destination_address}</div>
              </div>
              <span style="font-size:0.75rem; font-weight:600; color:#c084fc; background:rgba(192,132,252,0.15); padding:2px 8px; border-radius:4px;">${s.delivery_status}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:8px; font-size:0.75rem; color:var(--text-dim);">
              <span>Carrier: <strong>${s.carrier}</strong></span>
              <span>Tracking: <strong style="font-family:monospace; color:#38bdf8;">${s.tracking_number}</strong></span>
            </div>
          </div>
        `).join('');
      }
    }
  } catch (err) {
    console.error(err);
  }
}

async function togglePackagingItem(itemId) {
  try {
    const res = await fetch(`/api/v1/packaging-items/${itemId}/toggle`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ checked_by: 'QA Logistics Inspector' })
    });
    if (res.ok) {
      loadDispatchData();
      loadActivityLog();
    }
  } catch (err) {
    showToast('Failed to toggle packaging item', 'error');
  }
}

// ---------------- AUDIT TRAIL ----------------
async function loadActivityLog() {
  try {
    const res = await fetch(`/api/v1/projects/${projectId}/activity`);
    const logs = await res.json();
    const container = document.getElementById('activity-log-timeline');
    if (!container) return;

    if (logs.length === 0) {
      container.innerHTML = `<div style="text-align:center; color: var(--text-dim); padding: 20px;">No activity logged yet.</div>`;
      return;
    }

    container.innerHTML = logs.map(l => {
      const dt = new Date(l.timestamp).toLocaleString();
      return `
        <div style="position:relative; padding-left:24px; padding-bottom:16px; border-left:2px solid var(--border-accent);">
          <div style="position:absolute; left:-6px; top:0; width:10px; height:10px; border-radius:50%; background:#38bdf8;"></div>
          <div style="font-size:0.75rem; color:var(--text-dim);">${dt} • <strong style="color:#38bdf8;">${l.stage}</strong> by <em>${l.performed_by}</em></div>
          <div style="font-size:0.85rem; color:var(--text-main); margin-top:2px;">${l.description}</div>
          ${l.details ? `<div style="font-size:0.75rem; color:var(--text-dim); font-family:monospace; margin-top:2px;">${l.details}</div>` : ''}
        </div>
      `;
    }).join('');
  } catch (err) {
    console.error(err);
  }
}

// Export Full Project Data JSON
async function exportProjectJSON() {
  if (!projectId) return;
  try {
    const res = await fetch(`/api/v1/analytics/export/${projectId}`);
    const data = await res.json();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `project_${data.code}_export.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Project report exported as JSON!', 'success');
  } catch (err) {
    showToast('Failed to export project', 'error');
  }
}

