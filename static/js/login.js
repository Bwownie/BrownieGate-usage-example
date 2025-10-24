// static/js/login.js
// Expects window.BG_CONFIG to be present (injected by the template).
// Keeps the popup login logic separated from the template markup.

(function () {
	// Defensive defaults in case BG_CONFIG isn't provided
	var cfg = window.BG_CONFIG || {};
	var authUrl = cfg.authUrl || '/login';
	var popupFeatures = cfg.popupFeatures || 'width=500,height=700,menubar=no,toolbar=no,location=yes,resizable=yes,scrollbars=yes,status=no';

	// Wait for DOM ready to ensure the button exists
	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}

	function init() {
		var loginBtn = document.getElementById('bg-login-btn');
		if (!loginBtn) return;

		loginBtn.addEventListener('click', function (e) {
			e.preventDefault();

			// Open popup in direct click handler (avoids popup blockers)
			var popup = window.open(authUrl, 'browniegate_login', popupFeatures);

			if (!popup) {
				// Popup blocked -> fallback to full redirect
				window.location = authUrl;
				return;
			}

			// Handler for postMessage from popup
			function onMessage(e) {
				try {
					// Only accept messages from same origin (our app)
					if (e.origin !== window.location.origin) return;
					if (e.data && e.data.type === 'browniegate_logged_in') {
						window.removeEventListener('message', onMessage);
						// Cookie was set by popup response; reload to pick up session and authenticated UI
						window.location.reload();
					}
				} catch (err) {
					// ignore and continue
				}
			}

			window.addEventListener('message', onMessage, false);
		});
	}
})();