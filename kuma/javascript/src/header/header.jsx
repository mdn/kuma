//@flow
import * as React from 'react';

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
        </header>
    );
}
