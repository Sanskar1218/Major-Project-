// IVF Implantation Predictor Frontend JS
let featuresData = null;
let currentImageFile = null;
let samplePresets = null;

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', async () => {
  await loadFeatures();
  await loadPresets();
  setupEventListeners();
  updateLiveStatus();
});

// Load features metadata
async function loadFeatures() {
  try {
    const res = await fetch('/api/features');
    if (!res.ok) throw new Error('Failed to load features');
    featuresData = await res.json();
    renderFormSections(featuresData.sections);
  } catch (err) {
    console.error('Error loading features:', err);
  }
}

// Load presets
async function loadPresets() {
  try {
    const res = await fetch('/api/presets');
    if (res.ok) {
      samplePresets = await res.json();
    }
  } catch (err) {
    console.warn('Presets could not be loaded:', err);
  }
}

// Render 6 accordion sections
function renderFormSections(sections) {
  const container = document.getElementById('accordionContainer');
  container.innerHTML = '';

  sections.forEach((sec, idx) => {
    const item = document.createElement('div');
    item.className = 'accordion-item' + (idx === 0 ? ' open' : ''); // First section open by default
    item.id = `section-${sec.id}`;

    const iconSvg = getSectionIcon(sec.id);

    item.innerHTML = `
      <div class="accordion-header" data-section="${sec.id}">
        <div class="accordion-title-wrap">
          <div class="section-icon">${iconSvg}</div>
          <div>
            <h3 class="accordion-title">${sec.title}</h3>
            <p class="accordion-desc">${sec.description}</p>
          </div>
        </div>
        <div class="accordion-meta">
          <span class="count-badge" id="badge-${sec.id}">0 / ${sec.features.length}</span>
          <svg class="chevron-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
      </div>
      <div class="accordion-body">
        <div class="inputs-grid">
          ${sec.features.map(f => `
            <div class="form-group" title="${f.tooltip || ''}">
              <div class="form-label-row">
                <label class="form-label" for="input-${f.name}">${f.label}</label>
                <span class="unit-tag">${f.unit || ''}</span>
              </div>
              <div class="input-wrapper">
                <input 
                  type="number" 
                  step="${f.step || 'any'}"
                  min="${f.min ?? ''}"
                  max="${f.max ?? ''}"
                  id="input-${f.name}"
                  name="${f.name}" 
                  class="form-input clinical-input" 
                  placeholder="${f.placeholder || ''}"
                  data-section="${sec.id}"
                >
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    container.appendChild(item);
  });

  // Attach input listeners
  document.querySelectorAll('.clinical-input').forEach(input => {
    input.addEventListener('input', () => {
      updateSectionCount(input.dataset.section);
      updateLiveStatus();
    });
  });

  // Attach header toggle listeners
  document.querySelectorAll('.accordion-header').forEach(header => {
    header.addEventListener('click', () => {
      const parent = header.closest('.accordion-item');
      parent.classList.toggle('open');
    });
  });
}

function getSectionIcon(id) {
  switch (id) {
    case 'female_hormones_age':
      return `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="5"/><path d="M12 13v8"/><path d="M9 18h6"/></svg>`;
    case 'female_blood':
      return `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>`;
    case 'male_semen':
      return `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="m12 2.69 5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>`;
    case 'male_blood':
      return `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>`;
    case 'cycle':
      return `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`;
    case 'post_processing':
      return `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>`;
    default:
      return `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>`;
  }
}

// Update count badge for a given section
function updateSectionCount(secId) {
  if (!secId) return;
  const inputs = document.querySelectorAll(`.clinical-input[data-section="${secId}"]`);
  let filled = 0;
  inputs.forEach(inp => {
    if (inp.value.trim() !== '') filled++;
  });
  const badge = document.getElementById(`badge-${secId}`);
  if (badge) {
    badge.textContent = `${filled} / ${inputs.length}`;
    if (filled > 0) badge.classList.add('has-filled');
    else badge.classList.remove('has-filled');
  }
}

