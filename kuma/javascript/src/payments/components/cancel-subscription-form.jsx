// @flow
import * as React from 'react';
import { gettext, interpolate } from '../../l10n.js';
import { getCookie } from '../../utils.js';
import ErrorMessage from '../components/error-message.jsx';

export const FEEDBACK_URL = '/api/v1/subscriptions/feedback/';

type Props = {
    setShowForm: (((boolean) => boolean) | boolean) => void,
    date: string,
};

const SUBSCRIPTIONS_URL = '/api/v1/subscriptions/';

const CancelSubscriptionForm = ({ setShowForm, date }: Props): React.Node => {
    const [status, setStatus] = React.useState<
        'success' | 'error' | 'loading' | 'idle'
    >('idle');

    const handleCancel = () => {
        setShowForm(false);
    };

    const handleSubmit = (event: SyntheticEvent<HTMLFormElement>) => {
        event.preventDefault();
        setStatus('loading');

        fetch(SUBSCRIPTIONS_URL, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
        })
            .then((res) => {
                if (res.ok) {
                    setStatus('success');
                } else {
                    throw new Error(
                        `${res.status} ${res.statusText} fetching ${SUBSCRIPTIONS_URL}`
                    );
                }
            })
            .catch(() => {
                setStatus('error');
            });
    };

    if (status === 'success') {
        return (
            <p className="alert success" data-testid="success-msg">
                {gettext(
                    'Your monthly subscription has been successfully canceled.'
                )}
            </p>
        );
    }

    if (status === 'error') {
        return (
            <p className="alert error" data-testid="error-msg">
                <ErrorMessage />
            </p>
        );
    }

    return (
        <>
            <form
                disabled={status === 'loading'}
                data-testid="feedback-form"
                onSubmit={handleSubmit}
            >
                <div>
                    <strong>
                        {gettext('Are you sure you want to cancel?')}
                    </strong>
                    <p>
                        {interpolate(
                            'Your monthly subscription will end on %(date)s. You will have to set up a new subscription if you wish to resume making payments to MDN Web Docs.',
                            { date }
                        )}
                    </p>
                    <div className="form-footer">
                        <button
                            type="button"
                            className="cancel"
                            onClick={handleCancel}
                        >
                            {gettext('Keep my membership')}
                        </button>
                        <button type="submit" className="confirm inverse">
                            {gettext('Yes, cancel subscription')}
                        </button>
                    </div>
                </div>
            </form>
        </>
    );
};

export default CancelSubscriptionForm;
