// @flow
import * as React from 'react';
import { gettext, interpolate, Interpolated } from '../../l10n.js';
import { getCookie } from '../../utils.js';

export const FEEDBACK_URL = '/api/v1/subscriptions/feedback/';

type Props = {
    setShowForm: (((boolean) => boolean) | boolean) => void,
    date: string,
};

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

        fetch(FEEDBACK_URL, {
            method: 'POST',
            body: JSON.stringify({ feedback: '' }),
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
        })
            .then((res) => {
                // Remove focus from button
                if (document.activeElement) {
                    document.activeElement.blur();
                }

                if (!res.ok) {
                    throw new Error(`Request (POST) to ${FEEDBACK_URL} failed`);
                }
                return res;
            })
            .then(() => {
                setStatus('success');

                // refresh list of active subscriptions in parent
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
                <Interpolated
                    id={gettext(
                        "We're sorry, there was a problem canceling your subscription. Please contact <emailLink />."
                    )}
                    emailLink={
                        <a
                            target="_blank"
                            rel="noopener noreferrer"
                            href={`mailto:${window.mdn.contributionSupportEmail}`}
                        >
                            {gettext(window.mdn.contributionSupportEmail)}
                        </a>
                    }
                />
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
