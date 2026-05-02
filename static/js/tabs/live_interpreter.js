/**
 * Tab 4: Live Interpreter
 */
(() => {
  let mic = null;
  let playback = null;
  let isActive = false;
  let isPaused = false;

  document.querySelectorAll('input[name="li-source"]').forEach(radio => {
    radio.addEventListener('change', () => {
      document.getElementById('li-file-section').style.display =
        radio.value === 'file' && radio.checked ? '' : 'none';
    });
  });

  function getSelectedSource() {
    return document.querySelector('input[name="li-source"]:checked').value;
  }

  function buildConfig() {
    const cfg = App.getConfig();
    return {
      speech_key: cfg.speech_key,
      speech_region: cfg.speech_region,
      target_language: document.getElementById('li-target-lang').value,
      voice_mode: document.getElementById('li-voice-mode').value,
    };
  }

  function showButtons(state) {
    document.getElementById('li-start-btn').style.display = state === 'idle' ? '' : 'none';
    document.getElementById('li-pause-btn').style.display = state === 'active' ? '' : 'none';
    document.getElementById('li-resume-btn').style.display = state === 'paused' ? '' : 'none';
    document.getElementById('li-stop-btn').style.display = (state === 'active' || state === 'paused') ? '' : 'none';
    document.getElementById('li-download-btn').style.display = state === 'stopped' ? '' : 'none';
  }

  function appendResult(data) {
    if (data.type === 'interim') {
      const interim = document.getElementById('li-interim');
      const lang = data.language ? ` [${data.language}]` : '';
      interim.textContent = `Hearing${lang}: ${data.text}`;
      return;
    }

    // Clear interim
    document.getElementById('li-interim').textContent = '';

    const box = document.getElementById('li-results');

    if (data.type === 'error') {
      const el = document.createElement('div');
      el.className = 'msg msg-error';
      el.textContent = data.text;
      box.appendChild(el);
    } else if (data.type === 'final') {
      const entry = document.createElement('div');
      entry.className = 'translation-entry';
      const lang = data.language ? ` [${data.language}]` : '';
      let html = `<div class="original"><strong>Original${lang}:</strong> ${data.text}</div>`;
      for (const [lc, tt] of Object.entries(data.translations)) {
        html += `<div class="translated">&rarr; <em>${lc}</em>: ${tt}</div>`;
      }
      entry.innerHTML = html;
      box.appendChild(entry);
    }
    box.scrollTop = box.scrollHeight;
  }

  // Start
  document.getElementById('li-start-btn').addEventListener('click', async () => {
    const source = getSelectedSource();
    document.getElementById('li-results').innerHTML = '';
    document.getElementById('li-interim').textContent = '';
    document.getElementById('li-audio-container').style.display = 'none';

    playback = new AudioPlayback(16000);

    if (source === 'mic') {
      try {
        mic = new MicCapture(16000);
        const socket = SocketManager.getSocket();
        mic.onAudioData = (buffer) => {
          socket.emit('li:mic_audio', buffer);
        };
        await mic.start();
        socket.emit('li:start_mic', { config: buildConfig() });
        isActive = true;
        isPaused = false;
        showButtons('active');
      } catch (err) {
        App.setStatus('li-status', 'error', 'Microphone error: ' + err.message);
      }
    } else {
      const fileInput = document.getElementById('li-file-input');
      if (!fileInput.files[0]) {
        App.setStatus('li-status', 'error', 'Please select a file first.');
        return;
      }
      try {
        App.setStatus('li-status', 'info', 'Uploading file...');
        const result = await App.uploadFile(fileInput);
        const socket = SocketManager.getSocket();
        socket.emit('li:start_file', { config: buildConfig(), temp_id: result.temp_id });
        isActive = true;
        showButtons('active');
      } catch (err) {
        App.setStatus('li-status', 'error', 'Upload error: ' + err.message);
      }
    }
  });

  // Pause
  document.getElementById('li-pause-btn').addEventListener('click', () => {
    SocketManager.getSocket().emit('li:pause');
    isPaused = true;
    showButtons('paused');
  });

  // Resume
  document.getElementById('li-resume-btn').addEventListener('click', () => {
    SocketManager.getSocket().emit('li:resume');
    isPaused = false;
    showButtons('active');
  });

  // Stop
  document.getElementById('li-stop-btn').addEventListener('click', () => {
    if (mic) {
      mic.stop();
      mic = null;
    }
    SocketManager.getSocket().emit('li:stop_mic');
    isActive = false;
    isPaused = false;
    showButtons('stopped');
  });

  // Download audio
  document.getElementById('li-download-btn').addEventListener('click', () => {
    SocketManager.getSocket().emit('li:download_audio');
  });

  // SocketIO events
  const socket = SocketManager.getSocket();

  socket.on('li:result', (data) => {
    appendResult(data);
  });

  socket.on('li:synth_audio', (data) => {
    if (playback) {
      playback.queueAudio(data.audio);
    }
  });

  socket.on('li:status', (data) => {
    App.setStatus('li-status', data.type, data.message);
  });

  socket.on('li:done', () => {
    isActive = false;
    showButtons('stopped');
  });

  socket.on('li:download_ready', (data) => {
    const binary = atob(data.audio);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    const blob = new Blob([bytes], { type: 'audio/wav' });
    const url = URL.createObjectURL(blob);

    const container = document.getElementById('li-audio-container');
    const player = document.getElementById('li-audio-player');
    player.src = url;
    container.style.display = '';

    const a = document.createElement('a');
    a.href = url;
    a.download = data.filename || 'translated_audio.wav';
    a.click();
  });
})();

