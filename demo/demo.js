// Demo build only: explains what the demo is before the player starts.
(() => {
  const intro = document.getElementById('demo-intro');
  const boot = document.getElementById('boot');
  if (!intro || !boot) return;
  const close = () => { intro.hidden = true; document.removeEventListener('keydown', onKey, true); };

  document.getElementById('demo-try').addEventListener('click', () => { close(); boot.click(); });
  document.getElementById('demo-try').focus({ preventScroll: true });

  // keys that work the intro's own buttons stay here; any other key starts the player as usual
  function onKey(e) {
    if (intro.contains(document.activeElement) && ['Tab', 'Enter', ' '].includes(e.key)) { e.stopPropagation(); return; }
    if (!e.ctrlKey && !e.metaKey && !e.altKey) close();
  }
  document.addEventListener('keydown', onKey, true);

  // a gamepad button can also start the player
  new MutationObserver(() => { if (boot.classList.contains('gone')) close(); }).observe(boot, { attributes: true });
})();
