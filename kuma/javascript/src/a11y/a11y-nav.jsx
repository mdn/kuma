// @flow
import * as React from 'react';

import { gettext } from '../l10n.js';

export default function A11yNav() {
    return (
        <ul id="nav-access">
            <li>
                <a id="skip-main" href="#content">
                    {gettext('Skip to main content')}
                </a>
            </li>
            <li>
                <a id="skip-language" href="#language">
                    {gettext('Select language')}
                </a>
            </li>
            <li>
                <a id="skip-search" href="#main-q">
                    {gettext('Skip to search')}
                </a>
            </li>
        </ul>
    );
}
