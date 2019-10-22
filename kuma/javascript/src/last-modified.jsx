// @flow
import * as React from 'react';

import { gettext } from './l10n.js';

type Props = {
    documentLocale: string,
    lastModified: string,
    wikiRevisionHistoryURL: string
};

export default function LastModified({
    documentLocale,
    lastModified,
    wikiRevisionHistoryURL
}: Props) {
    // This fortunately works because the 'lastModified' date string is
    // predictable and always of the same format. It's not a proper ISO
    // string but it's close.
    const lastModifiedDate = new Date(lastModified);
    // Justification for these is to match the Wiki.
    const dateStringOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    };

    return (
        <section className="document-meta">
            <header className="visually-hidden">
                <h4>Metadata</h4>
            </header>{' '}
            <ul>
                <li className="last-modified">
                    <b>{gettext('Last modified:')}</b>{' '}
                    <time dateTime={lastModified}>
                        {lastModifiedDate.toLocaleString(
                            documentLocale,
                            dateStringOptions
                        )}
                    </time>
                    ,{' '}
                    <a href={`${wikiRevisionHistoryURL}`} rel="nofollow">
                        {gettext('by MDN contributors')}
                    </a>
                </li>
            </ul>
        </section>
    );
}