// Live Status & Expected Reliability computation
function updateLiveStatus() {
  const inputs = document.querySelectorAll('.clinical-input');
  let filled = 0;
  inputs.forEach(inp => {
    if (inp.value.trim() !== '') filled++;
  });

  const total = inputs.length || 36;
  const comp = filled / total;
  const hasImage = currentImageFile !== null;

  document.getElementById('inputsCount').textContent = filled;
  document.getElementById('completenessBar').style.width = `${Math.round(comp * 100)}%`;

  const imgIndicator = document.getElementById('imageIndicator');
  const summaryImg = document.getElementById('summaryImage');
  if (hasImage) {
    imgIndicator.textContent = 'Image Attached';
    imgIndicator.classList.add('attached');
    summaryImg.textContent = 'Yes';
    summaryImg.style.color = '#15803d';
  } else {
    imgIndicator.textContent = 'No Image';
    imgIndicator.classList.remove('attached');
    summaryImg.textContent = 'No';
    summaryImg.style.color = '#64748b';
  }

  const relBadge = document.getElementById('summaryReliability');
  relBadge.className = 'reliability-badge';

  if (filled === 0 && !hasImage) {
    relBadge.textContent = 'None (Provide input)';
    relBadge.classList.add('badge-neutral');
  } else if (filled > 0 && hasImage && comp >= 0.75) {
    relBadge.textContent = 'High (Full Multi-modal)';
    relBadge.classList.add('badge-high');
  } else if ((filled > 0 && hasImage && comp >= 0.15) || (filled > 0 && comp >= 0.75)) {
    relBadge.textContent = 'Medium (Partial Fusion)';
    relBadge.classList.add('badge-medium');
  } else {
    relBadge.textContent = 'Low (Single/Sparse)';
    relBadge.classList.add('badge-low');
  }
}

// Event Listeners
function setupEventListeners() {
  // Expand / Collapse all
  document.getElementById('btnExpandAll').addEventListener('click', () => {
    document.querySelectorAll('.accordion-item').forEach(i => i.classList.add('open'));
  });
  document.getElementById('btnCollapseAll').addEventListener('click', () => {
    document.querySelectorAll('.accordion-item').forEach(i => i.classList.remove('open'));
  });

  // Clear Form
  document.getElementById('btnClearForm').addEventListener('click', () => {
    clearForm();
  });

  // Image Drag & Drop and Browse
  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('imageFileInput');

  dropZone.addEventListener('click', (e) => {
    if (e.target.id !== 'btnRemoveImage') {
      fileInput.click();
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      handleImageSelected(e.target.files[0]);
    }
  });

  ['dragenter', 'dragover'].forEach(name => {
    dropZone.addEventListener(name, (e) => {
      e.preventDefault();
      dropZone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(name => {
    dropZone.addEventListener(name, (e) => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
    });
  });

  dropZone.addEventListener('drop', (e) => {
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleImageSelected(e.dataTransfer.files[0]);
    }
  });

  // Remove Image
  document.getElementById('btnRemoveImage').addEventListener('click', (e) => {
    e.stopPropagation();
    removeImage();
  });

  // Sample Image Chips
  document.querySelectorAll('.chip-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const sampleId = btn.dataset.sample;
      await loadSampleImage(sampleId);
    });
  });

  // Scenario Presets
  document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const p = btn.dataset.preset;
      applyPreset(p);
    });
  });

  // Predict Button
  document.getElementById('btnPredict').addEventListener('click', () => {
    runPrediction();
  });

  // Modal open & close
  document.getElementById('btnPerformanceModal').addEventListener('click', () => {
    openPerformanceModal();
  });
  document.getElementById('btnCloseModal').addEventListener('click', () => {
    document.getElementById('performanceModal').classList.add('hidden');
  });
  document.getElementById('performanceModal').addEventListener('click', (e) => {
    if (e.target.id === 'performanceModal') {
      document.getElementById('performanceModal').classList.add('hidden');
    }
  });
}

