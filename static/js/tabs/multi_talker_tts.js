/** Multi-Talker TTS tab. */
(() => {
  const $ = (id) => document.getElementById(id);
  if (!$('mt-synthesize-btn')) return;

  const presets = JSON.parse($('mt-presets-data').textContent);

  function applyPreset() {
    const locale = $('mt-locale').value;
    const cfg = presets[locale];
    if (!cfg) return;
    $('mt-voice-name').value = cfg.voiceName;
    if (!$('mt-content').value.trim()) {
      $('mt-content').value = cfg.sample || '';
    }
  }
  $('mt-locale').addEventListener('change', applyPreset);
  applyPreset();

  $('mt-preview-btn').addEventListener('click', async () => {
    const resp = await fetch('/api/multi-talker-tts/ssml-preview', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        content: $('mt-content').value,
        voice_name: $('mt-voice-name').value,
        locale: $('mt-locale').value,
      }),
    });
    const data = await resp.json();
    $('mt-ssml').textContent = data.ssml || '';
    $('mt-ssml-panel').open = true;
  });

  $('mt-synthesize-btn').addEventListener('click', async () => {
    const cfg = App.getConfig();
    if (!cfg.speech_key || !cfg.speech_region) {
      App.setStatus('mt-status', 'error', 'Configure Azure Speech in sidebar.');
      return;
    }
    const content = $('mt-content').value.trim();
    if (!content) {
      App.setStatus('mt-status', 'warning', 'Please provide dialog script.');
      return;
    }
    App.setStatus('mt-status', 'info', 'Synthesizing multi-talker dialog...');
    $('mt-synthesize-btn').disabled = true;
    try {
      const resp = await fetch('/api/multi-talker-tts/synthesize', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          speech_key: cfg.speech_key,
          speech_region: cfg.speech_region,
          content,
          voice_name: $('mt-voice-name').value,
          locale: $('mt-locale').value,
        }),
      });
      if (!resp.ok) {
        const err = await resp.json();
        App.setStatus('mt-status', 'error', err.error || resp.statusText);
        return;
      }
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const player = $('mt-audio-player');
      player.src = url;
      player.classList.remove('hidden');
      const dl = $('mt-download-btn');
      dl.classList.remove('hidden');
      dl.onclick = () => {
        const a = document.createElement('a');
        a.href = url; a.download = 'multi_talker.wav'; a.click();
      };
      App.setStatus('mt-status', 'success', `Synthesis complete (${(blob.size / 1024).toFixed(1)} KB).`);
    } catch (err) {
      App.setStatus('mt-status', 'error', err.message);
    } finally {
      $('mt-synthesize-btn').disabled = false;
    }
  });
})();
