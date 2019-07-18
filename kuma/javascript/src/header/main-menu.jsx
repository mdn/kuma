//@flow
import * as React from 'react';
import { memo, useEffect, useMemo, useState } from 'react';

import { gettext } from '../l10n.js';
import type { DocumentData } from '../document.jsx';

type Props = {
    document?: ?DocumentData,
    locale: string
};

// To avoid problems with flow and React.memo(), define the component
// in this plain way first. See bottom of file for the final memo() and export.
const _MainMenu = ({ document, locale }: Props) => {
    // The CSS that supports this is sufficiently smart to understand
    // hovering over the top-level menu items and stuff. But for mobile,
    // there's no mouse hover so for that we use a piece of state to
    // record onTouchStart events.
    const [showSubMenu, setShowSubMenu] = useState(null);
    // console.log('RENDERING _MainMenu', showSubMenu);

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
                    {
                        url: `/${locale}/docs/Web/HTML`,
                        label: gettext('HTML')
                    },
                    {
                        url: `/${locale}/docs/Web/CSS`,
                        label: gettext('CSS')
                    },
                    {
                        url: `/${locale}/docs/Web/JavaScript`,
                        label: gettext('JavaScript')
                    },
                    {
                        url: `/${locale}/docs/Web/Guide/Graphics`,
                        label: gettext('Graphics')
                    },
                    {
                        url: `/${locale}/docs/Web/HTTP`,
                        label: gettext('HTTP')
                    },
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

    // For Desktop, we don't need any JavaScript to make the menu behave
    // nicely. But for mobile, we're using the onTouchStart event to
    // update state that tells the menu to start with className="show".
    // However, if that mobile user opened a menu (with onTouchStart) and
    // decided to click on of the links, there's no good chance to now
    // hide what was forcibly shown. So we use the first mount effect to
    // make it so that it hides the menu if it was shown.
    // To a mobile user, the effect is that after their click (on a sub-menu
    // item) has completed, it manually closes the menu.
    useEffect(() => {
        if (showSubMenu) {
            setShowSubMenu(null);
        }
        // TODO: react-hooks/exhaustive-deps will say to include showSubMenu
        // in list of dependencies. But if you do that, you won't be able
        // to distinguish between a new mount (navigating to a new document
        // for example) and the menu having been shown.
        // We only want this effect to run when the component is re-rendered
        // with a new 'document'.
    }, [document]); // eslint-disable-line react-hooks/exhaustive-deps

    // One of the menu items has a URL that we need to substitute
    // the current document path into. Compute that now.
    let path = encodeURIComponent(
        `/${locale}` + (document ? `/docs/${document.slug}` : '')
    );

    return (
        <nav className="main-nav" role="navigation">
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
                            onTouchStart={() => {
                                // Ultimately, because there's no :hover on
                                // mobile, we have to compensate for that using
                                // JavaScript.
                                setShowSubMenu(
                                    showSubMenu === menuEntry.label
                                        ? null
                                        : menuEntry.label
                                );
                            }}
                        >
                            {menuEntry.label}
                            <span
                                className="main-menu-arrow"
                                aria-hidden="true"
                            >
                                ▼
                            </span>
                        </button>
                        <ul
                            className={
                                menuEntry.label === showSubMenu ? 'show' : null
                            }
                        >
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
};

const MainMenu = memo<Props>(_MainMenu);
export default MainMenu;
