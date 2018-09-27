/**
 * Find all level two and three headings, and append a link
 * element that links directly to the heading
 */

(function() {
    'use strict';

    function prependLocalAnchors() {
        // collect all headings in wiki articles with an `id` attribute
        var headings = Array.from(document.querySelectorAll('#wikiArticle h2[id]')).concat(
            Array.from(document.querySelectorAll('#wikiArticle h3[id]'))
        );
        var pageUrl = document.location.href;

        for (var i = 0, l = headings.length; i < l; i++) {
            var currentHeading = headings[i];
            var localAnchorTag = document.createElement('a');
            var span = document.createElement('span');
            var link = window.mdnIcons ? window.mdnIcons.getIcon('link') : gettext('Link');

            localAnchorTag.classList.add('local-anchor');
            span.textContent = gettext('Section');
            localAnchorTag.appendChild(link);
            localAnchorTag.appendChild(span);

            // only append to headings that are not offscreen
            if (!currentHeading.classList.contains('offscreen')) {
                localAnchorTag.href = pageUrl + '#' + currentHeading.id;
                currentHeading.insertAdjacentElement('beforeend', localAnchorTag);
            }
        }
    }

    // `Array.from` is not supported in IE, progressively enhance
    if (typeof Array.from !== 'undefined') {
        window.addEventListener('load', function() {
            prependLocalAnchors();
        });
    }
})();
