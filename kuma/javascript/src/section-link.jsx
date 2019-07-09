import * as React from 'react';
import { render } from 'react-dom';

import { gettext } from './l10n.js';

import Anchor from './icons/anchor.svg';

/**
 * Returns a section anchor element with a nested SVG icon
 * @param {Object} heading - The current heading DOM node
 * @returns section anchor element as an HTML element
 */
export default function sectionAnchor(heading) {
    const anchor = document.createElement('a');
    anchor.href = `#${heading.id}`;
    anchor.classList.add('section-link');
    // heading.innerText is the current heading and will already be translated
    anchor.setAttribute('aria-label', gettext('Link to ') + heading.innerText);
    // render the SVG into the anchor element
    render(<Anchor />, anchor);
    return anchor;
}
