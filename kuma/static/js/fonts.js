(function(win, $) {
    /*
        Font Loading
    */

    /*
        Note that sessionStorage is checked in the <head> to avoid font flicker.

        mdn.fonts is defined in font-check.js
    */

    var $html = $('html');

    // time to wait for each font varient to load
    var ffoTimeout = 2000;

    // loads all varients of a font
    // accepts a font object as defined in font-check.js
    function loadFont(fontObj) {
        // array to hold promises for each varient
        var varientPromises = [];
        // holds reference to an instance of FontFaceObserver in loop below
        var observer;

        // loop over each varient for the given font
        for (var i = 0, len = fontObj.varient.length; i < len; i++) {
            // instantiate new FontFaceObserver for the varient
            observer = new FontFaceObserver(fontObj.name, fontObj.varient[i]);
            // add the promise from the observer to the array
            // 1st argument is text to test font (not needed)
            // 2nd argument is amount of time to wait for font to load
            varientPromises.push(observer.load(null, ffoTimeout));
        }

        // make sure all varients load
        Promise.all(varientPromises).then(function() {
            // add attribute to <html> to trigger CSS changes
            $html.attr('data-' + fontObj.className, true);

            // remember that this font family has been loaded (font-check.js)
            try {
                sessionStorage.setItem(fontObj.name, true);
            } catch(e) {}
        });
    }

    // check each font - if not loaded, load using routing above
    for (var i = 0, len = win.mdn.fonts.length; i < len; i++) {
        if (!win.mdn.fonts[i].loaded) {
            loadFont(win.mdn.fonts[i]);
        }
    }
})(window, window.jQuery);