function handleImageSelected(file) {
  currentImageFile = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    document.getElementById('imagePreview').src = e.target.result;
    document.getElementById('previewFilename').textContent = file.name || 'embryo_blastocyst.jpg';
    document.getElementById('dropZonePrompt').classList.add('hidden');
    document.getElementById('imagePreviewContainer').classList.remove('hidden');
    updateLiveStatus();
  };
  reader.readAsDataURL(file);
}

function removeImage() {
  currentImageFile = null;
  document.getElementById('imageFileInput').value = '';
  document.getElementById('imagePreview').src = '';
  document.getElementById('dropZonePrompt').classList.remove('hidden');
  document.getElementById('imagePreviewContainer').classList.add('hidden');
  updateLiveStatus();
}

async function loadSampleImage(sampleId) {
  try {
    const res = await fetch(`/api/sample_image/${sampleId}`);
    if (!res.ok) throw new Error('Failed to load sample image');
    const blob = await res.blob();
    const file = new File([blob], `${sampleId}.jpg`, { type: 'image/jpeg' });
    handleImageSelected(file);
  } catch (err) {
    console.error('Error loading sample image:', err);
  }
}

// Clear all inputs
function clearForm() {
  document.querySelectorAll('.clinical-input').forEach(inp => inp.value = '');
  removeImage();
  if (featuresData) {
    featuresData.sections.forEach(s => updateSectionCount(s.id));
  }
  updateLiveStatus();
  document.getElementById('resultCard').classList.add('hidden');
}

// Apply quick scenario preset
async function applyPreset(presetType) {
  if (!samplePresets) {
    await loadPresets();
  }
  if (!samplePresets) return;

  const data = samplePresets[presetType];
  if (!data) return;

  // Clear first
  clearForm();

  // Fill clinical features
  if (data.clinical) {
    for (const [key, val] of Object.entries(data.clinical)) {
      const input = document.getElementById(`input-${key}`);
      if (input && val !== null && val !== undefined && val !== '') {
        input.value = val;
      }
    }
  }

  // Load preset image if available
  if (data.image_sample) {
    await loadSampleImage(data.image_sample);
  }

  // Update count badges
  if (featuresData) {
    featuresData.sections.forEach(s => updateSectionCount(s.id));
  }
  updateLiveStatus();

  // Auto-run prediction for quick instant feedback
  runPrediction();
}

// Run Prediction API call
async function runPrediction() {
  const inputs = document.querySelectorAll('.clinical-input');
  const clinicalObj = {};
  let filledCount = 0;

  inputs.forEach(inp => {
    const v = inp.value.trim();
    if (v !== '') {
      clinicalObj[inp.name] = parseFloat(v);
      filledCount++;
    } else {
      clinicalObj[inp.name] = null;
    }
  });

  if (filledCount === 0 && !currentImageFile) {
    alert('Please enter at least one clinical value or upload an embryo image to predict.');
    return;
  }

  const spinner = document.getElementById('predictSpinner');
  const btnText = document.getElementById('predictBtnText');
  const btnPredict = document.getElementById('btnPredict');

  spinner.classList.remove('hidden');
  btnText.textContent = 'Processing Multimodal Ensemble...';
  btnPredict.disabled = true;

  try {
    const formData = new FormData();
    formData.append('clinical_json', JSON.stringify(clinicalObj));
    if (currentImageFile) {
      formData.append('image', currentImageFile);
    }

    const res = await fetch('/api/predict', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.error || `Server responded with ${res.status}`);
    }

    const result = await res.json();
    renderPredictionResult(result);
  } catch (err) {
    alert(`Prediction Error: ${err.message}`);
    console.error(err);
  } finally {
    spinner.classList.add('hidden');
    btnText.textContent = '⚡ Predict Implantation Success';
    btnPredict.disabled = false;
  }
}

