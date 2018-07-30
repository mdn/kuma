/**
 * Find all level two and three headings, and append a link
 * element that links directly to the heading
 */
function prependLocalAnchors() {
    'use strict';

    // collect all headings with an `id` attribute
    var headings = Array.from(document.querySelectorAll('h2[id]')).concat(
        Array.from(document.querySelectorAll('h3[id]'))
    );
    var pageUrl = document.location.href;

    for (var i = 0, l = headings.length; i < l; i++) {
        var currentHeading = headings[i];
        var localAnchorTag = document.createElement('a');
        var span = document.createElement('span');

        localAnchorTag.classList.add('local-anchor');
        span.textContent = gettext('Link to section');
        localAnchorTag.appendChild(span);

        // only append to headings that are not offscreen
        if (!currentHeading.classList.contains('offscreen')) {
            localAnchorTag.href = pageUrl + '#' + currentHeading.id;
            currentHeading.insertAdjacentElement('afterbegin', localAnchorTag);
        }
    }
}

// `Array.from` is not supported in IE, progressively enhance
if (typeof Array.from !== 'undefined') {
    window.addEventListener('load', function() {
        prependLocalAnchors();
    });
}
