/**
 * vanilla version of the function at:
 * https://github.com/mdn/kuma/blob/master/kuma/static/js/wiki.js#L252
 */
(function() {
    'use strict';

    /*
     * Bug 981409 - Add some CSS fallback for browsers without MathML support.
     *
     * This is based on:
     * https://developer.mozilla.org/en-US/docs/Web/MathML/Authoring#Fallback_for_Browsers_without_MathML_support
     * and https://github.com/fred-wang/mathml.css
     */
    var mathElements = document.querySelectorAll('math');
    // if no `math` elements on the page, bail
    if (!mathElements.length) {
        return;
    }

    /**
     * Returns a `math` element wrapped in a `div` that is positioned offscreen
     * @returns `div` element
     */
    function getMathElement() {
        var offscreenContainer = document.createElement('div');
        var mathMLNamespace = 'http://www.w3.org/1998/Math/MathML';
        var mathElement = document.createElementNS(mathMLNamespace, 'math');
        var mspaceElement = document.createElementNS(mathMLNamespace, 'mspace');

        mspaceElement.setAttribute('height', '23px');
        mspaceElement.setAttribute('width', '77px');

        mathElement.append(mspaceElement);
        offscreenContainer.append(mathElement);
        offscreenContainer.classList.add('offscreen');

        return offscreenContainer;
    }

    // Test for MathML support
    var mathMLTestElement = document.body.appendChild(getMathElement());
    var box = mathMLTestElement.querySelector('mspace').getBoundingClientRect();
    document.body.removeChild(mathMLTestElement);

    var supportsMathML =
        Math.abs(box.height - 23) <= 1 && Math.abs(box.width - 77) <= 1;
    if (!supportsMathML) {
        // Add CSS fallback
        var polyfill = document.createElement('link');
        polyfill.href = mdn.staticPath + 'styles/libs/mathml.css';
        polyfill.rel = 'stylesheet';
        polyfill.type = 'text/css';

        document.head.append(polyfill);

        // if we do not do this, React hydrate is unhappy and removes the element
        // Warning: Did not expect server HTML to contain a <div> in <div>.
        setTimeout(function() {
            // Add notification
            var wikiArticleContainer = document.getElementById('wikiArticle');
            var notice = document.createElement('div');
            var messageContainer = document.createElement('p');

            messageContainer.textContent =
                'Your browser does not support MathML. A CSS fallback has been used instead.';
            notice.append(messageContainer);
            notice.classList.add('notice');

            wikiArticleContainer.insertAdjacentElement('beforebegin', notice);
        }, 500);
    }
})();
