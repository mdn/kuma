//@flow
import * as React from 'react';
import { useMemo } from 'react';
import { css } from '@emotion/core';

import { getLocale, gettext } from '../l10n.js';
import Login from './login.jsx';
import Logo from '../icons/logo.svg';
import Dropdown from './dropdown.jsx';
import { Row, Strut } from '../layout.jsx';
import Search from './search.jsx';

import type { DocumentData } from '../document.jsx';

const DESKTOP = '@media (min-width: 1024px)';
const TABLET = '@media (min-width: 750px) and (max-width: 1023px)';
const PHONE = '@media (max-width: 749px)';

const styles = {
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

type Props = {
    document?: ?DocumentData,
    searchQuery?: string
};

export default function Header(props: Props): React.Node {
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
                url: `/${locale}/docs/Web`,
                items: [
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
                url: `/${locale}/docs/Learn`,
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
                url: `/${locale}/docs/MDN/Feedback`,
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

    // One of the menu items has a URL that we need to substitute
    // the current document path into. Compute that now.
    let path = encodeURIComponent(
        `/${locale}` + (props.document ? `/docs/${props.document.slug}` : '')
    );

    return (
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
                        <Dropdown label={<a href={m.url}>{m.label}</a>}>
                            {m.items.map((item, index) => (
                                <li key={index}>
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
                        </Dropdown>
                        {index < menus.length - 1 && <Strut width={16} />}
                    </React.Fragment>
                ))}
            </Row>
            <div css={styles.search}>
                <Search initialQuery={props.searchQuery || ''} />
            </div>
            <div css={styles.login}>
                <Login />
            </div>

            {
                // Display a "Beta Feedback" banner.
                // When we're done with beta testing, remove this <a> tag
                // by reverting https://github.com/mozilla/kuma/pull/5511
            }
            <a
                href="https://bugzilla.mozilla.org/show_bug.cgi?id=1561020"
                target="_blank"
                rel="noopener noreferrer nofollow"
                css={css({
                    boxSizing: 'border-box',
                    position: 'absolute',
                    display: 'block',
                    top: 0,
                    left: 0,
                    width: 99,
                    height: 99,
                    zIndex: 100,
                    transform: 'translate(-49.5px, -49.5px) rotate(-45deg)',
                    backgroundColor: 'rgba(255,255,0,0.85)',
                    border: 'solid black 1px',
                    boxShadow: '0px 3px 10px #000',
                    fontWeight: 'bold',
                    textAlign: 'center',
                    lineHeight: '1.0',
                    fontSize: 12.5,
                    paddingTop: 68,
                    color: 'black',
                    ':hover': {
                        backgroundColor: '#ff0',
                        textDecoration: 'none'
                    }
                })}
            >
                Beta
                <br />
                Feedback
            </a>
        </div>
    );
}
