//@flow
import * as React from 'react';
import { css } from '@emotion/core';

import gettext from '../gettext.js';

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
            <svg
                css={styles.icon}
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 26 28"
                aria-hidden="true"
            >
                <path d="M18 13c0-3.859-3.141-7-7-7s-7 3.141-7 7 3.141 7 7 7 7-3.141 7-7zm8 13c0 1.094-.906 2-2 2a1.96 1.96 0 0 1-1.406-.594l-5.359-5.344a10.971 10.971 0 0 1-6.234 1.937c-6.078 0-11-4.922-11-11s4.922-11 11-11 11 4.922 11 11c0 2.219-.672 4.406-1.937 6.234l5.359 5.359c.359.359.578.875.578 1.406z" />
            </svg>

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
