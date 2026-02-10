/**
 * Main application: tab switching, sidebar toggle, config management, theme.
 */

const App = (() => {
  // --- Config ---
  function getConfig() {
    return {
      speech_key: document.getElementById('cfg-speech-key').value,
      speech_region: document.getElementById('cfg-speech-region').value,
      api_key: document.getElementById('cfg-aoai-key').value,
      aoai_endpoint: document.getElementById('cfg-aoai-endpoint').value,
      aoai_deployment: document.getElementById('cfg-aoai-deployment').value,
      aoai_version: document.getElementById('cfg-aoai-version').value,
    };
  }

  // --- Status helpers ---
  function setStatus(elementId, type, message) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.className = 'status-bar ' + type;
    el.textContent = message;
  }

  function clearStatus(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.className = 'status-bar';
    el.textContent = '';
  }

  // --- File upload helper ---
  async function uploadFile(fileInput) {
    const file = fileInput.files[0];
    if (!file) return null;
    const formData = new FormData();
    formData.append('file', file);
    const resp = await fetch('/upload', { method: 'POST', body: formData });
    if (!resp.ok) throw new Error('Upload failed');
    return await resp.json();
  }

  // --- Theme ---
  function initTheme() {
    const stored = localStorage.getItem('ss_theme');
    let theme;
    if (stored === 'light' || stored === 'dark') {
      theme = stored;
    } else {
      theme = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    }
    applyTheme(theme);

    const toggle = document.getElementById('theme-toggle');
    if (toggle) {
      toggle.addEventListener('click', () => {
        const current = document.body.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        applyTheme(next);
        localStorage.setItem('ss_theme', next);
      });
    }
  }

  function applyTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    const icon = document.getElementById('theme-icon');
    const label = document.getElementById('theme-label');
    if (icon) icon.innerHTML = theme === 'dark' ? '&#9789;' : '&#9788;';
    if (label) label.textContent = theme === 'dark' ? 'Dark' : 'Light';
  }

  // --- Tab switching (with sub-tabs) ---
  function initTabs() {
    const buttons = document.querySelectorAll('#tabs .tab-btn');
    const panels = document.querySelectorAll('#main-content > .tab-panel');

    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        buttons.forEach(b => b.classList.remove('active'));
        panels.forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
      });
    });

    // Sub-tabs (segmented controls)
    document.querySelectorAll('.sub-tabs').forEach(container => {
      const subBtns = container.querySelectorAll('.sub-tab-btn');
      const group = container.closest('.tab-panel');
      const subPanels = group.querySelectorAll('.sub-panel');

      subBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          subBtns.forEach(b => b.classList.remove('active'));
          subPanels.forEach(p => p.classList.remove('active'));
          btn.classList.add('active');
          document.getElementById('tab-' + btn.dataset.subtab).classList.add('active');
        });
      });
    });
  }

  // --- Sidebar toggle ---
  function initSidebar() {
    const toggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    toggle.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
      toggle.textContent = sidebar.classList.contains('collapsed') ? '\u00bb' : '\u00ab';
    });

    // Persist config to sessionStorage (cleared when browser tab closes)
    const configFields = [
      'cfg-speech-key', 'cfg-speech-region',
      'cfg-aoai-key', 'cfg-aoai-endpoint', 'cfg-aoai-deployment', 'cfg-aoai-version',
    ];

    // Restore from sessionStorage (only if not already set by env)
    configFields.forEach(id => {
      const el = document.getElementById(id);
      const stored = sessionStorage.getItem('ss_' + id);
      if (stored && !el.value) {
        el.value = stored;
      }
      el.addEventListener('change', () => {
        sessionStorage.setItem('ss_' + id, el.value);
      });
      el.addEventListener('input', () => {
        sessionStorage.setItem('ss_' + id, el.value);
      });
    });

  }

  function init() {
    initTheme();
    initTabs();
    initSidebar();
  }

  // Scripts load at end of body — DOM is ready, init immediately
  init();

  return { getConfig, setStatus, clearStatus, uploadFile };
})();
