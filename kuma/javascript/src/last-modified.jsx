// @flow
import * as React from 'react';

import { gettext } from './l10n.js';

import ClockIcon from './icons/clock.svg';

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
        <section className="contributors-sub">
            <ClockIcon />
            <header>
                <h4>{gettext('Last updated by:')}</h4>
            </header>
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
        </section>
    );
}
