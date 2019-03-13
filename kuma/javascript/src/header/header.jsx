//@flow
import * as React from 'react';
import { css } from '@emotion/core';

import LanguageIcon from '../icons/language.svg';
import Login from './login.jsx';
import Logo from './logo.jsx';
import Dropdown from './dropdown.jsx';
import { Row, Spring, Strut } from '../layout.jsx';
import Search from './search.jsx';
import gettext from '../gettext.js';

const styles = {
    headerRow: css({ borderTop: '5px solid #83d0f2' })
};

const menus = [
    {
        label: gettext('Technologies'),
        items: [
            { url: 'Web/HTML', label: gettext('HTML') },
            { url: 'Web/CSS', label: gettext('CSS') },
            { url: 'Web/JavaScript', label: gettext('JavaScript') },
            { url: 'Web/Guide/Graphics', label: gettext('Graphics') },
            { url: 'Web/HTTP', label: gettext('HTTP') },
            { url: 'Web/API', label: gettext('APIs / DOM') },
            {
                url: 'Mozilla/Add-ons/WebExtensions',
                label: gettext('Browser Extensions')
            },
            { url: 'Web/MathML', label: gettext('MathML') }
        ]
    },
    {
        label: gettext('References & Guides'),
        items: [
            { url: 'Learn', label: gettext('Learn web development') },
            { url: 'Web/Tutorials', label: gettext('Tutorials') },
            { url: 'Web/Reference', label: gettext('References') },
            { url: 'Web/Guide', label: gettext('Developer Guides') },
            { url: 'Web/Accessibility', label: gettext('Accessibility') },
            { url: 'Games', label: gettext('Game development') },
            { url: 'Web', label: gettext('...more docs') }
        ]
    },
    {
        label: gettext('Feedback'),
        items: [
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
            { url: 'MDN/Community', label: gettext('Join the MDN community') },
            {
                label: gettext('Report a content problem'),
                external: true,
                url: `https://github.com/mdn/sprints/issues/new?template=issue-template.md&projects=mdn/sprints/2&labels=user-report&title=${encodeURIComponent(
                    window.location
                )}`
            },
            {
                label: gettext('Report a bug'),
                external: true,
                url: 'https://bugzilla.mozilla.org/form.mdn'
            }
        ]
    }
];

function fixurl(url) {
    if (url.startsWith('https://')) {
        return url;
    } else {
        let locale = window.location.pathname.split('/')[1];
        return `/${locale}/docs/${url}`;
    }
}

const LOCALE =
    window && window.location && window.location.pathname.split('/')[1];
const HOME_URL = LOCALE ? `/${LOCALE}/` : '/en-US/';

export default function Header(): React.Node {
    return (
        <Row css={styles.headerRow}>
            <Logo url={HOME_URL} />
            <Strut width={4} />
            {menus.map((m, index) => (
                <Dropdown label={m.label} key={index}>
                    {m.items.map((item, index) => (
                        <li key={index}>
                            {item.external ? (
                                <a
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    href={fixurl(item.url)}
                                >
                                    {item.label} &#x1f310;
                                </a>
                            ) : (
                                <a href={fixurl(item.url)}>{item.label}</a>
                            )}
                        </li>
                    ))}
                </Dropdown>
            ))}
            {
                // We should have a LanguageMenu component here.
                // We can get available languages from the $json query.
                // Maybe do anohter context/provider thing and set the
                // available set of translations on that, then update
                // on document load and on every client-side navigation?
            }
            <Dropdown label={<LanguageIcon />}>
                <li>Not yet implemented</li>
            </Dropdown>
            <Spring />
            <Search />
            {/* search box here */}
            <Strut width={15} />
            <Login />
            <Strut width={15} />
        </Row>
    );
}
