// @flow
import * as React from 'react';
import { gettext, Interpolated } from '../l10n.js';

type Props = {
    text: string,
    onClick: (event: SyntheticEvent<HTMLAnchorElement>) => void,
};

/**
 * Structured error message with header, text, and button
 */
const ErrorWithRetry = ({ text, onClick }: Props): React.Node => (
    <section className="error">
        <h4>{gettext('Sorry!')}</h4>
        <p>{text}</p>
        <button type="button" className="button cta primary" onClick={onClick}>
            {gettext('Try again')}
        </button>
    </section>
);

/**
 * Simple sentence with support email
 **/
const GenericError = (): React.Node => (
    <Interpolated
        id={gettext(
            "We're sorry, something went wrong. Please contact <emailLink />."
        )}
        emailLink={
            <a
                target="_blank"
                rel="noopener noreferrer"
                href={`mailto:${window.mdn.contributionSupportEmail}`}
            >
                {window.mdn.contributionSupportEmail}
            </a>
        }
    />
);

export { GenericError, ErrorWithRetry };
