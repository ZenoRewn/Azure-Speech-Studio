/**
 * Tab 7: Text to Speech
 */
(() => {
  const modeSelect = document.getElementById('tts-mode');
  const voiceLabel = document.getElementById('tts-voice-label');
  const voiceSelect = document.getElementById('tts-voice');
  const textInput = document.getElementById('tts-input');
  const synthesizeBtn = document.getElementById('tts-synthesize-btn');
  const downloadBtn = document.getElementById('tts-download-btn');
  const audioPlayer = document.getElementById('tts-audio-player');
  const statusBar = document.getElementById('tts-status');

  const SSML_TEMPLATE = `<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN">
  <voice name="zh-CN-XiaoxiaoNeural">
    在此输入文本
  </voice>
</speak>`;

  let currentBlobUrl = null;

  // Mode switch: hide Voice dropdown in SSML mode (voice is inside SSML)
  modeSelect.addEventListener('change', () => {
    const isSSML = modeSelect.value === 'ssml';
    voiceLabel.style.display = isSSML ? 'none' : '';
    textInput.placeholder = isSSML
      ? '输入 SSML 内容...'
      : '输入要合成的文本...';
    if (isSSML && !textInput.value.trim()) {
      textInput.value = SSML_TEMPLATE;
    }
  });

  // Synthesize
  synthesizeBtn.addEventListener('click', async () => {
    const cfg = App.getConfig();
    const mode = modeSelect.value;
    const text = textInput.value.trim();

    if (!cfg.speech_key || !cfg.speech_region) {
      App.setStatus('tts-status', 'error', 'Missing Azure Speech Key or Region.');
      return;
    }
    if (!text) {
      App.setStatus('tts-status', 'error', 'Please enter text to synthesize.');
      return;
    }

    const body = {
      speech_key: cfg.speech_key,
      speech_region: cfg.speech_region,
      text: text,
      voice: voiceSelect.value,
      mode: mode,
    };

    App.setStatus('tts-status', 'info', 'Synthesizing...');
    synthesizeBtn.disabled = true;

    try {
      const resp = await fetch('/api/tts/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ error: resp.statusText }));
        throw new Error(err.error || 'Synthesis failed');
      }

      const blob = await resp.blob();

      // Revoke previous URL
      if (currentBlobUrl) {
        URL.revokeObjectURL(currentBlobUrl);
      }
      currentBlobUrl = URL.createObjectURL(blob);

      audioPlayer.src = currentBlobUrl;
      audioPlayer.style.display = '';
      audioPlayer.play();

      downloadBtn.style.display = '';
      App.setStatus('tts-status', 'success', 'Synthesis complete.');
    } catch (err) {
      App.setStatus('tts-status', 'error', err.message);
    } finally {
      synthesizeBtn.disabled = false;
    }
  });

  // Download
  downloadBtn.addEventListener('click', () => {
    if (!currentBlobUrl) return;
    const a = document.createElement('a');
    a.href = currentBlobUrl;
    a.download = 'tts_output.wav';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  });
})();

