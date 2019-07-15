//@flow
import * as React from 'react';
import { css } from '@emotion/core';

import { getLocale } from '../l10n.js';
import Login from './login.jsx';
import Logo from '../icons/logo.svg';
import MainMenu from './main-menu.jsx';
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

    return (
        <div css={styles.header}>
            <a
                css={styles.logoContainer}
                href={`/${locale}/`}
                aria-label={gettext('MDN Web Docs')}
            >
                <Logo css={styles.logo} />
            </a>
            {
                // The div below is used as a horizontal rule. We aren't
                // using a semantic <hr/> element because our document
                // stylesheets define a bunch of styles on <hr>.
            }
            <div css={styles.rule} />
            <MainMenu document={props.document} />
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
