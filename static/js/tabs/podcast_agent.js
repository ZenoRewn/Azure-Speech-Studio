/** Podcast Agent — SocketIO async generation. */
(() => {
  const $ = (id) => document.getElementById(id);
  if (!$('pa-start-btn')) return;
  const socket = SocketManager.getSocket();

  function setRunning(on) {
    $('pa-start-btn').classList.toggle('hidden', on);
    $('pa-stop-btn').classList.toggle('hidden', !on);
    $('pa-waveform').classList.toggle('hidden', !on);
  }

  $('pa-start-btn').addEventListener('click', () => {
    const cfg = App.getConfig();
    if (!cfg.speech_key || !cfg.speech_region) {
      App.setStatus('pa-status', 'error', 'Configure Azure Speech in sidebar.');
      return;
    }
    const content = $('pa-content').value.trim();
    if (!content) {
      App.setStatus('pa-status', 'warning', 'Please provide source content.');
      return;
    }
    $('pa-result-section').classList.add('hidden');
    setRunning(true);
    App.setStatus('pa-status', 'info', 'Submitting podcast generation...');
    socket.emit('pa:start', {
      speech_key: cfg.speech_key,
      speech_region: cfg.speech_region,
      content,
      locale: $('pa-locale').value,
      host_type: $('pa-host-type').value,
      style: $('pa-style').value,
      length: $('pa-length').value,
      title: $('pa-title').value,
    });
  });

  $('pa-stop-btn').addEventListener('click', () => {
    socket.emit('pa:stop');
    App.setStatus('pa-status', 'warning', 'Cancelling...');
    setRunning(false);
  });

  socket.on('pa:progress', (data) => App.setStatus('pa-status', 'info', data.text || ''));
  socket.on('pa:done', (data) => {
    setRunning(false);
    App.setStatus('pa-status', 'success', 'Podcast generated.');
    $('pa-result-section').classList.remove('hidden');
    if (data.audio_url) {
      $('pa-audio-player').src = data.audio_url;
      $('pa-audio-link').href = data.audio_url;
    }
    const transcript = $('pa-transcript-link');
    const script = $('pa-script-link');
    if (data.transcript_url) { transcript.href = data.transcript_url; transcript.classList.remove('hidden'); }
    else transcript.classList.add('hidden');
    if (data.script_url) { script.href = data.script_url; script.classList.remove('hidden'); }
    else script.classList.add('hidden');
  });
  socket.on('pa:error', (data) => {
    setRunning(false);
    App.setStatus('pa-status', 'error', data.message || 'Generation failed.');
  });
})();
