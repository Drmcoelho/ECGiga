/*
 * ECGiga PWA Registration & Install Prompt
 */

/* ------------------------------------------------------------------ */
/*  Register service worker                                           */
/* ------------------------------------------------------------------ */
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function () {
    navigator.serviceWorker
      .register('/assets/sw.js')
      .then(function (reg) {
        console.log('[PWA] Service worker registered, scope:', reg.scope);
      })
      .catch(function (err) {
        console.warn('[PWA] Service worker registration failed:', err);
      });
  });
}

/* ------------------------------------------------------------------ */
/*  Install prompt handling                                           */
/* ------------------------------------------------------------------ */
(function () {
  var deferredPrompt = null;

  // Capture the beforeinstallprompt event
  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault();
    deferredPrompt = e;
    showInstallBanner();
  });

  function showInstallBanner() {
    // Build the banner if it doesn't exist yet
    var banner = document.getElementById('pwa-install-banner');
    if (!banner) {
      banner = document.createElement('div');
      banner.id = 'pwa-install-banner';
      banner.className = 'pwa-install-banner';
      banner.setAttribute('role', 'alert');
      banner.innerHTML =
        '<div class="pwa-text">' +
          '<strong>Instalar ECGiga</strong>' +
          'Acesse rapidamente pelo seu celular, mesmo offline.' +
        '</div>' +
        '<button class="btn btn-primary btn-install" id="pwa-btn-install">' +
          'Instalar' +
        '</button>' +
        '<button class="btn-dismiss" id="pwa-btn-dismiss" aria-label="Fechar">' +
          '\u00D7' +
        '</button>';
      document.body.appendChild(banner);

      document.getElementById('pwa-btn-install').addEventListener('click', onInstallClick);
      document.getElementById('pwa-btn-dismiss').addEventListener('click', dismissBanner);
    }

    // Only show if user hasn't dismissed recently
    if (localStorage.getItem('pwa-install-dismissed')) {
      return;
    }

    // Show with slight delay so CSS transition fires
    requestAnimationFrame(function () {
      banner.classList.add('visible');
    });
  }

  function onInstallClick() {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    deferredPrompt.userChoice.then(function (choice) {
      if (choice.outcome === 'accepted') {
        console.log('[PWA] Install accepted');
      }
      deferredPrompt = null;
      hideBanner();
    });
  }

  function dismissBanner() {
    // Remember dismissal for 7 days
    localStorage.setItem('pwa-install-dismissed', Date.now().toString());
    hideBanner();
  }

  function hideBanner() {
    var banner = document.getElementById('pwa-install-banner');
    if (banner) {
      banner.classList.remove('visible');
    }
  }

  // Detect successful install
  window.addEventListener('appinstalled', function () {
    console.log('[PWA] App installed');
    deferredPrompt = null;
    hideBanner();
  });
})();
