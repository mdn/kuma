// @flow
import * as React from 'react';

import { gettext } from './l10n.js';

import ClockIcon from './icons/clock.svg';

type LastModifiedByProps = {
    lastModifiedBy: String,
    lastModified: String,
    profileBaseURL: String
};

export default function LastModifiedBy({
    lastModifiedBy,
    lastModified,
    profileBaseURL
}: LastModifiedByProps) {
    return (
        <section className="contributors-sub">
            <ClockIcon />
            <header>
                <h4>{gettext('Last updated by:')}</h4>
            </header>
            <a href={`${profileBaseURL}${lastModifiedBy}`} rel="nofollow">
                {`${lastModifiedBy}, `}
            </a>
            <time dateTime={lastModified}>{lastModified}</time>
        </section>
    );
}
