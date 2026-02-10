/**
 * Tab 6: LLM Speech (Transcribe & Translate)
 */
(() => {
  let currentTranslationLang = '';

  async function callApi(endpoint, fileInput, extraFields = {}) {
    const file = fileInput.files[0];
    if (!file) throw new Error('No file selected');

    const cfg = App.getConfig();
    const formData = new FormData();
    formData.append('file', file);
    formData.append('speech_key', cfg.speech_key);
    formData.append('speech_region', cfg.speech_region);
    for (const [k, v] of Object.entries(extraFields)) {
      formData.append(k, v);
    }

    const resp = await fetch(endpoint, { method: 'POST', body: formData });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || 'API request failed');
    return data;
  }

  // Transcribe
  document.getElementById('llm-transcribe-btn').addEventListener('click', async () => {
    const fileInput = document.getElementById('llm-file-input');
    if (!fileInput.files[0]) {
      App.setStatus('llm-status', 'error', 'Please upload an audio file first.');
      return;
    }

    const cfg = App.getConfig();
    if (!cfg.speech_key || !cfg.speech_region) {
      App.setStatus('llm-status', 'error', 'Missing Azure Speech Configuration.');
      return;
    }

    try {
      App.setStatus('llm-status', 'info', 'Transcribing via LLM Speech API...');
      const prompt = document.getElementById('llm-prompt').value;
      const data = await callApi('/api/llm-speech/transcribe', fileInput,
        prompt ? { prompt } : {});

      const combined = data.combinedPhrases || [];
      let fullText;
      if (combined.length > 0) {
        fullText = combined[0].text || '';
      } else {
        fullText = (data.phrases || []).map(p => p.text || '').join(' ');
      }

      document.getElementById('llm-transcript').value = fullText;
      document.getElementById('llm-transcript-section').style.display = '';

      // Phrase details
      const phrases = data.phrases || [];
      const phrasesEl = document.getElementById('llm-phrases');
      phrasesEl.innerHTML = '';
      if (phrases.length > 0) {
        phrases.forEach(p => {
          const div = document.createElement('div');
          div.className = 'phrase';
          const offset = (p.offsetMilliseconds || 0) / 1000;
          const dur = (p.durationMilliseconds || 0) / 1000;
          const locale = p.locale || '';
          div.innerHTML = `<strong>[${offset.toFixed(1)}s - ${(offset + dur).toFixed(1)}s]</strong> (${locale}) ${p.text || ''}`;
          phrasesEl.appendChild(div);
        });
        document.getElementById('llm-phrases-section').style.display = '';
      }

      App.setStatus('llm-status', 'success', 'Transcription complete.');
    } catch (err) {
      App.setStatus('llm-status', 'error', err.message);
    }
  });

  // Translate
  document.getElementById('llm-translate-btn').addEventListener('click', async () => {
    const fileInput = document.getElementById('llm-file-input');
    if (!fileInput.files[0]) {
      App.setStatus('llm-status', 'error', 'Please upload an audio file first.');
      return;
    }

    const cfg = App.getConfig();
    if (!cfg.speech_key || !cfg.speech_region) {
      App.setStatus('llm-status', 'error', 'Missing Azure Speech Configuration.');
      return;
    }

    const targetLang = document.getElementById('llm-target-lang').value;

    try {
      App.setStatus('llm-status', 'info', `Translating to ${targetLang} via LLM Speech API...`);
      const prompt = document.getElementById('llm-prompt').value;
      const fields = { target_language: targetLang };
      if (prompt) fields.prompt = prompt;
      const data = await callApi('/api/llm-speech/translate', fileInput, fields);

      const combined = data.combinedPhrases || [];
      let fullText;
      if (combined.length > 0) {
        fullText = combined[0].text || '';
      } else {
        fullText = (data.phrases || []).map(p => p.text || '').join(' ');
      }

      document.getElementById('llm-translation').value = fullText;
      document.getElementById('llm-translation-header').textContent =
        `Translation Result (${targetLang})`;
      document.getElementById('llm-translation-section').style.display = '';
      currentTranslationLang = targetLang;

      App.setStatus('llm-status', 'success', 'Translation complete.');
    } catch (err) {
      App.setStatus('llm-status', 'error', err.message);
    }
  });

  // Read Aloud
  document.getElementById('llm-read-aloud-btn').addEventListener('click', async () => {
    const text = document.getElementById('llm-translation').value;
    if (!text) return;

    const cfg = App.getConfig();
    if (!cfg.speech_key || !cfg.speech_region) {
      App.setStatus('llm-status', 'error', 'Missing Azure Speech Configuration.');
      return;
    }

    try {
      App.setStatus('llm-status', 'info', 'Synthesizing speech...');
      const resp = await fetch('/api/llm-speech/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          speech_key: cfg.speech_key,
          speech_region: cfg.speech_region,
          text: text,
          language_label: currentTranslationLang || 'English',
        }),
      });

      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.error || 'Synthesis failed');
      }

      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const player = document.getElementById('llm-audio-player');
      player.src = url;
      player.style.display = '';
      player.play();
      App.setStatus('llm-status', 'success', 'Playing audio...');
    } catch (err) {
      App.setStatus('llm-status', 'error', err.message);
    }
  });
})();
