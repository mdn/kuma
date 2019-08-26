// @flow
import * as React from 'react';
import { useContext } from 'react';

import { gettext } from './l10n.js';
import EditIcon from './icons/pencil.svg';
import UserProvider from './user-provider.jsx';

import type { DocumentData, DocumentProps } from './document.jsx';

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
        <div className="titlebar-container">
            <div className="titlebar">
                <h1 className="title">{title}</h1>
                {document && showEdit && <EditButton document={document} />}
            </div>
        </div>
    );
}
