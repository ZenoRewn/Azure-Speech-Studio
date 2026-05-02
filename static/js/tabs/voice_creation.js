/** Voice Creation — 4-step wizard for Personal Voice training. */
(() => {
  const $ = (id) => document.getElementById(id);
  if (!$('vc-next-btn')) return;

  const consentTemplate = JSON.parse($('vc-consent-template').textContent);
  let currentStep = 1;

  function renderStep() {
    for (let i = 1; i <= 4; i++) {
      const pane = $('vc-step-' + i);
      if (pane) pane.classList.toggle('hidden', i !== currentStep);
    }
    document.querySelectorAll('#vc-stepper .step').forEach(s => {
      const n = parseInt(s.dataset.step);
      s.classList.toggle('active', n === currentStep);
      s.classList.toggle('done', n < currentStep);
    });
    $('vc-prev-btn').disabled = currentStep === 1;
    $('vc-next-btn').classList.toggle('hidden', currentStep === 4);
    $('vc-submit-btn').classList.toggle('hidden', currentStep !== 4);

    if (currentStep === 2) {
      const statement = consentTemplate
        .replace('{voice_talent_name}', $('vc-voice-name').value || '<name>')
        .replace('{company_name}', $('vc-company-name').value || '<company>');
      $('vc-consent-text').textContent = statement;
    }
    if (currentStep === 3) {
      const files = $('vc-training-files').files;
      const list = $('vc-training-list');
      list.innerHTML = '';
      for (const f of files) {
        const row = document.createElement('div');
        row.className = 'list-row';
        row.innerHTML = `<span class="flex-1">${f.name}</span><span class="muted">${(f.size/1024/1024).toFixed(2)} MB</span>`;
        list.appendChild(row);
      }
    }
  }

  function validateStep() {
    if (currentStep === 1) {
      if (!$('vc-project-name').value || !$('vc-voice-name').value) {
        App.setStatus('vc-status', 'warning', 'Project and voice talent names are required.');
        return false;
      }
    } else if (currentStep === 2) {
      if (!$('vc-consent-file').files[0]) {
        App.setStatus('vc-status', 'warning', 'Please upload consent audio.');
        return false;
      }
    } else if (currentStep === 3) {
      if (!$('vc-training-files').files.length) {
        App.setStatus('vc-status', 'warning', 'Please upload at least one training audio file.');
        return false;
      }
    }
    return true;
  }

  $('vc-next-btn').addEventListener('click', () => {
    if (!validateStep()) return;
    currentStep = Math.min(4, currentStep + 1);
    renderStep();
  });
  $('vc-prev-btn').addEventListener('click', () => {
    currentStep = Math.max(1, currentStep - 1);
    renderStep();
  });
  $('vc-training-files').addEventListener('change', renderStep);

  $('vc-submit-btn').addEventListener('click', async () => {
    const cfg = App.getConfig();
    if (!cfg.speech_key || !cfg.speech_region) {
      App.setStatus('vc-status', 'error', 'Configure Azure Speech in sidebar.');
      return;
    }
    const fd = new FormData();
    fd.append('speech_key', cfg.speech_key);
    fd.append('speech_region', cfg.speech_region);
    fd.append('project_name', $('vc-project-name').value);
    fd.append('voice_name', $('vc-voice-name').value);
    fd.append('company_name', $('vc-company-name').value);
    fd.append('model_id', $('vc-model-id').value);
    fd.append('locale', $('vc-locale').value);
    fd.append('description', $('vc-description').value);
    fd.append('consent_audio', $('vc-consent-file').files[0]);
    for (const f of $('vc-training-files').files) fd.append('training_audio', f);

    App.setStatus('vc-status', 'info', 'Uploading and submitting training... this can take a minute.');
    $('vc-submit-btn').disabled = true;
    try {
      const resp = await fetch('/api/voice-creation/create', { method: 'POST', body: fd });
      const data = await resp.json();
      if (!resp.ok) {
        App.setStatus('vc-status', 'error', data.error || resp.statusText);
        return;
      }
      App.setStatus('vc-status', 'success',
        `Voice "${$('vc-voice-name').value}" submitted. Voice ID: ${data.voice_id}`);
      refreshVoices();
    } catch (err) {
      App.setStatus('vc-status', 'error', err.message);
    } finally {
      $('vc-submit-btn').disabled = false;
    }
  });

  async function refreshVoices() {
    const cfg = App.getConfig();
    if (!cfg.speech_key || !cfg.speech_region) return;
    const params = new URLSearchParams({ speech_key: cfg.speech_key, speech_region: cfg.speech_region });
    try {
      const resp = await fetch('/api/voice-creation/voices?' + params.toString());
      const data = await resp.json();
      const list = $('vc-voices-list');
      list.innerHTML = '';
      const voices = data.value || data.values || [];
      if (!voices.length) {
        list.innerHTML = '<div class="muted">No custom voices found.</div>';
        return;
      }
      voices.forEach(v => {
        const row = document.createElement('div');
        row.className = 'list-row';
        row.innerHTML = `
          <span class="flex-1"><strong>${v.displayName || v.name || '(unnamed)'}</strong></span>
          <span class="mono muted">${v.locale || ''}</span>
          <span class="mono">${v.status || ''}</span>
          <span class="mono muted">${v.id || ''}</span>`;
        list.appendChild(row);
      });
    } catch (err) {
      // silently ignore — first-load may fail without creds
    }
  }
  $('vc-refresh-voices-btn').addEventListener('click', refreshVoices);
  renderStep();
})();
