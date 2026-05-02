/**
 * Tab 2: Fast Transcription (REST API)
 */
(() => {
  const langDetectSelect = document.getElementById('ft-lang-detect');
  const langSelectRow = document.getElementById('ft-lang-select-row');
  const diarizationCheckbox = document.getElementById('ft-diarization');
  const maxSpeakersLabel = document.getElementById('ft-max-speakers-label');

  langDetectSelect.addEventListener('change', () => {
    langSelectRow.style.display = langDetectSelect.value === 'Off' ? 'none' : '';
  });

  diarizationCheckbox.addEventListener('change', () => {
    maxSpeakersLabel.style.display = diarizationCheckbox.checked ? '' : 'none';
  });

  function getSelectedLanguages() {
    const sel = document.getElementById('ft-languages');
    return Array.from(sel.selectedOptions).map(o => o.value);
  }

  function getPhraseList() {
    const text = document.getElementById('ft-phrase-list').value.trim();
    if (!text) return [];
    return text.split('\n').map(s => s.trim()).filter(Boolean);
  }

  function buildConfig() {
    const cfg = App.getConfig();
    const language = document.getElementById('ft-source-language').value;
    return {
      speech_key: cfg.speech_key,
      speech_region: cfg.speech_region,
      language: language,
      diarization: diarizationCheckbox.checked,
      max_speakers: parseInt(document.getElementById('ft-max-speakers').value) || 4,
      lang_detect: langDetectSelect.value,
      languages: langDetectSelect.value !== 'Off' ? getSelectedLanguages() : [language],
      phrase_list: getPhraseList(),
    };
  }

  document.getElementById('ft-start-btn').addEventListener('click', async () => {
    const fileInput = document.getElementById('ft-file-input');
    if (!fileInput.files[0]) {
      App.setStatus('ft-status', 'error', 'Please select a file first.');
      return;
    }

    document.getElementById('ft-results').textContent = '';
    document.getElementById('ft-combined-section').style.display = 'none';
    document.getElementById('ft-combined').value = '';

    try {
      App.setStatus('ft-status', 'info', 'Uploading file...');
      const result = await App.uploadFile(fileInput);
      const socket = SocketManager.getSocket();
      socket.emit('ft:start_file', { config: buildConfig(), temp_id: result.temp_id });
    } catch (err) {
      App.setStatus('ft-status', 'error', 'Upload error: ' + err.message);
    }
  });

  const socket = SocketManager.getSocket();

  socket.on('ft:result', (data) => {
    const box = document.getElementById('ft-results');
    box.textContent += (box.textContent ? '\n' : '') + data.line;
    box.scrollTop = box.scrollHeight;
  });

  socket.on('ft:combined', (data) => {
    if (data.text) {
      document.getElementById('ft-combined').value = data.text;
      document.getElementById('ft-combined-section').style.display = '';
    }
  });

  socket.on('ft:status', (data) => {
    App.setStatus('ft-status', data.type, data.message);
  });

  socket.on('ft:done', () => {
    // Status is set by the server with details
  });
})();

