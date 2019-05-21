//@flow
import * as React from 'react';
import { useContext } from 'react';
import { css } from '@emotion/core';

import DocumentProvider from '../document-provider.jsx';
import { getLocale, gettext } from '../l10n.js';
import SearchIcon from '../icons/search.svg';

const styles = {
    container: css({
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        padding: '2px 8px',
        border: 'solid #888 1px',
        borderRadius: 8,
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
        fontSize: 16,
        fontWeight: 'bold !important',
        flex: '1 1 100px',
        minWidth: 60
    })
};

export default function Search() {
    const locale = getLocale();
    const documentData = useContext(DocumentProvider.context);
    if (!documentData) {
        return null;
    }
    const { absoluteURL, editURL } = documentData;

    // This is available as window.mdn.wikiSiteUrl. But we can't access
    // that during server-side rendering, so we either need to add that mdn
    // data to the document data, or we need to derive it from existing
    // document data somehow
    // TODO: pass this URL in some more reasonable way
    const WIKI_SITE_URL = editURL.substring(0, editURL.indexOf(absoluteURL));

    return (
        <form
            css={styles.container}
            id="nav-main-search"
            action={`${WIKI_SITE_URL}/${locale}/search`}
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
