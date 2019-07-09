// @flow
import * as React from 'react';

import { gettext } from './l10n.js';

import ContributorsIcon from './icons/contributors.svg';

type ContributorProps = {
    contributors: Array,
    profileBaseURL: String
};

export default function Contributors({
    contributors,
    profileBaseURL
}: ContributorProps) {
    return (
        <section className="contributors-sub">
            <ContributorsIcon />
            <header>
                <h4>{gettext('Contributors to this page:')}</h4>
            </header>
            <ul>
                {contributors.map((contributor, index) => (
                    <li key={contributor}>
                        {index > 0 && ', '}
                        <a
                            href={`${profileBaseURL}${contributor}`}
                            rel="nofollow"
                        >
                            {contributor}
                        </a>
                    </li>
                ))}
            </ul>
        </section>
    );
}
