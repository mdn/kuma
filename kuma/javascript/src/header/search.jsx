//@flow
import * as React from 'react';
import { css } from '@emotion/core';

import gettext from '../gettext.js';
import SearchIcon from '../icons/search.svg';

const strings = {
    placeholder: gettext('Search MDN')
};

const styles = {
    container: css({
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        borderBottom: 'solid black 1px',
        maxWidth: 350,
        minWidth: 120,
        flex: '2 1 120px'
    }),
    icon: css({
        verticalAlign: -2,
        flex: '0 0 20px'
    }),
    input: css({
        // TODO: the !important declarations are used to override
        // stuff in the stylesheets. If we can simplify the
        // stylesheets, then maybe we can remove the importants
        borderWidth: '0 !important',
        fontSize: 18,
        fontWeight: 'bold !important',
        paddingBottom: '0 !important',
        flex: '0 1 300px'
    })
};

const LOCALE =
    window && window.location && window.location.pathname.split('/')[1];
const URL = LOCALE ? `/${LOCALE}/search` : '/en-US/search';

export default function Search() {
    return (
        <form
            css={styles.container}
            id="nav-main-search"
            action={URL}
            method="get"
            role="search"
        >
            <SearchIcon css={styles.icon} />

            <input
                css={styles.input}
                type="search"
                id="main-q"
                name="q"
                placeholder={strings.placeholder}
            />
        </form>
    );
}
