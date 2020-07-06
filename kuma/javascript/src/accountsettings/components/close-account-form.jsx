// @flow
import * as React from 'react';
import { useState } from 'react';

import { gettext } from '../../l10n.js';

type Props = {
    onCancel: () => void,
};

export const title = gettext('Are you sure you want to close your account?');

const CloseAccountForm = ({ onCancel }: Props) => {
    const [status, setStatus] = useState<'error' | 'submitting' | 'idle'>(
        'idle'
    );

    const handleSubmit = (event: SyntheticEvent<HTMLFormElement>) => {
        event.preventDefault();
        setStatus('submitting');
    };

    return (
        <form
            name="close-account"
            className="confirmation-form"
            onSubmit={handleSubmit}
            aria-labelledby="close-account-heading"
        >
            <h4 id="close-account-heading">{title}</h4>

            <p>
                {gettext(
                    'Deleting your account loses any preferences you have set, as well as makes your username available for others to use. It will also cancel any MDN subscription you might have.'
                )}
            </p>

            <footer className="form-footer">
                <button
                    type="button"
                    className="cta neutral"
                    onClick={onCancel}
                >
                    {gettext('Keep account')}
                </button>
                <button
                    type="submit"
                    className="cta negative solid"
                    disabled={status === 'submitting'}
                >
                    {gettext('Yes, close account')}
                </button>
            </footer>
        </form>
    );
};

export default CloseAccountForm;
