//@flow
import * as React from 'react';
import { useContext } from 'react';
import { css } from '@emotion/core';

import DocumentProvider from '../document-provider.jsx';
import LanguageMenu from './language-menu.jsx';
import Login from './login.jsx';
import Logo from '../icons/logo.svg';
import Dropdown from './dropdown.jsx';
import { Row, Spring, Strut } from '../layout.jsx';
import Search from './search.jsx';
import gettext from '../gettext.js';

const styles = {
    headerRow: css({
        borderTop: '4px solid #83d0f2',
        height: 64,
        boxSizing: 'border-box'
    }),
    logo: css({ display: 'block', height: 60 })
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

export default function Header(): React.Node {
    const documentData = useContext(DocumentProvider.context);
    if (!documentData) {
        return null;
    }
    const { localeFromURL } = documentData;

    function fixurl(url) {
        return url.startsWith('https://')
            ? url
            : `/${localeFromURL}/docs/${url}`;
    }

    return (
        <Row css={styles.headerRow}>
            <a css={styles.logo} href={`/${localeFromURL}/`}>
                <Logo alt="MDN Web Docs Logo" />
            </a>
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
            <LanguageMenu />
            <Spring />
            <Search />
            {/* search box here */}
            <Strut width={15} />
            <Login />
            <Strut width={15} />
        </Row>
    );
}
