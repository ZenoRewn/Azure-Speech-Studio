/** MAI-Transcribe tab — HTTP POST to /api/mai-transcribe. */
(() => {
  const $ = (id) => document.getElementById(id);
  const btn = $('mai-start-btn');
  if (!btn) return;

  btn.addEventListener('click', async () => {
    const cfg = App.getConfig();
    const fileEl = $('mai-file-input');
    if (!fileEl.files[0]) {
      App.setStatus('mai-status', 'warning', 'Please select an audio file.');
      return;
    }
    if (!cfg.speech_key || !cfg.speech_region) {
      App.setStatus('mai-status', 'error', 'Configure Azure Speech key and region in sidebar.');
      return;
    }

    const locales = Array.from($('mai-locales').selectedOptions).map(o => o.value);
    if (locales.length === 0) {
      App.setStatus('mai-status', 'warning', 'Select at least one locale.');
      return;
    }

    const fd = new FormData();
    fd.append('file', fileEl.files[0]);
    fd.append('speech_key', cfg.speech_key);
    fd.append('speech_region', cfg.speech_region);
    fd.append('locales', locales.join(','));
    fd.append('enable_diarization', $('mai-diarization').checked ? 'true' : 'false');
    fd.append('max_speakers', $('mai-max-speakers').value || '4');
    fd.append('phrase_list', $('mai-phrase-list').value || '');

    App.setStatus('mai-status', 'info', 'Transcribing with MAI-Transcribe-1...');
    btn.disabled = true;
    btn.classList.add('running');
    try {
      const resp = await fetch('/api/mai-transcribe', { method: 'POST', body: fd });
      const data = await resp.json();
      if (!resp.ok) {
        App.setStatus('mai-status', 'error', 'Error: ' + (data.error || resp.statusText));
        return;
      }

      const segments = data.segments || [];
      const combined = data.combined_text || '';
      if (combined) {
        $('mai-combined-section').classList.remove('hidden');
        $('mai-combined').value = combined;
      }
      const lines = segments.map((s, i) => {
        const t = (s.offset_ms / 1000).toFixed(2);
        const speaker = s.speaker ? '[' + s.speaker + '] ' : '';
        const locale = s.locale ? '(' + s.locale + ') ' : '';
        return `${String(i + 1).padStart(3, '0')}  ${t}s  ${speaker}${locale}${s.text}`;
      });
      $('mai-results').textContent = lines.join('\n');
      App.setStatus('mai-status', 'success', `Completed. ${segments.length} segments.`);
    } catch (err) {
      App.setStatus('mai-status', 'error', 'Failed: ' + err.message);
    } finally {
      btn.disabled = false;
      btn.classList.remove('running');
    }
  });
})();
