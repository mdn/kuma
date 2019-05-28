//@flow
import * as React from 'react';
import { useContext } from 'react';
import { css } from '@emotion/core';

import DocumentProvider from '../document-provider.jsx';
import { getLocale, gettext } from '../l10n.js';
import Login from './login.jsx';
import Logo from '../icons/logo.svg';
import Dropdown from './dropdown.jsx';
import { Row, Strut } from '../layout.jsx';
import Search from './search.jsx';

const DESKTOP = '@media (min-width: 1024px)';
const TABLET = '@media (min-width: 750px) and (max-width: 1023px)';
const PHONE = '@media (max-width: 749px)';

const styles = {
    loadingBar: css({
        height: 5,
        width: '100%',
        backgroundImage: 'linear-gradient(-271deg, #206584, #83d0f2)'
    }),
    header: css({
        display: 'grid',
        alignItems: 'center',
        fontSize: 15,
        margin: '0 16px',
        [DESKTOP]: {
            height: 68,
            gridTemplateColumns: '221px 5fr minmax(250px, 2fr) auto',
            gridTemplateAreas: '"I M S L"' // Icon Menus Search Login
        },

        [TABLET]: {
            height: 122,
            gridTemplateColumns: 'minmax(206px,1fr) 300px auto',
            gridTemplateAreas: '"I S L" "R R R" "M M M"'
        },

        [PHONE]: {
            fontSize: 10,
            gridTemplateColumns: 'repeat(4, 1fr)',
            gridTemplateAreas: '"I I L L" "S S S S" "M M M M"'
        }
    }),

    logoContainer: css({
        display: 'block',
        gridArea: 'I',
        width: 200,
        height: 44,
        marginRight: 24
    }),
    logo: css({
        width: 200,
        height: 44
    }),
    rule: css({
        // In tablet layout this rule separates the header menus below
        // from the logo and search box above. It is not included in
        // desktop layouts
        display: 'none',
        gridArea: 'R',
        height: 2,
        width: '100%',
        backgroundColor: '#dce3e5',
        [TABLET]: {
            display: 'block'
        }
    }),
    menus: css({
        gridArea: 'M',
        flexWrap: 'wrap',
        fontSize: 15,
        fontWeight: 'bold',
        button: {
            lineHeight: '32px'
        }
    }),
    search: css({
        gridArea: 'S',
        justifySelf: 'stretch'
    }),
    login: css({
        gridArea: 'L',
        justifySelf: 'end'
    })
};

const menus = [
    {
        label: 'Technologies',
        url: 'Web',
        items: [
            { url: 'Web/HTML', label: 'HTML' },
            { url: 'Web/CSS', label: 'CSS' },
            { url: 'Web/JavaScript', label: 'JavaScript' },
            { url: 'Web/Guide/Graphics', label: 'Graphics' },
            { url: 'Web/HTTP', label: 'HTTP' },
            { url: 'Web/API', label: 'APIs / DOM' },
            {
                url: 'Mozilla/Add-ons/WebExtensions',
                label: 'Browser Extensions'
            },
            { url: 'Web/MathML', label: 'MathML' }
        ]
    },
    {
        label: 'References & Guides',
        url: 'Learn',
        items: [
            { url: 'Learn', label: 'Learn web development' },
            { url: 'Web/Tutorials', label: 'Tutorials' },
            { url: 'Web/Reference', label: 'References' },
            { url: 'Web/Guide', label: 'Developer Guides' },
            { url: 'Web/Accessibility', label: 'Accessibility' },
            { url: 'Games', label: 'Game development' },
            { url: 'Web', label: '...more docs' }
        ]
    },
    {
        label: 'Feedback',
        url: 'MDN/Feedback',
        items: [
            {
                url: 'https://support.mozilla.org/',
                label: 'Get Firefox help',
                external: true
            },
            {
                url: 'https://stackoverflow.com/',
                label: 'Get web development help',
                external: true
            },
            { url: 'MDN/Community', label: 'Join the MDN community' },
            {
                label: 'Report a content problem',
                external: true,
                // See fixurl() for code that replaces the {{SLUG}}
                url:
                    'https://github.com/mdn/sprints/issues/new?template=issue-template.md&projects=mdn/sprints/2&labels=user-report&title={{SLUG}}'
            },
            {
                label: 'Report a bug',
                external: true,
                url: 'https://bugzilla.mozilla.org/form.mdn'
            }
        ]
    }
];

export default function Header(): React.Node {
    const documentData = useContext(DocumentProvider.context);
    const locale = getLocale();
    if (!documentData) {
        return null;
    }

    function fixurl(url) {
        // The "Report a content issue" menu item has a link that requires
        // the document slug, so we work that in here.
        url = url.replace('{{SLUG}}', encodeURIComponent(documentData.slug));
        if (!url.startsWith('https://')) {
            url = `/${locale}/docs/${url}`;
        }
        return url;
    }

    return (
        <>
            <div css={styles.loadingBar} />
            <div css={styles.header}>
                <a css={styles.logoContainer} href={`/${locale}/`}>
                    <Logo css={styles.logo} alt="MDN Web Docs Logo" />
                </a>
                {
                    // The div below is used as a horizontal rule. We aren't
                    // using a semantic <hr/> element because our document
                    // stylesheets define a bunch of styles on <hr>.
                }
                <div css={styles.rule} />
                <Row css={styles.menus}>
                    {menus.map((m, index) => (
                        <React.Fragment key={index}>
                            <Dropdown
                                label={
                                    <a href={fixurl(m.url)}>
                                        {gettext(m.label)}
                                    </a>
                                }
                            >
                                {m.items.map((item, index) => (
                                    <li key={index}>
                                        {item.external ? (
                                            <a
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                href={fixurl(item.url)}
                                            >
                                                {gettext(item.label)} &#x1f310;
                                            </a>
                                        ) : (
                                            <a href={fixurl(item.url)}>
                                                {gettext(item.label)}
                                            </a>
                                        )}
                                    </li>
                                ))}
                            </Dropdown>
                            {index < menus.length - 1 && <Strut width={16} />}
                        </React.Fragment>
                    ))}
                </Row>
                <div css={styles.search}>
                    <Search />
                </div>
                <div css={styles.login}>
                    <Login />
                </div>
            </div>
        </>
    );
}
