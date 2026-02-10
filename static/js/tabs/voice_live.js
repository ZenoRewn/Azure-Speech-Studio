/**
 * Tab 5: Voice Live
 */
(() => {
  let mic = null;
  let playback = null;
  let isActive = false;

  // Parse embedded JSON data
  const modelTiers = JSON.parse(document.getElementById('vl-model-tiers-data').textContent);
  const voiceProviders = JSON.parse(document.getElementById('vl-voice-providers-data').textContent);

  // Cumulative usage tracking
  let cumulativeUsage = { total: 0, input: 0, output: 0 };

  function filterModels() {
    const tier = document.getElementById('vl-model-tier').value;
    const modelSelect = document.getElementById('vl-model');
    const models = modelTiers[tier] || [];
    modelSelect.innerHTML = '';
    models.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m;
      opt.textContent = m;
      modelSelect.appendChild(opt);
    });
  }

  function filterVoices() {
    const provider = document.getElementById('vl-voice-provider').value;
    const voiceSelect = document.getElementById('vl-voice');
    const voices = voiceProviders[provider] || {};
    voiceSelect.innerHTML = '';
    Object.entries(voices).forEach(([label, val]) => {
      const opt = document.createElement('option');
      opt.value = val;
      opt.textContent = label;
      voiceSelect.appendChild(opt);
    });
  }

  // Initialize dropdowns
  filterModels();
  filterVoices();

  document.getElementById('vl-model-tier').addEventListener('change', filterModels);
  document.getElementById('vl-voice-provider').addEventListener('change', filterVoices);

  function buildConfig() {
    const cfg = App.getConfig();
    return {
      vl_endpoint: cfg.aoai_endpoint,
      api_key: cfg.api_key,
      model: document.getElementById('vl-model').value,
      voice: document.getElementById('vl-voice').value,
      voice_provider: document.getElementById('vl-voice-provider').value,
      target_language: document.getElementById('vl-target-language').value,
      asr_model: document.getElementById('vl-asr-model').value,
      instructions: document.getElementById('vl-instructions').value,
    };
  }

  function resetStatsUI() {
    const ids = [
      'vl-stat-total', 'vl-stat-input', 'vl-stat-input-text', 'vl-stat-input-audio',
      'vl-stat-input-cached', 'vl-stat-output', 'vl-stat-output-text', 'vl-stat-output-audio',
      'vl-stat-cum-total', 'vl-stat-cum-input', 'vl-stat-cum-output',
    ];
    ids.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = '0';
    });
  }

  function updateStatsUI(usage) {
    const inputTokens = usage.input_tokens || 0;
    const outputTokens = usage.output_tokens || 0;
    const totalTokens = usage.total_tokens || (inputTokens + outputTokens);
    const inputDetails = usage.input_token_details || {};
    const outputDetails = usage.output_token_details || {};

    document.getElementById('vl-stat-total').textContent = totalTokens;
    document.getElementById('vl-stat-input').textContent = inputTokens;
    document.getElementById('vl-stat-input-text').textContent = inputDetails.text_tokens || 0;
    document.getElementById('vl-stat-input-audio').textContent = inputDetails.audio_tokens || 0;
    document.getElementById('vl-stat-input-cached').textContent = inputDetails.cached_tokens || 0;
    document.getElementById('vl-stat-output').textContent = outputTokens;
    document.getElementById('vl-stat-output-text').textContent = outputDetails.text_tokens || 0;
    document.getElementById('vl-stat-output-audio').textContent = outputDetails.audio_tokens || 0;

    cumulativeUsage.total += totalTokens;
    cumulativeUsage.input += inputTokens;
    cumulativeUsage.output += outputTokens;

    document.getElementById('vl-stat-cum-total').textContent = cumulativeUsage.total;
    document.getElementById('vl-stat-cum-input').textContent = cumulativeUsage.input;
    document.getElementById('vl-stat-cum-output').textContent = cumulativeUsage.output;
  }

  function appendTranscript(role, text) {
    const box = document.getElementById('vl-conversation');
    const msg = document.createElement('div');
    msg.className = 'msg msg-' + role;

    const label = document.createElement('span');
    label.className = 'msg-label';
    if (role === 'user') label.textContent = 'You:';
    else if (role === 'assistant') label.textContent = 'Assistant:';
    else label.textContent = 'Error:';

    msg.appendChild(label);
    msg.appendChild(document.createTextNode(' ' + text));
    box.appendChild(msg);
    box.scrollTop = box.scrollHeight;
  }

  // Start
  document.getElementById('vl-start-btn').addEventListener('click', async () => {
    const config = buildConfig();
    if (!config.vl_endpoint) {
      App.setStatus('vl-status', 'error', 'Please provide Azure OpenAI Endpoint in sidebar.');
      return;
    }
    if (!config.api_key) {
      App.setStatus('vl-status', 'error', 'Please provide Azure OpenAI API Key in sidebar.');
      return;
    }

    document.getElementById('vl-conversation').innerHTML = '';
    cumulativeUsage = { total: 0, input: 0, output: 0 };
    resetStatsUI();

    try {
      mic = new MicCapture(24000);
      playback = new AudioPlayback(24000);
      const socket = SocketManager.getSocket();

      mic.onAudioData = (buffer) => {
        socket.emit('vl:mic_audio', buffer);
      };
      await mic.start();
      socket.emit('vl:start', { config });

      isActive = true;
      document.getElementById('vl-start-btn').style.display = 'none';
      document.getElementById('vl-stop-btn').style.display = '';
    } catch (err) {
      App.setStatus('vl-status', 'error', 'Microphone error: ' + err.message);
    }
  });

  // Stop
  document.getElementById('vl-stop-btn').addEventListener('click', () => {
    if (mic) {
      mic.stop();
      mic = null;
    }
    if (playback) {
      playback.close();
      playback = null;
    }
    SocketManager.getSocket().emit('vl:stop');
    isActive = false;
    document.getElementById('vl-start-btn').style.display = '';
    document.getElementById('vl-stop-btn').style.display = 'none';
  });

  // SocketIO events
  const socket = SocketManager.getSocket();

  socket.on('vl:status', (data) => {
    App.setStatus('vl-status', data.type, data.message);
  });

  socket.on('vl:transcript', (data) => {
    appendTranscript(data.role, data.text);
  });

  socket.on('vl:playback_audio', (data) => {
    if (playback) {
      playback.queueAudio(data.audio);
    }
  });

  socket.on('vl:skip_audio', () => {
    if (playback) {
      playback.skipPending();
    }
  });

  socket.on('vl:usage', (data) => {
    updateStatsUI(data);
  });

  socket.on('vl:stopped', (data) => {
    App.setStatus('vl-status', 'warning', data.message);
    isActive = false;
    if (mic) {
      mic.stop();
      mic = null;
    }
    if (playback) {
      playback.close();
      playback = null;
    }
    document.getElementById('vl-start-btn').style.display = '';
    document.getElementById('vl-stop-btn').style.display = 'none';
  });
})();
