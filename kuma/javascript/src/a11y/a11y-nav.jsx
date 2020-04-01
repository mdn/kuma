// @flow
import * as React from 'react';
import { useContext } from 'react';

import GAProvider from '../ga-provider.jsx';

import { gettext } from '../l10n.js';

export default function A11yNav() {
    const ga = useContext(GAProvider.context);

    /**
     * Send a signal to GA when there is an interaction on one
     * of the access menu links.
     * @param {Object} event - The event object that was fired
     */
    function sendAccessMenuItemClick(event) {
        const action = new URL(event.target.href).hash;
        const label = event.target.textContent;

        ga('send', {
            hitType: 'event',
            eventCategory: 'Access Links',
            eventAction: action,
            eventLabel: label,
        });
    }

    return (
        <ul id="nav-access">
            <li>
                <a
                    id="skip-main"
                    href="#content"
                    onClick={sendAccessMenuItemClick}
                    onContextMenu={sendAccessMenuItemClick}
                >
                    {gettext('Skip to main content')}
                </a>
            </li>
            <li>
                <a
                    id="skip-language"
                    href="#language"
                    onClick={sendAccessMenuItemClick}
                    onContextMenu={sendAccessMenuItemClick}
                >
                    {gettext('Select language')}
                </a>
            </li>
            <li>
                <a
                    id="skip-search"
                    href="#main-q"
                    onClick={sendAccessMenuItemClick}
                    onContextMenu={sendAccessMenuItemClick}
                >
                    {gettext('Skip to search')}
                </a>
            </li>
        </ul>
    );
}
