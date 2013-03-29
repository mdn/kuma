// 1. Add jQuery.browser, which is no longer present in 1.9
jQuery.uaMatch = function( ua ) {
	ua = ua.toLowerCase();

	var rwebkit = /(webkit)[ \/]([\w.]+)/,
		ropera = /(opera)(?:.*version)?[ \/]([\w.]+)/,
		rmsie = /(msie) ([\w.]+)/,
		rmozilla = /(mozilla)(?:.*? rv:([\w.]+))?/,
		match = rwebkit.exec( ua ) ||
		ropera.exec( ua ) ||
		rmsie.exec( ua ) ||
		ua.indexOf("compatible") < 0 && rmozilla.exec( ua ) ||
		[];

	return { browser: match[1] || "", version: match[2] || "0" };
}
jQuery.browser = {};

(function() {
	var browserMatch = jQuery.uaMatch(navigator.userAgent);
	if ( browserMatch.browser ) {
		jQuery.browser[ browserMatch.browser ] = true;
		jQuery.browser.version = browserMatch.version;
	}

	// Deprecated, use jQuery.browser.webkit instead
	if ( jQuery.browser.webkit ) {
		jQuery.browser.safari = true;
	}
})();

// 2. Avoid c.curCSS is not a function error
jQuery.curCSS = jQuery.css;

// 3. outerHeight returns nodes, not a number; fix initialize
(function() {
	var outerHeight = jQuery.fn.outerHeight;
	jQuery.fn.outerHeight = function() {
		return outerHeight.call(this, true);
	}
	var outerWidth = jQuery.fn.outerWidth;
	jQuery.fn.outerWidth = function() {
		return outerWidth.call(this, true);
	}
})();