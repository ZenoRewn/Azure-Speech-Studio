/** Video Translation tab — SocketIO async polling. */
(() => {
  const $ = (id) => document.getElementById(id);
  if (!$('vt-start-btn')) return;
  const socket = SocketManager.getSocket();

  function setRunning(on) {
    $('vt-start-btn').classList.toggle('hidden', on);
    $('vt-stop-btn').classList.toggle('hidden', !on);
  }

  $('vt-start-btn').addEventListener('click', () => {
    const cfg = App.getConfig();
    if (!cfg.speech_key || !cfg.speech_region) {
      App.setStatus('vt-status', 'error', 'Configure Azure Speech in sidebar.');
      return;
    }
    const url = $('vt-video-url').value.trim();
    if (!url) {
      App.setStatus('vt-status', 'warning', 'Please provide a video URL.');
      return;
    }
    $('vt-result-section').classList.add('hidden');
    setRunning(true);
    App.setStatus('vt-status', 'info', 'Submitting translation job...');
    socket.emit('vt:start', {
      speech_key: cfg.speech_key,
      speech_region: cfg.speech_region,
      video_url: url,
      source_locale: $('vt-source-locale').value,
      target_locale: $('vt-target-locale').value,
      voice_kind: $('vt-voice-kind').value,
      speaker_count: $('vt-speaker-count').value || null,
      subtitle_max_chars: $('vt-subtitle-max').value || null,
      export_subtitle_in_video: $('vt-burn-subtitles').checked,
    });
  });

  $('vt-stop-btn').addEventListener('click', () => {
    socket.emit('vt:stop');
    App.setStatus('vt-status', 'warning', 'Cancelling...');
    setRunning(false);
  });

  socket.on('vt:progress', (data) => App.setStatus('vt-status', 'info', data.text || ''));
  socket.on('vt:done', (data) => {
    setRunning(false);
    App.setStatus('vt-status', 'success',
      `Translation complete: ${data.source_locale} → ${data.target_locale}`);
    $('vt-result-section').classList.remove('hidden');
    if (data.video_url) $('vt-video-link').href = data.video_url;
    if (data.subtitle_url) {
      $('vt-subtitle-link').href = data.subtitle_url;
      $('vt-subtitle-link').classList.remove('hidden');
    } else {
      $('vt-subtitle-link').classList.add('hidden');
    }
  });
  socket.on('vt:error', (data) => {
    setRunning(false);
    App.setStatus('vt-status', 'error', data.message || 'Translation failed.');
  });
})();
