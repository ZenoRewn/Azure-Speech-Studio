/**
 * Tab 1: Realtime STT
 */
(() => {
  let mic = null;
  let isRecording = false;

  const langDetectSelect = document.getElementById('rt-lang-detect');

  // Show/hide file input based on source
  document.querySelectorAll('input[name="rt-source"]').forEach(radio => {
    radio.addEventListener('change', () => {
      document.getElementById('rt-file-section').style.display =
        radio.value === 'file' && radio.checked ? '' : 'none';
    });
  });

  function getSelectedSource() {
    return document.querySelector('input[name="rt-source"]:checked').value;
  }

  function getSelectedLanguages() {
    const sel = document.getElementById('rt-languages');
    return Array.from(sel.selectedOptions).map(o => o.value);
  }

  function getPhraseList() {
    const text = document.getElementById('rt-phrase-list').value.trim();
    if (!text) return [];
    return text.split('\n').map(s => s.trim()).filter(Boolean);
  }

  function buildConfig() {
    const cfg = App.getConfig();
    const language = document.getElementById('rt-source-language').value;
    return {
      speech_key: cfg.speech_key,
      speech_region: cfg.speech_region,
      language: language,
      diarization: document.getElementById('rt-diarization').checked,
      lang_detect: langDetectSelect.value,
      languages: getSelectedLanguages().length > 0 ? getSelectedLanguages() : [language],
      phrase_list: getPhraseList(),
    };
  }

  // Start button
  document.getElementById('rt-start-btn').addEventListener('click', async () => {
    const source = getSelectedSource();
    document.getElementById('rt-results').textContent = '';

    if (source === 'mic') {
      try {
        mic = new MicCapture(16000);
        const socket = SocketManager.getSocket();
        mic.onAudioData = (buffer) => {
          socket.emit('rt:mic_audio', buffer);
        };
        await mic.start();
        socket.emit('rt:start_mic', { config: buildConfig() });
        isRecording = true;
        document.getElementById('rt-start-btn').style.display = 'none';
        document.getElementById('rt-stop-btn').style.display = '';
      } catch (err) {
        App.setStatus('rt-status', 'error', 'Microphone error: ' + err.message);
      }
    } else {
      // File mode
      const fileInput = document.getElementById('rt-file-input');
      if (!fileInput.files[0]) {
        App.setStatus('rt-status', 'error', 'Please select a file first.');
        return;
      }
      try {
        App.setStatus('rt-status', 'info', 'Uploading file...');
        const result = await App.uploadFile(fileInput);
        const socket = SocketManager.getSocket();
        socket.emit('rt:start_file', { config: buildConfig(), temp_id: result.temp_id });
      } catch (err) {
        App.setStatus('rt-status', 'error', 'Upload error: ' + err.message);
      }
    }
  });

  // Stop button
  document.getElementById('rt-stop-btn').addEventListener('click', () => {
    if (mic) {
      mic.stop();
      mic = null;
    }
    SocketManager.getSocket().emit('rt:stop_mic');
    isRecording = false;
    document.getElementById('rt-start-btn').style.display = '';
    document.getElementById('rt-stop-btn').style.display = 'none';
  });

  // SocketIO events — register directly (scripts load at end of body)
  const socket = SocketManager.getSocket();

  socket.on('rt:result', (data) => {
    const box = document.getElementById('rt-results');
    box.textContent += (box.textContent ? '\n' : '') + data.line;
    box.scrollTop = box.scrollHeight;
  });

  socket.on('rt:status', (data) => {
    App.setStatus('rt-status', data.type, data.message);
  });

  socket.on('rt:done', () => {
    App.setStatus('rt-status', 'success', 'File processing complete.');
  });
})();

