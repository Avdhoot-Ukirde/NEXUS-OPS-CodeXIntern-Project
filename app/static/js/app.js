// NEXUS-OPS Core Dashboard Application

let currentProjects = [];
let selectedProjectId = null;

document.addEventListener('DOMContentLoaded', () => {
  loadDashboardData();
  loadProjects();
  setupEventListeners();
});

function setupEventListeners() {
  const searchInput = document.getElementById('search-input');
  const stageFilter = document.getElementById('filter-stage');
  const healthFilter = document.getElementById('filter-health');

  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => loadProjects(), 300);
    });
  }

  if (stageFilter) stageFilter.addEventListener('change', () => loadProjects());
  if (healthFilter) healthFilter.addEventListener('change', () => loadProjects());

  // Create Project Form
  const createForm = document.getElementById('form-create-project');
  if (createForm) {
    createForm.addEventListener('submit', handleCreateProject);
  }

  // Advance Stage Form
  const advanceForm = document.getElementById('form-advance-stage');
  if (advanceForm) {
    advanceForm.addEventListener('submit', handleAdvanceStage);
  }
}

async function loadDashboardData() {
  try {
    const res = await fetch('/api/v1/analytics/dashboard');
    if (!res.ok) return;
    const data = await res.json();
    renderDashboardKPIs(data);
  } catch (err) {
    console.error('Failed to load dashboard metrics:', err);
  }
}

function renderDashboardKPIs(data) {
  const totalEl = document.getElementById('kpi-total-projects');
  const readinessEl = document.getElementById('kpi-bom-readiness');
  const passRateEl = document.getElementById('kpi-test-passrate');
  const budgetEl = document.getElementById('kpi-total-budget');

  if (totalEl) totalEl.textContent = data.total_projects;
  if (readinessEl) readinessEl.textContent = `${data.procurement_kpis.readiness_pct}%`;
  if (passRateEl) passRateEl.textContent = `${data.software_kpis.pass_rate_pct}%`;
  if (budgetEl) {
    const spend = (data.financials.total_actual / 1000).toFixed(1);
    const budget = (data.financials.total_budget / 1000).toFixed(1);
    budgetEl.textContent = `$${spend}k / $${budget}k`;
  }

  // Render funnel pill counts if present
  const stageDist = data.stage_distribution;
  if (stageDist) {
    for (const [stg, count] of Object.entries(stageDist)) {
      const el = document.getElementById(`funnel-count-${stg.toLowerCase()}`);
      if (el) el.textContent = count;
    }
  }
}

async function loadProjects() {
  const searchInput = document.getElementById('search-input');
  const stageFilter = document.getElementById('filter-stage');
  const healthFilter = document.getElementById('filter-health');

  let url = '/api/v1/projects?';
  const params = new URLSearchParams();

  if (searchInput && searchInput.value.trim()) params.append('q', searchInput.value.trim());
  if (stageFilter && stageFilter.value) params.append('stage', stageFilter.value);
  if (healthFilter && healthFilter.value) params.append('health', healthFilter.value);

  try {
    const res = await fetch(url + params.toString());
    if (!res.ok) throw new Error('Failed to fetch projects');
    currentProjects = await res.json();
    renderProjectsList(currentProjects);
  } catch (err) {
    console.error(err);
    showToast('Failed to load projects', 'error');
  }
}

