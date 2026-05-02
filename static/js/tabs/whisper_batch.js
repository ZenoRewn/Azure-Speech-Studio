/** Whisper Batch tab — SocketIO async polling. */
(() => {
  const $ = (id) => document.getElementById(id);
  if (!$('wb-start-btn')) return;
  const socket = SocketManager.getSocket();
  let running = false;
  let ringPct = 0;

  function setRunning(on) {
    running = on;
    $('wb-start-btn').classList.toggle('hidden', on);
    $('wb-stop-btn').classList.toggle('hidden', !on);
    $('wb-ring').classList.toggle('hidden', !on);
    if (on) Effects.setRing('wb-ring', 0, '0%');
  }

  $('wb-start-btn').addEventListener('click', () => {
    const cfg = App.getConfig();
    if (!cfg.speech_key || !cfg.speech_region) {
      App.setStatus('wb-status', 'error', 'Configure Azure Speech in sidebar.');
      return;
    }
    const audioUrl = $('wb-audio-url').value.trim();
    if (!audioUrl) {
      App.setStatus('wb-status', 'warning', 'Please provide an audio URL.');
      return;
    }
    $('wb-results').textContent = '';
    ringPct = 5;
    setRunning(true);
    App.setStatus('wb-status', 'info', 'Submitting Whisper batch job...');
    socket.emit('wb:start', {
      speech_key: cfg.speech_key,
      speech_region: cfg.speech_region,
      audio_url: audioUrl,
      locale: $('wb-locale').value,
    });
  });

  $('wb-stop-btn').addEventListener('click', () => {
    socket.emit('wb:stop');
    App.setStatus('wb-status', 'warning', 'Cancelling...');
    setRunning(false);
  });

  socket.on('wb:progress', (data) => {
    App.setStatus('wb-status', 'info', data.text || '');
    // Best-effort progress bump per phase
    const phaseMap = { finding_model: 15, found_model: 25, submitting: 35, polling: 60, fetching: 90, cancelled: 0 };
    const next = phaseMap[data.phase];
    if (next != null) {
      ringPct = Math.max(ringPct, next);
      Effects.setRing('wb-ring', ringPct);
    }
  });
  socket.on('wb:done', (data) => {
    Effects.setRing('wb-ring', 100, 'Done');
    setTimeout(() => setRunning(false), 300);
    const segments = data.segments || [];
    const text = segments.map((s, i) => {
      const t = s.offset_ms ? (s.offset_ms / 1000).toFixed(2) + 's  ' : '';
      const speaker = s.speaker ? '[' + s.speaker + '] ' : '';
      return `${String(i + 1).padStart(3, '0')}  ${t}${speaker}${s.text}`;
    }).join('\n');
    $('wb-results').textContent = text || '(no segments)';
    App.setStatus('wb-status', 'success', `Complete. ${segments.length} segments.`);
  });
  socket.on('wb:error', (data) => {
    setRunning(false);
    App.setStatus('wb-status', 'error', data.message || 'Failed.');
  });
})();
