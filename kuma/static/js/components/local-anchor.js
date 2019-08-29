/**
 * Find all level two and three headings, and append a link
 * element that links directly to the heading
 *
 * See also the React version of this code in the addAnchors() function
 * of kuma/javascript/src/article.jsx
 */

(function () {
    'use strict';

    function prependLocalAnchors() {
        var mainDocument = document.getElementById('document-main');

        // if no `mainDocument`, skip because we're on an edit page
        if (!mainDocument) {
            return;
        }

        // collect all headings with an `id` attribute
        var headings = Array.from(document.querySelectorAll('h2[id]')).concat(
            Array.from(document.querySelectorAll('h3[id]'))
        );
        var pageUrl = new URL(document.location.href);

        // if the pageUrl containes a hash, clear it
        if (pageUrl.hash) {
            pageUrl.hash = '';
        }

        for (var i = 0, l = headings.length; i < l; i++) {
            var currentHeading = headings[i];
            var localAnchorTag = document.createElement('a');
            var span = document.createElement('span');
            var link = window.mdnIcons
                ? window.mdnIcons.getIcon('link')
                : gettext('Link');

            localAnchorTag.classList.add('local-anchor');
            span.textContent = gettext('Section');
            localAnchorTag.appendChild(link);
            localAnchorTag.appendChild(span);

            // only append to headings that are not offscreen
            if (!currentHeading.classList.contains('offscreen')) {
                pageUrl.hash = currentHeading.id;
                localAnchorTag.href = pageUrl;
                localAnchorTag.dataset.headingId = currentHeading.id;
                currentHeading.insertAdjacentElement(
                    'beforeend',
                    localAnchorTag
                );
            }
        }

        // listen for right clicks
        mainDocument.addEventListener('contextmenu', function (event) {
            // if it was on a section link
            if (event.target.classList && event.target.classList.contains('local-anchor')) {
                // send event to GA
                mdn.analytics.trackEvent({
                    category: 'MDN UI',
                    action: 'Right click on section link',
                    label: 'Section-Link-Right-Click'
                });
            }
        });

        mainDocument.addEventListener('click', function (event) {
            var target = event.target;

            // only handle clicks on anchor elements
            if (target.tagName === 'A') {
                /* getting the attribute value as apposed to the target property
                   to ensure we get the actual text value of the attribute */
                var hrefAttrValue = target.getAttribute('href');
                var isInDocumentLink = hrefAttrValue.startsWith('#');

                var headingId = isInDocumentLink
                    ? hrefAttrValue.substr(1)
                    : target.dataset.headingId;
                /* only handle clicks on in document links or, that originated from
                   a `local-anchor` */
                if (
                    target.classList.contains('local-anchor') ||
                    isInDocumentLink
                ) {
                    event.preventDefault();
                    mdn.utils.scrollToHeading(headingId);
                    // send left click events to GA
                    mdn.analytics.trackEvent({
                        category: 'MDN UI',
                        action: 'Click on section link',
                        label: 'Section-Link-Click'
                    });
                }
            }
        });
    }

    // `Array.from` is not supported in IE, progressively enhance
    if (typeof Array.from !== 'undefined') {
        window.addEventListener('load', function () {
            prependLocalAnchors();
        });
    }
})();
