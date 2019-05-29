window.mdn.utils = {
    isTocSticky: false,
    tocHeight: 0,
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
        var top = boundingClientRect.top;
        var yOffset = parseInt(elemDocumentWindow.pageYOffset, 10);
        return top + yOffset;
    },
    /**
     * Scroll the page to the location of the element with
     * the given `id`. Takes into account the space taken
     * up by the `#toc` to avoid overlap.
     * @param {String} id = The elements `id`
     */
    scrollToHeading: function(id) {
        'use strict';
        var toc = document.getElementById('toc');

        // if page has a TOC,
        if (toc) {
            // get and store the `offsetHeight`
            this.tocHeight = toc.offsetHeight;
            // and its sticky status
            this.isTocSticky = getComputedStyle(toc).position === 'sticky';
        }

        var heading = document.getElementById(id);
        var headingTop = mdn.utils.getOffsetTop(heading);
        var scrollY = 0;

        // if the toc is sticky
        if (toc && this.isTocSticky) {
            scrollY = headingTop - this.tocHeight;
        } else {
            scrollY = headingTop;
        }

        // update hash
        window.location.hash = id;
        // scroll to heading
        window.scroll(0, parseInt(scrollY, 10));
    }
};