function renderProjectsList(projects) {
  const container = document.getElementById('projects-container');
  if (!container) return;

  if (projects.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 48px 16px; color: var(--text-dim);">
        <p style="font-size: 1.1rem; margin-bottom: 8px;">No projects found matching current criteria.</p>
        <button class="nexus-btn nexus-btn-primary" onclick="openModal('modal-create-project')">+ Create New Engineering Project</button>
      </div>
    `;
    return;
  }

  const STAGES = ['Design', 'Purchase', 'Assembly', 'Software', 'Dispatch', 'Completed'];

  container.innerHTML = projects.map(p => {
    const summary = p.summary || {};
    const currStageIdx = STAGES.indexOf(p.current_stage);
    
    // Health status class
    let healthClass = 'health-on-track';
    let pulseColor = 'green';
    if (p.health_status === 'At Risk') { healthClass = 'health-at-risk'; pulseColor = 'amber'; }
    else if (p.health_status === 'Blocked') { healthClass = 'health-blocked'; pulseColor = 'red'; }
    else if (p.health_status === 'Delayed') { healthClass = 'health-delayed'; pulseColor = 'amber'; }

    // Stage pills bar
    const stageBarHtml = STAGES.slice(0, 5).map((stg, i) => {
      let isDone = i < currStageIdx || p.current_stage === 'Completed';
      let isCurrent = stg === p.current_stage;
      let stepStyle = isCurrent 
        ? 'font-weight: 700; color: #ffffff; border-bottom: 2px solid #3b82f6; padding-bottom: 2px;' 
        : (isDone ? 'color: #10b981;' : 'color: var(--text-dim);');
      let icon = isDone ? '✓' : `${i + 1}.`;
      return `<span style="font-size: 0.75rem; ${stepStyle}">${icon} ${stg}</span>`;
    }).join('<span style="color: var(--border-accent); font-size: 0.75rem;">→</span>');

    return `
      <div class="nexus-card" style="padding: 20px; margin-bottom: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px; margin-bottom: 14px;">
          <div>
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
              <span style="font-family: monospace; font-size: 0.85rem; font-weight: 700; background: var(--bg-tertiary); padding: 3px 8px; border-radius: 4px; border: 1px solid var(--border-subtle); color: #38bdf8;">${p.code}</span>
              <h3 style="font-size: 1.15rem; font-weight: 600; color: var(--text-main);">
                <a href="/projects/${p.id}" style="color: inherit; text-decoration: none;" onmouseover="this.style.color='#38bdf8'" onmouseout="this.style.color='inherit'">${p.name}</a>
              </h3>
            </div>
            <p style="color: var(--text-muted); font-size: 0.85rem; max-width: 650px; line-height: 1.4;">${p.description || 'No description provided.'}</p>
          </div>

          <div style="display: flex; align-items: center; gap: 10px;">
            <span class="badge-health ${healthClass}">
              <span class="pulse-dot ${pulseColor}"></span>
              ${p.health_status}
            </span>
            <span class="stage-pill ${p.current_stage.toLowerCase()}">${p.current_stage}</span>
          </div>
        </div>

        <!-- 5-Stage Visual Progression Line -->
        <div style="background: var(--bg-primary); padding: 8px 14px; border-radius: 8px; border: 1px solid var(--border-subtle); margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-dim); margin-right: 4px;">Stage Progression:</span>
            ${stageBarHtml}
          </div>
          <div style="font-size: 0.8rem; font-weight: 600; color: #38bdf8;">
            ${summary.overall_progress_pct || 0}% Complete
          </div>
        </div>

        <!-- 5 Stage Micro-Metrics Matrix -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; margin-bottom: 16px;">
          <!-- Stage 1 Design -->
          <div style="background: var(--bg-secondary); padding: 8px 12px; border-radius: 6px; border: 1px solid var(--border-subtle);">
            <div style="font-size: 0.7rem; color: var(--text-dim); text-transform: uppercase;">1. Design</div>
            <div style="font-size: 0.95rem; font-weight: 600; color: var(--text-main); margin-top: 2px;">
              ${summary.design?.approved_docs || 0}/${summary.design?.total_docs || 0} Docs
            </div>
            <div style="font-size: 0.72rem; color: ${summary.design?.open_ecos > 0 ? '#ef4444' : 'var(--text-dim)'};">
              ${summary.design?.open_ecos || 0} Open ECOs
            </div>
          </div>

          <!-- Stage 2 Purchase -->
          <div style="background: var(--bg-secondary); padding: 8px 12px; border-radius: 6px; border: 1px solid var(--border-subtle);">
            <div style="font-size: 0.7rem; color: var(--text-dim); text-transform: uppercase;">2. Purchase</div>
            <div style="font-size: 0.95rem; font-weight: 600; color: var(--text-main); margin-top: 2px;">
              ${summary.procurement?.readiness_pct || 0}% Ready
            </div>
            <div style="font-size: 0.72rem; color: var(--text-dim);">
              ${summary.procurement?.received_parts || 0}/${summary.procurement?.total_parts || 0} Parts
            </div>
          </div>

          <!-- Stage 3 Assembly -->
          <div style="background: var(--bg-secondary); padding: 8px 12px; border-radius: 6px; border: 1px solid var(--border-subtle);">
            <div style="font-size: 0.7rem; color: var(--text-dim); text-transform: uppercase;">3. Assembly</div>
            <div style="font-size: 0.95rem; font-weight: 600; color: var(--text-main); margin-top: 2px;">
              ${summary.assembly?.completed_units || 0}/${summary.assembly?.total_units || 0} Units
            </div>
            <div style="font-size: 0.72rem; color: var(--text-dim);">Validated</div>
          </div>

          <!-- Stage 4 Software -->
          <div style="background: var(--bg-secondary); padding: 8px 12px; border-radius: 6px; border: 1px solid var(--border-subtle);">
            <div style="font-size: 0.7rem; color: var(--text-dim); text-transform: uppercase;">4. Software</div>
            <div style="font-size: 0.95rem; font-weight: 600; color: var(--text-main); margin-top: 2px;">
              ${summary.software?.passed_tests || 0}/${summary.software?.total_tests || 0} Tests
            </div>
            <div style="font-size: 0.72rem; color: ${summary.software?.test_pass_pct === 100 ? '#10b981' : 'var(--text-dim)'};">
              ${summary.software?.test_pass_pct || 0}% Pass Rate
            </div>
          </div>

          <!-- Stage 5 Dispatch -->
          <div style="background: var(--bg-secondary); padding: 8px 12px; border-radius: 6px; border: 1px solid var(--border-subtle);">
            <div style="font-size: 0.7rem; color: var(--text-dim); text-transform: uppercase;">5. Dispatch</div>
            <div style="font-size: 0.95rem; font-weight: 600; color: var(--text-main); margin-top: 2px;">
              ${summary.dispatch?.qa_certified_count > 0 ? '✓ QA Cert' : 'Pending QA'}
            </div>
            <div style="font-size: 0.72rem; color: var(--text-dim);">
              ${summary.dispatch?.packaging_verified || 0}/${summary.dispatch?.packaging_total || 0} Packed
            </div>
          </div>
        </div>

        <!-- Footer Actions -->
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; border-top: 1px solid var(--border-subtle); padding-top: 14px;">
          <div style="display: flex; gap: 16px; font-size: 0.8rem; color: var(--text-dim);">
            <span>Lead: <strong style="color: var(--text-muted);">${p.lead_engineer}</strong></span>
            <span>Budget: <strong style="color: var(--text-muted);">$${p.actual_cost.toLocaleString()} / $${p.budget.toLocaleString()}</strong></span>
          </div>

          <div style="display: flex; gap: 8px;">
            <a href="/projects/${p.id}" class="nexus-btn nexus-btn-secondary" style="text-decoration: none;">
              Open Project Cockpit →
            </a>
            ${p.current_stage !== 'Completed' ? `
              <button class="nexus-btn nexus-btn-primary" onclick="openAdvanceModal(${p.id})">
                Advance Stage ⇥
              </button>
            ` : `
              <span style="font-size: 0.8rem; color: #10b981; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">
                ✓ Project Completed
              </span>
            `}
          </div>
        </div>
      </div>
    `;
  }).join('');
}

async function handleCreateProject(e) {
  e.preventDefault();
  const form = e.target;
  const payload = {
    code: form.code.value.trim(),
    name: form.name.value.trim(),
    description: form.description.value.trim(),
    lead_engineer: form.lead_engineer.value.trim(),
    priority: form.priority.value,
    budget: parseFloat(form.budget.value) || 0.0,
    target_date: form.target_date.value || null,
  };

  try {
    const res = await fetch('/api/v1/projects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Failed to create project');
    }
    showToast('Project initialized successfully!', 'success');
    closeModal('modal-create-project');
    form.reset();
    loadProjects();
    loadDashboardData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function openAdvanceModal(projectId) {
  selectedProjectId = projectId;
  const project = currentProjects.find(p => p.id === projectId);
  if (!project) return;

  const titleEl = document.getElementById('advance-modal-title');
  const contentEl = document.getElementById('advance-modal-content');
  const targetStageInput = document.getElementById('advance-target-stage');
  const overrideCheckbox = document.getElementById('advance-override-check');
  const overrideReasonBox = document.getElementById('advance-override-reason-box');

  if (titleEl) titleEl.textContent = `Advance Stage: ${project.code}`;
  if (overrideCheckbox) overrideCheckbox.checked = false;
  if (overrideReasonBox) overrideReasonBox.style.display = 'none';

  // Fetch gate status
  try {
    const res = await fetch(`/api/v1/projects/${projectId}/gate-status`);
    const gateData = await res.json();

    if (targetStageInput) targetStageInput.value = gateData.next_stage || '';

    let blockersHtml = '';
    if (gateData.can_advance) {
      blockersHtml = `
        <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; border-radius: 8px; padding: 12px; margin-bottom: 16px;">
          <h4 style="color: #10b981; font-size: 0.9rem; font-weight: 600; margin-bottom: 4px;">✓ All Stage Gate Prerequisites Satisfied</h4>
          <p style="font-size: 0.8rem; color: var(--text-main);">
            Ready to transition from <strong>${gateData.current_stage}</strong> to <strong>${gateData.next_stage}</strong>.
          </p>
        </div>
      `;
    } else {
      blockersHtml = `
        <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; border-radius: 8px; padding: 12px; margin-bottom: 16px;">
          <h4 style="color: #ef4444; font-size: 0.9rem; font-weight: 600; margin-bottom: 6px;">⚠️ Stage Gate Incomplete (${gateData.blocking_reasons.length} Blocking Issues)</h4>
          <ul style="font-size: 0.8rem; color: var(--text-main); margin-left: 18px; line-height: 1.5;">
            ${gateData.blocking_reasons.map(r => `<li>${r}</li>`).join('')}
          </ul>
        </div>
      `;
    }

    contentEl.innerHTML = `
      <div style="margin-bottom: 14px;">
        <p style="font-size: 0.85rem; color: var(--text-muted);">Current Stage: <strong style="color: #ffffff;">${gateData.current_stage}</strong></p>
        <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">Target Next Stage: <strong style="color: #38bdf8;">${gateData.next_stage || 'None (Completed)'}</strong></p>
      </div>
      ${blockersHtml}
    `;

    openModal('modal-advance-stage');
  } catch (err) {
    console.error(err);
    showToast('Failed to check gate status', 'error');
  }
}

function toggleOverrideReason(checked) {
  const box = document.getElementById('advance-override-reason-box');
  if (box) {
    box.style.display = checked ? 'block' : 'none';
  }
}

async function handleAdvanceStage(e) {
  e.preventDefault();
  if (!selectedProjectId) return;

  const form = e.target;
  const targetStage = form.target_stage.value;
  const override = form.override_checks.checked;
  const overrideReason = form.override_reason ? form.override_reason.value.trim() : '';

  if (override && !overrideReason) {
    showToast('You must enter an Engineering Override Justification', 'warning');
    return;
  }

  try {
    const res = await fetch(`/api/v1/projects/${selectedProjectId}/advance-stage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_stage: targetStage,
        override_checks: override,
        override_reason: overrideReason,
        performed_by: 'Chief Systems Engineer'
      })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || (data.blockers ? data.blockers.join(', ') : 'Advance failed'));
    }

    showToast(`Successfully advanced to ${targetStage}!`, 'success');
    closeModal('modal-advance-stage');
    loadProjects();
    loadDashboardData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

