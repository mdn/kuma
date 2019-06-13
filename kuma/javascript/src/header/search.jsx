//@flow
import * as React from 'react';
import { css } from '@emotion/core';

import { getLocale, gettext } from '../l10n.js';
import SearchIcon from '../icons/search.svg';

const styles = {
    container: css({
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        padding: '2px 8px',
        border: 'solid 2px #333',
        borderRadius: 20,
        backgroundColor: '#fafafa',
        boxSizing: 'border-box',
        height: 40,
        minWidth: 80,
        flex: '2 1'
    }),
    icon: css({
        fill: '#333',
        flex: '0 0 20px'
    }),
    input: css({
        // TODO: the !important declarations are used to override
        // stuff in the stylesheets. If we can simplify the
        // stylesheets, then maybe we can remove the importants
        borderWidth: '0 !important',
        fontSize: 14,
        flex: '1 1 100px',
        minWidth: 60,
        color: '#000',
        backgroundColor: '#fafafa !important'
    })
};

export default function Search() {
    const locale = getLocale();

    return (
        <form
            css={styles.container}
            id="nav-main-search"
            action={`/${locale}/search`}
            method="get"
            role="search"
        >
            <SearchIcon css={styles.icon} />

            <input
                css={styles.input}
                type="search"
                id="main-q"
                name="q"
                placeholder={gettext('Search MDN')}
            />
        </form>
    );
}
