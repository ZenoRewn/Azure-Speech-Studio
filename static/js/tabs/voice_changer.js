/** Voice Changer — upload audio -> convert to selected target voice. */
(() => {
  const $ = (id) => document.getElementById(id);
  if (!$('vch-start-btn')) return;

  const allowedRegions = ['eastus', 'westeurope', 'southeastasia'];
  let selectedVoice = null;

  function checkRegion() {
    const region = App.getConfig().speech_region;
    const warn = $('vch-region-warn');
    if (region && !allowedRegions.includes(region)) {
      warn.classList.remove('hidden');
      warn.textContent = `Voice Changer is only available in ${allowedRegions.join(', ')}. Current: ${region}.`;
    } else {
      warn.classList.add('hidden');
    }
  }
  ['cfg-speech-region'].forEach(id => {
    const el = $(id);
    if (el) el.addEventListener('input', checkRegion);
  });
  checkRegion();

  document.querySelectorAll('#vch-voice-grid .voice-card').forEach(card => {
    card.addEventListener('click', () => {
      document.querySelectorAll('#vch-voice-grid .voice-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      selectedVoice = card.dataset.voice;
    });
  });

  $('vch-start-btn').addEventListener('click', async () => {
    const cfg = App.getConfig();
    if (!cfg.speech_key || !cfg.speech_region) {
      App.setStatus('vch-status', 'error', 'Configure Azure Speech in sidebar.');
      return;
    }
    const fileEl = $('vch-file-input');
    if (!fileEl.files[0]) {
      App.setStatus('vch-status', 'warning', 'Please select an audio file.');
      return;
    }
    if (!selectedVoice) {
      App.setStatus('vch-status', 'warning', 'Please select a target voice.');
      return;
    }
    App.setStatus('vch-status', 'info', 'Uploading and converting...');
    $('vch-start-btn').disabled = true;
    try {
      const fd = new FormData();
      fd.append('file', fileEl.files[0]);
      fd.append('speech_key', cfg.speech_key);
      fd.append('speech_region', cfg.speech_region);
      fd.append('target_voice', selectedVoice);
      const resp = await fetch('/api/voice-changer', { method: 'POST', body: fd });
      if (!resp.ok) {
        const err = await resp.json();
        App.setStatus('vch-status', 'error', err.error || resp.statusText);
        return;
      }
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const player = $('vch-audio-player');
      player.src = url;
      player.classList.remove('hidden');
      const dl = $('vch-download-btn');
      dl.classList.remove('hidden');
      dl.onclick = () => {
        const a = document.createElement('a');
        a.href = url; a.download = 'voice_changer.mp3'; a.click();
      };
      App.setStatus('vch-status', 'success', `Conversion complete (${(blob.size / 1024).toFixed(1)} KB).`);
    } catch (err) {
      App.setStatus('vch-status', 'error', err.message);
    } finally {
      $('vch-start-btn').disabled = false;
    }
  });
})();
