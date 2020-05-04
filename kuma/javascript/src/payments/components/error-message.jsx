import * as React from 'react';
import { gettext, Interpolated } from '../../l10n.js';

const errorMessage = () => (
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

export default errorMessage;
