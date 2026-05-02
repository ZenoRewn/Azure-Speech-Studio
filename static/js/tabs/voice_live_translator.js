/** Voice Live Translator — mic streaming with translation instructions. */
(() => {
  const $ = (id) => document.getElementById(id);
  if (!$('vlt-start-btn')) return;

  const voiceProviders = JSON.parse(document.getElementById('vl-voice-providers-data').textContent);
  let mic = null, playback = null;

  function populateVoices() {
    const provider = $('vlt-voice-provider').value;
    const voices = voiceProviders[provider] || {};
    const sel = $('vlt-voice');
    sel.innerHTML = '';
    Object.entries(voices).forEach(([label, val]) => {
      const opt = document.createElement('option');
      opt.value = val; opt.textContent = label;
      sel.appendChild(opt);
    });
  }
  $('vlt-voice-provider').addEventListener('change', populateVoices);
  populateVoices();

  function appendMsg(role, text) {
    const box = $('vlt-conversation');
    const div = document.createElement('div');
    div.className = 'msg ' + role;
    div.textContent = text;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
  }

  function setRunning(on) {
    $('vlt-start-btn').classList.toggle('hidden', on);
    $('vlt-stop-btn').classList.toggle('hidden', !on);
  }

  $('vlt-start-btn').addEventListener('click', async () => {
    const cfg = App.getConfig();
    if (!cfg.vl_endpoint && !cfg.speech_region) {
      App.setStatus('vlt-status', 'error', 'Provide Voice Live endpoint or Speech region in sidebar.');
      return;
    }
    const apiKey = cfg.api_key || cfg.speech_key;
    if (!apiKey) {
      App.setStatus('vlt-status', 'error', 'Provide Azure OpenAI or Speech key in sidebar.');
      return;
    }
    $('vlt-conversation').innerHTML = '';
    try {
      mic = new MicCapture(24000);
      playback = new AudioPlayback(24000);
      const socket = SocketManager.getSocket();
      mic.onAudioData = (buf) => socket.emit('vlt:mic_audio', buf);
      await mic.start();

      socket.emit('vlt:start', {
        config: {
          vl_endpoint: cfg.vl_endpoint || `https://${cfg.speech_region}.cognitiveservices.azure.com`,
          api_key: apiKey,
          model: $('vlt-model').value,
          voice: $('vlt-voice').value,
          voice_provider: $('vlt-voice-provider').value,
          target_language: $('vlt-target-language').value,
          asr_model: $('vlt-asr-model').value,
          instructions: $('vlt-instructions').value,
        },
      });
      setRunning(true);
    } catch (err) {
      App.setStatus('vlt-status', 'error', 'Microphone error: ' + err.message);
    }
  });

  $('vlt-stop-btn').addEventListener('click', () => {
    if (mic) { mic.stop(); mic = null; }
    if (playback) { playback.close(); playback = null; }
    SocketManager.getSocket().emit('vlt:stop');
    setRunning(false);
  });

  const socket = SocketManager.getSocket();
  socket.on('vlt:status', (d) => App.setStatus('vlt-status', d.type, d.message));
  socket.on('vlt:transcript', (d) => appendMsg(d.role === 'assistant' ? 'assistant' : d.role, d.text));
  socket.on('vlt:playback_audio', (d) => { if (playback) playback.queueAudio(d.audio); });
  socket.on('vlt:skip_audio', () => { if (playback) playback.skipPending(); });
  socket.on('vlt:stopped', (d) => {
    App.setStatus('vlt-status', 'warning', d.message);
    if (mic) { mic.stop(); mic = null; }
    if (playback) { playback.close(); playback = null; }
    setRunning(false);
  });
})();
