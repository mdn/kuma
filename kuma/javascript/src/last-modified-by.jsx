// @flow
import * as React from 'react';

import { gettext } from './l10n.js';

import ClockIcon from './icons/clock.svg';

type LastModifiedByProps = {
    documentLocale: String,
    lastModifiedBy: String,
    lastModified: String,
    profileBaseURL: String
};

export default function LastModifiedBy({
    documentLocale,
    lastModifiedBy,
    lastModified,
    profileBaseURL
}: LastModifiedByProps) {
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
            <a href={`${profileBaseURL}${lastModifiedBy}`} rel="nofollow">
                {`${lastModifiedBy}, `}
            </a>
            <time dateTime={lastModified}>
                {lastModifiedDate.toLocaleString(
                    documentLocale,
                    dateStringOptions
                )}
            </time>
        </section>
    );
}
