// @flow
import * as React from 'react';
import { useContext } from 'react';
import { css } from '@emotion/core';

import { gettext } from './l10n.js';
import EditIcon from './icons/pencil.svg';
import UserProvider from './user-provider.jsx';

import type { DocumentData, DocumentProps } from './document.jsx';

// TODO: define this in a global styles.js file
// A media query that identifies screens narrower than a tablet
const NARROW = '@media (max-width: 749px)';

const styles = {
    // Titlebar styles
    titlebarContainer: css({
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        boxSizing: 'border-box',
        width: '100%',
        minHeight: 106,
        padding: '12px 24px',
        backgroundColor: '#f5f9fa',
        borderBottom: 'solid 1px #dce3e5',
        borderTop: 'solid 1px #dce3e5',
        [NARROW]: {
            // Reduce titlebar size on narrow screens
            minHeight: 60,
            padding: '8px 16px'
        }
    }),
    titlebar: css({
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        width: '100%',
        maxWidth: 1352
    }),
    title: css({
        flex: '1 1',
        fontFamily:
            'x-locale-heading-primary, zillaslab, "Palatino", "Palatino Linotype", x-locale-heading-secondary, serif',
        fontSize: 45,
        fontWeight: 'bold',
        hyphens: 'auto',
        [NARROW]: {
            // Reduce the H1 size on narrow screens
            fontSize: 28
        }
    })
};

function EditButton({ document }: DocumentProps) {
    /* we want to omit the trailing `$edit` from the URL
       to ensure users are not sent into edit mode immediately 
       https://bugzilla.mozilla.org/show_bug.cgi?id=1567720#c1 */
    let editURL = document.editURL.split('$')[0];
    return (
        <a className="button neutral" href={editURL} rel="nofollow">
            <EditIcon /> {gettext('Edit in wiki')}
        </a>
    );
}

export default function Titlebar({
    title,
    document
}: {
    title: string,
    document?: DocumentData
}) {
    const userData = useContext(UserProvider.context);

    // If we have user data, and the user is logged in, and they
    // are a contributor (or, if we don't know whether they are a
    // contributor because the backend does not support that yet) then
    // we want to show the Edit button on the right side of the titlebar.
    let showEdit =
        userData &&
        userData.isAuthenticated &&
        (userData.isContributor === undefined || userData.isContributor);

    return (
        <div css={styles.titlebarContainer}>
            <div css={styles.titlebar}>
                <h1 css={styles.title}>{title}</h1>
                {document && showEdit && <EditButton document={document} />}
            </div>
        </div>
    );
}
