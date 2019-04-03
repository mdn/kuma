//@flow
import * as React from 'react';
import { useContext } from 'react';
import { css } from '@emotion/core';

import DocumentProvider from '../document-provider.jsx';
import LanguageMenu from './language-menu.jsx';
import Login from './login.jsx';
import Logo from '../icons/logo.svg';
import Dropdown from './dropdown.jsx';
import { Row, Spring } from '../layout.jsx';
import Search from './search.jsx';
import gettext from '../gettext.js';

const DESKTOP = '@media (min-width: 1024px)';
const TABLET = '@media (min-width: 750px) and (max-width: 1023px)';
const PHONE = '@media (max-width: 749px)';

const styles = {
    header: css({
        borderTop: '4px solid #83d0f2',
        display: 'grid',
        alignItems: 'center',
        [DESKTOP]: {
            fontSize: 15,
            gridTemplateColumns: '274px 500px minmax(80px, 1fr) 125px',
            columnGap: '10px',
            gridTemplateAreas: '"I M S L"' // Icon Menus Search Login
        },

        [TABLET]: {
            fontSize: 12,
            gridTemplateColumns: 'repeat(10, 1fr)',
            columnGap: '5px',
            gridTemplateAreas: '"I I I S S S S S L L" "M M M M M M M M M M"'
        },

        [PHONE]: {
            fontSize: 10,
            gridTemplateColumns: 'repeat(4, 1fr)',
            gridTemplateAreas: '"I I L L" "S S S S" "M M M M"'
        }
    }),

    logoContainer: css({
        display: 'block',
        gridArea: 'I'
    }),
    logo: css({
        // header style sets 1em to 15, 12, or 10px
        height: '4em'
    }),
    menus: css({
        gridArea: 'M',
        flexWrap: 'wrap',
        margin: '0 5px',
        button: {
            [DESKTOP]: {
                fontSize: 16,
                fontWeight: 'bold',
                lineHeight: '32px'
            },

            [TABLET]: {
                fontSize: 14,
                fontWeight: 'bold',
                lineHeight: '28px'
            },

            [PHONE]: {
                fontSize: 12,
                fontWeight: 'normal',
                lineHeight: '24px'
            }
        }
    }),
    search: css({
        gridArea: 'S',
        margin: '2px 8px',
        justifySelf: 'stretch'
    }),
    login: css({
        gridArea: 'L',
        justifySelf: 'end',
        marginRight: 15
    })
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
        <div css={styles.header}>
            <a css={styles.logoContainer} href={`/${localeFromURL}/`}>
                <Logo css={styles.logo} alt="MDN Web Docs Logo" />
            </a>
            <Row css={styles.menus}>
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
                <Spring />
                <LanguageMenu />
            </Row>
            <div css={styles.search}>
                <Search />
            </div>
            <div css={styles.login}>
                <Login />
            </div>
        </div>
    );
}
