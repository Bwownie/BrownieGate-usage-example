(function() {
    // If this page was opened as a popup by the main app:
    try {
    var opener = window.opener;
    // Only post back to same-origin opener to avoid security issues.
    if (opener && !opener.closed) {
        var targetOrigin = window.location.origin; // same-origin expected
        // Post minimal message to parent (no sensitive data)
        opener.postMessage({ type: 'browniegate_logged_in' }, targetOrigin);

        // Give the opener a moment and close the popup
        setTimeout(function(){ window.close(); }, 250);
    } else {
        // If there's no opener, navigate to the app home (fallback)
        window.location = "/";
    }
    } catch (e) {
    // If anything goes wrong, fallback to redirect
    try { window.location = "/"; } catch (err) { /* swallow */ }
    }
})();