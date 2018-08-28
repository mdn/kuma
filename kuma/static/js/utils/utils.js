window.mdn.utils = {
    /**
     * From the jQuery source:
     * Get document-relative position by adding viewport scroll
     * to viewport-relative gBCR.
     * @param {Object} elem - The element for which to get the top offset
     * @returns {Number} The top offset of the element
     */
    getOffsetTop: function(elem) {
        'use strict';
        var boundingClientRect = elem.getBoundingClientRect();
        /* Get the window object associated with the
           top-level document object for this node */
        var elemDocumentWindow = elem.ownerDocument.defaultView;
        return boundingClientRect.top + elemDocumentWindow.pageYOffset;
    },
    /**
     * Generate and returns a random string thanks to:
     * https://stackoverflow.com/questions/1349404/generate-random-string-characters-in-javascript
     * @param {Number} [strLength] - The length of the string to return
     * @return {String} a randomly generated string with a chracter count of `strLength`
     */
    randomString: function(strLength) {
        'use strict';
        var length = strLength || 5;
        var possible =
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        var text = '';

        for (var i = 0; i < length; i++) {
            text += possible.charAt(
                Math.floor(Math.random() * possible.length)
            );
        }

        return text;
    },
    /**
     * Scroll the page to the location of the element with
     * the given `id`. Takes into account the space taken
     * up by the `#toc` to avoid overlap.
     * @param {String} id = The elements `id`
     */
    scrollToHeading: function(id) {
        'use strict';
        var heading = document.getElementById(id);
        var headingTop = mdn.utils.getOffsetTop(heading);
        var toc = document.getElementById('toc');
        var tocHeight = toc.offsetHeight;
        var scrollY = headingTop - tocHeight;

        // update hash
        window.location.hash = id;
        // scroll to heading
        window.scroll(0, scrollY);
    }
};
