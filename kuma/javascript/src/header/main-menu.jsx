//@flow
import * as React from 'react';
import { useMemo, useEffect } from 'react';

import { getLocale, gettext } from '../l10n.js';

export default function MainMenu(mdnDocument: Object) {
    const locale = getLocale();

    // The menus array includes objects that define the set of
    // menus displayed by this header component. The data structure
    // is defined here during rendering so that the gettext() calls
    // happen after the string catalog is available. And we're using
    // useMemo() so that localization only happens when the locale
    // changes.
    const menus = useMemo(
        () => [
            {
                label: gettext('Technologies'),
                items: [
                    {
                        url: `/${locale}/docs/Web`,
                        label: gettext('Technologies Overview')
                    },
                    { url: `/${locale}/docs/Web/HTML`, label: gettext('HTML') },
                    { url: `/${locale}/docs/Web/CSS`, label: gettext('CSS') },
                    {
                        url: `/${locale}/docs/Web/JavaScript`,
                        label: gettext('JavaScript')
                    },
                    {
                        url: `/${locale}/docs/Web/Guide/Graphics`,
                        label: gettext('Graphics')
                    },
                    { url: `/${locale}/docs/Web/HTTP`, label: gettext('HTTP') },
                    {
                        url: `/${locale}/docs/Web/API`,
                        label: gettext('APIs / DOM')
                    },
                    {
                        url: `/${locale}/docs/Mozilla/Add-ons/WebExtensions`,
                        label: gettext('Browser Extensions')
                    },
                    {
                        url: `/${locale}/docs/Web/MathML`,
                        label: gettext('MathML')
                    }
                ]
            },
            {
                label: gettext('References & Guides'),
                items: [
                    {
                        url: `/${locale}/docs/Learn`,
                        label: gettext('Learn web development')
                    },
                    {
                        url: `/${locale}/docs/Web/Tutorials`,
                        label: gettext('Tutorials')
                    },
                    {
                        url: `/${locale}/docs/Web/Reference`,
                        label: gettext('References')
                    },
                    {
                        url: `/${locale}/docs/Web/Guide`,
                        label: gettext('Developer Guides')
                    },
                    {
                        url: `/${locale}/docs/Web/Accessibility`,
                        label: gettext('Accessibility')
                    },
                    {
                        url: `/${locale}/docs/Games`,
                        label: gettext('Game development')
                    },
                    {
                        url: `/${locale}/docs/Web`,
                        label: gettext('...more docs')
                    }
                ]
            },
            {
                label: gettext('Feedback'),
                items: [
                    {
                        url: `/${locale}/docs/MDN/Feedback`,
                        label: gettext('Send Feedback')
                    },
                    {
                        url: 'https://support.mozilla.org/',
                        label: gettext('Get Firefox help'),
                        external: true
                    },
                    {
                        url: 'https://stackoverflow.com/',
                        label: gettext('Get web development help'),
                        external: true
                    },
                    {
                        url: `/${locale}/docs/MDN/Community`,
                        label: gettext('Join the MDN community')
                    },
                    {
                        label: gettext('Report a content problem'),
                        external: true,
                        url:
                            'https://github.com/mdn/sprints/issues/new?template=issue-template.md&projects=mdn/sprints/2&labels=user-report&title={{PATH}}'
                    },
                    {
                        label: gettext('Report a bug'),
                        external: true,
                        url: 'https://bugzilla.mozilla.org/form.mdn'
                    }
                ]
            }
        ],
        [locale]
    );

    /**
     * Handles all interaction events
     * @param {Object} event - The Event object
     */
    function interactionHandler(event: SyntheticEvent<HTMLButtonElement>) {
        let mediaQuery = window.matchMedia('(min-width: 47.9375em)');
        let currentTarget = event.target;

        /* currentTarget instanceof 'HTMLButtonElement' is added
           to keep Flow happy: https://github.com/facebook/flow/issues/218#issuecomment-74119319 */
        if (
            (!mediaQuery.matches,
            event.type === 'touchstart' &&
                currentTarget instanceof HTMLButtonElement &&
                currentTarget.classList.contains('top-level-entry'))
        ) {
            if (currentTarget instanceof HTMLButtonElement) {
                let subMenu = currentTarget.nextElementSibling;

                if (subMenu) {
                    subMenu.classList.toggle('show');
                }
            }
        }
    }

    /**
     * Hide the visible submenu in main navigation
     */
    function hideVisibleSubMenu() {
        let visibleSubMenu = document.querySelector('ul.show');
        if (visibleSubMenu) {
            visibleSubMenu.classList.remove('show');
        }
    }

    useEffect(() => {
        const mediaQuery = window.matchMedia('(min-width: 47.9375em)');

        if (!mediaQuery.matches) {
            hideVisibleSubMenu();
        }
    }, [mdnDocument]);

    // One of the menu items has a URL that we need to substitute
    // the current mdnDocument path into. Compute that now.
    let path = encodeURIComponent(
        `/${locale}` + (mdnDocument ? `/docs/${mdnDocument.slug}` : '')
    );

    return (
        <nav
            onMouseOver={interactionHandler}
            onFocus={interactionHandler}
            onMouseOut={interactionHandler}
            onBlur={interactionHandler}
            onTouchStart={interactionHandler}
            className="main-nav"
            role="navigation"
        >
            <ul>
                {menus.map(menuEntry => (
                    <li
                        key={menuEntry.label}
                        className="top-level-entry-container"
                    >
                        <button
                            type="button"
                            className="top-level-entry"
                            aria-haspopup="true"
                        >
                            {menuEntry.label}
                            <span
                                className="main-menu-arrow"
                                aria-hidden="true"
                            >
                                ▼
                            </span>
                        </button>
                        <ul>
                            {menuEntry.items.map(item => (
                                <li
                                    key={item.url}
                                    data-item={menuEntry.label}
                                    role="menuitem"
                                >
                                    {item.external ? (
                                        <a
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            href={item.url.replace(
                                                '{{PATH}}',
                                                path
                                            )}
                                        >
                                            {item.label} &#x1f310;
                                        </a>
                                    ) : (
                                        <a href={item.url}>{item.label}</a>
                                    )}
                                </li>
                            ))}
                        </ul>
                    </li>
                ))}
            </ul>
        </nav>
    );
}
