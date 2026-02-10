/**
 * Tab 3: Speech Translation
 */
(() => {
  let mic = null;
  let isActive = false;

  document.querySelectorAll('input[name="st-source"]').forEach(radio => {
    radio.addEventListener('change', () => {
      document.getElementById('st-file-section').style.display =
        radio.value === 'file' && radio.checked ? '' : 'none';
    });
  });

  function getSelectedSource() {
    return document.querySelector('input[name="st-source"]:checked').value;
  }

  function getTargetLanguages() {
    const sel = document.getElementById('st-target-langs');
    return Array.from(sel.selectedOptions).map(o => o.value);
  }

  function buildConfig() {
    const cfg = App.getConfig();
    const language = document.getElementById('st-source-language').value;
    return {
      speech_key: cfg.speech_key,
      speech_region: cfg.speech_region,
      language: language,
      target_languages: getTargetLanguages(),
    };
  }

  function appendResult(data) {
    const box = document.getElementById('st-results');
    const entry = document.createElement('div');
    entry.className = 'translation-entry';

    let html = `<div class="original"><strong>Original:</strong> ${data.text}</div>`;
    for (const [lang, text] of Object.entries(data.translations)) {
      html += `<div class="translated">&rarr; <em>${lang}</em>: ${text}</div>`;
    }
    entry.innerHTML = html;
    box.appendChild(entry);
    box.scrollTop = box.scrollHeight;
  }

  document.getElementById('st-start-btn').addEventListener('click', async () => {
    const source = getSelectedSource();
    document.getElementById('st-results').innerHTML = '';

    if (source === 'mic') {
      try {
        mic = new MicCapture(16000);
        const socket = SocketManager.getSocket();
        mic.onAudioData = (buffer) => {
          socket.emit('st:mic_audio', buffer);
        };
        await mic.start();
        socket.emit('st:start_mic', { config: buildConfig() });
        isActive = true;
        document.getElementById('st-start-btn').style.display = 'none';
        document.getElementById('st-stop-btn').style.display = '';
      } catch (err) {
        App.setStatus('st-status', 'error', 'Microphone error: ' + err.message);
      }
    } else {
      const fileInput = document.getElementById('st-file-input');
      if (!fileInput.files[0]) {
        App.setStatus('st-status', 'error', 'Please select a file first.');
        return;
      }
      try {
        App.setStatus('st-status', 'info', 'Uploading file...');
        const result = await App.uploadFile(fileInput);
        const socket = SocketManager.getSocket();
        socket.emit('st:start_file', { config: buildConfig(), temp_id: result.temp_id });
      } catch (err) {
        App.setStatus('st-status', 'error', 'Upload error: ' + err.message);
      }
    }
  });

  document.getElementById('st-stop-btn').addEventListener('click', () => {
    if (mic) {
      mic.stop();
      mic = null;
    }
    SocketManager.getSocket().emit('st:stop_mic');
    isActive = false;
    document.getElementById('st-start-btn').style.display = '';
    document.getElementById('st-stop-btn').style.display = 'none';
  });

  const socket = SocketManager.getSocket();

  socket.on('st:result', (data) => {
    appendResult(data);
  });

  socket.on('st:status', (data) => {
    App.setStatus('st-status', data.type, data.message);
  });

  socket.on('st:done', () => {
    App.setStatus('st-status', 'success', 'Translation complete.');
  });
})();
