// @flow
import * as React from 'react';
import { useContext } from 'react';
import { css } from '@emotion/core';

import { gettext } from './l10n.js';
import EditIcon from './icons/pencil.svg';
import HistoryIcon from './icons/clock.svg';
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
        overflowX: 'scroll',
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
    }),

    editAndHistoryButtons: css({
        display: 'flex',
        flexDirection: 'row',
        flex: '0 0'
    }),
    editButton: css({
        flex: '1 0 auto',
        height: 32,
        border: 'solid 2px #3d7e9a',
        color: '#3d7e9a', // for the text
        fill: '#3d7e9a', // for the icon
        backgroundColor: '#fff',
        whiteSpace: 'nowrap',
        fontSize: 15,
        fontWeight: 'bold',
        padding: '0 18px'
    }),
    historyButton: css({
        width: 32,
        height: 32,
        border: 'solid 2px #333',
        backgroundColor: '#fff',
        padding: 5,
        marginLeft: 8
    })
};

function EditAndHistoryButtons({ document }: DocumentProps) {
    let editURL = document.editURL;
    return (
        <div css={styles.editAndHistoryButtons}>
            <button
                css={styles.editButton}
                onClick={() => {
                    window.location = editURL;
                }}
            >
                <EditIcon width={13} height={13} /> {gettext('Edit')}
            </button>
            <button
                css={styles.historyButton}
                aria-label={gettext('History')}
                onClick={() => {
                    window.location = editURL.replace('$edit', '$history');
                }}
            >
                <HistoryIcon width={18} height={18} />
            </button>
        </div>
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
    // are a contributor (or, if we don't know whether they are
    // a contributor because the backend does not support that yet)
    // then we want to show Edit and History buttons on the
    // right side of the titlebar.
    let showEditAndHistory =
        userData &&
        userData.isAuthenticated &&
        (userData.isContributor === undefined || userData.isContributor);

    return (
        <div css={styles.titlebarContainer}>
            <div css={styles.titlebar}>
                <h1 css={styles.title}>{title}</h1>
                {document && showEditAndHistory && (
                    <EditAndHistoryButtons document={document} />
                )}
            </div>
        </div>
    );
}
