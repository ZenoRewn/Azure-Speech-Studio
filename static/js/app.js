/**
 * App shell: theme, tab routing, sidebar, config persistence, status helpers.
 * Preserves legacy IDs/classes so existing tab modules keep working.
 */

const App = (() => {
  // --- Config ---
  function getConfig() {
    const byId = (id) => (document.getElementById(id) ? document.getElementById(id).value : '');
    return {
      speech_key: byId('cfg-speech-key'),
      speech_region: byId('cfg-speech-region'),
      api_key: byId('cfg-aoai-key'),
      aoai_endpoint: byId('cfg-aoai-endpoint'),
      aoai_deployment: byId('cfg-aoai-deployment'),
      aoai_version: byId('cfg-aoai-version'),
      vl_endpoint: byId('cfg-vl-endpoint'),
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

  async function uploadFile(fileInput) {
    const file = fileInput.files[0];
    if (!file) return null;
    const formData = new FormData();
    formData.append('file', file);
    const resp = await fetch('/upload', { method: 'POST', body: formData });
    if (!resp.ok) throw new Error('Upload failed');
    return await resp.json();
  }

  // --- Theme (applied on <html>, so CSS `:root[data-theme]` and `body` both see it) ---
  function initTheme() {
    const stored = localStorage.getItem('ss_theme');
    const pref = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    const theme = (stored === 'light' || stored === 'dark') ? stored : pref;
    applyTheme(theme);

    const toggle = document.getElementById('theme-toggle');
    if (toggle) {
      toggle.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        applyTheme(next);
        localStorage.setItem('ss_theme', next);
      });
    }
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    // Keep body attribute too for legacy styles
    document.body.setAttribute('data-theme', theme);
    const icon = document.getElementById('theme-icon');
    const label = document.getElementById('theme-label');
    if (icon) icon.innerHTML = theme === 'dark' ? '&#9789;' : '&#9788;';
    if (label) label.textContent = theme === 'dark' ? 'Dark' : 'Light';
  }

  // --- Tabs ---
  function initTabs() {
    const buttons = document.querySelectorAll('#tabs .tab-btn, #tabs .tab-button');
    const panels = document.querySelectorAll('#main-content > .tab-panel');

    function activate(name) {
      buttons.forEach(b => b.classList.toggle('active', b.dataset.tab === name));
      panels.forEach(p => p.classList.toggle('active', p.id === 'tab-' + name));
      localStorage.setItem('ss_active_tab', name);
    }

    buttons.forEach(btn => {
      btn.addEventListener('click', () => activate(btn.dataset.tab));
    });

    const stored = localStorage.getItem('ss_active_tab');
    if (stored && document.getElementById('tab-' + stored)) activate(stored);

    // Sub-tabs
    document.querySelectorAll('.sub-tabs').forEach(container => {
      const subBtns = container.querySelectorAll('.sub-tab-btn, .sub-tab-button');
      const group = container.closest('.tab-panel') || document;
      const subPanels = group.querySelectorAll('.sub-panel');

      subBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          subBtns.forEach(b => b.classList.remove('active'));
          subPanels.forEach(p => p.classList.remove('active'));
          btn.classList.add('active');
          const target = document.getElementById('tab-' + btn.dataset.subtab);
          if (target) target.classList.add('active');
        });
      });
    });
  }

  // --- Sidebar + config persistence ---
  function initSidebar() {
    const toggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    if (toggle && sidebar) {
      const restored = localStorage.getItem('ss_sidebar_collapsed') === '1';
      if (restored) sidebar.classList.add('collapsed');
      toggle.textContent = sidebar.classList.contains('collapsed') ? '»' : '«';
      toggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
        const collapsed = sidebar.classList.contains('collapsed');
        toggle.textContent = collapsed ? '»' : '«';
        localStorage.setItem('ss_sidebar_collapsed', collapsed ? '1' : '0');
      });
    }

    const configFields = [
      'cfg-speech-key', 'cfg-speech-region',
      'cfg-aoai-key', 'cfg-aoai-endpoint', 'cfg-aoai-deployment', 'cfg-aoai-version',
      'cfg-vl-endpoint',
    ];
    configFields.forEach(id => {
      const el = document.getElementById(id);
      if (!el) return;
      const stored = sessionStorage.getItem('ss_' + id);
      if (stored && !el.value) el.value = stored;
      ['change', 'input'].forEach(evt =>
        el.addEventListener(evt, () => sessionStorage.setItem('ss_' + id, el.value))
      );
    });
  }

  function init() {
    initTheme();
    initTabs();
    initSidebar();
    if (window.Effects) window.Effects.init();
  }

  init();

  return { getConfig, setStatus, clearStatus, uploadFile, applyTheme };
})();
