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
     * Tests whether MathML is supported(at least in terms of mspace),
     * and returns true or false.
     * @returns {Boolean} isMathMLSupported
     */
    function isMathMLSupported() {
        var box = null;
        var mathMLTestElement = null;
        var offscreenContainer = document.createElement('div');
        var mathMLNamespace = 'http://www.w3.org/1998/Math/MathML';
        var mathElement = document.createElementNS(mathMLNamespace, 'math');
        var mspaceElement = document.createElementNS(mathMLNamespace, 'mspace');

        mspaceElement.setAttribute('height', '23px');
        mspaceElement.setAttribute('width', '77px');

        mathElement.append(mspaceElement);
        offscreenContainer.append(mathElement);
        offscreenContainer.classList.add('offscreen');

        mathMLTestElement = document.body.appendChild(offscreenContainer);
        box = mathMLTestElement.querySelector('mspace').getBoundingClientRect();
        document.body.removeChild(mathMLTestElement);

        return Math.abs(box.height - 23) <= 1 && Math.abs(box.width - 77) <= 1;
    }

    if (!isMathMLSupported()) {
        // Add CSS fallback
        var polyfill = document.createElement('link');
        polyfill.href = mdn.staticPath + 'styles/libs/mathml.css';
        polyfill.rel = 'stylesheet';
        polyfill.type = 'text/css';

        document.head.append(polyfill);
    }
})();