// Render Result Card
function renderPredictionResult(res) {
  const card = document.getElementById('resultCard');
  card.classList.remove('hidden');

  const probPercent = (res.probability * 100).toFixed(1);
  document.getElementById('probVal').textContent = `${probPercent}%`;

  const circle = document.getElementById('probCircle');
  const isLikely = res.probability >= res.threshold;

  if (isLikely) {
    circle.style.borderColor = '#16a34a';
    circle.style.boxShadow = '0 4px 14px rgba(22, 163, 74, 0.25)';
  } else {
    circle.style.borderColor = '#0284c7';
    circle.style.boxShadow = '0 4px 14px rgba(2, 132, 199, 0.2)';
  }

  // Verdict Tag
  const verdictTag = document.getElementById('verdictTag');
  verdictTag.textContent = res.prediction;
  verdictTag.className = 'verdict-tag ' + (isLikely ? 'verdict-likely' : 'verdict-unlikely');

  // Reliability Tag
  const relTag = document.getElementById('resultReliabilityTag');
  relTag.textContent = `Reliability: ${res.reliability}`;
  relTag.className = 'reliability-tag';
  if (res.reliability === 'High') {
    relTag.style.background = '#dcfce7';
    relTag.style.color = '#15803d';
  } else if (res.reliability === 'Medium') {
    relTag.style.background = '#fef3c7';
    relTag.style.color = '#b45309';
  } else {
    relTag.style.background = '#fee2e2';
    relTag.style.color = '#b91c1c';
  }

  // Sub scores
  document.getElementById('scoreClinical').textContent = 
    res.clinical_score !== null ? `${(res.clinical_score * 100).toFixed(1)}%` : 'N/A';
  document.getElementById('clinicalInputsGiven').textContent = 
    `${res.inputs_provided} of ${res.inputs_total} provided`;

  document.getElementById('scoreImage').textContent = 
    res.image_score !== null ? `${(res.image_score * 100).toFixed(1)}%` : 'N/A';
  document.getElementById('visionModelUsed').textContent = 
    res.used_image ? '10 CNN models (TTA)' : 'No image uploaded';

  document.getElementById('scoreThreshold').textContent = `${(res.threshold * 100).toFixed(1)}%`;

  // Rationale
  let rationale = '';
  if (res.reliability === 'High') {
    rationale = `High-confidence assessment: Comprehensive clinical panel (${res.inputs_provided}/36 features) and blastocyst microphotograph evaluated through dual-branch ensemble fusion.`;
  } else if (res.reliability === 'Medium') {
    rationale = `Moderate-confidence assessment: Model utilized available subset of clinical markers (${res.inputs_provided}/36) with multimodal dropout calibration.`;
  } else {
    rationale = `Lower-confidence screening: Prediction is based on sparse or single-modality inputs (${res.used_image ? 'Image-focused' : 'Few clinical features'}). Supplying additional lab panels is advised for diagnostic robustness.`;
  }
  document.getElementById('rationaleText').textContent = rationale;

  // Scroll smoothly to result card if on mobile
  if (window.innerWidth < 1024) {
    card.scrollIntoView({ behavior: 'smooth' });
  }
}

// Performance Modal
async function openPerformanceModal() {
  const modal = document.getElementById('performanceModal');
  modal.classList.remove('hidden');

  try {
    const res = await fetch('/api/metrics');
    if (res.ok) {
      const data = await res.json();
      const tbody = document.getElementById('benchmarkTableBody');
      tbody.innerHTML = '';
      (data.test_by_scenario || []).forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${row.Scenario}</strong></td>
          <td>${row.AUC.toFixed(3)} ${row.AUC_lo ? `(${row.AUC_lo.toFixed(3)}–${row.AUC_hi.toFixed(3)})` : ''}</td>
          <td>${(row.Accuracy * 100).toFixed(1)}%</td>
          <td>${(row.Sensitivity * 100).toFixed(1)}%</td>
          <td>${(row.Specificity * 100).toFixed(1)}%</td>
          <td>${row.F1.toFixed(3)}</td>
        `;
        tbody.appendChild(tr);
      });
    }
  } catch (err) {
    console.warn('Failed to load performance metrics:', err);
  }
}

