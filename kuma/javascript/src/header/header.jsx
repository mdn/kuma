//@flow
import * as React from 'react';
import { css } from '@emotion/core';

import { getLocale, gettext } from '../l10n.js';
import Login from './login.jsx';
import Logo from '../icons/logo.svg';
import MainMenu from './main-menu.jsx';
import Search from './search.jsx';

import type { DocumentData } from '../document.jsx';

type Props = {
    document?: ?DocumentData,
    searchQuery?: string
};

export default function Header(props: Props): React.Node {
    const locale = getLocale();

    return (
        <header className="page-header">
            <a
                href={`/${locale}/`}
                className="logo"
                aria-label={gettext('MDN Web Docs')}
            >
                <Logo />
            </a>
            <MainMenu document={props.document} locale={locale} />
            <Search initialQuery={props.searchQuery || ''} />
            <Login />

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
        </header>
    );
}
