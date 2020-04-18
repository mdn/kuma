// @flow
import * as React from 'react';
import { gettext, interpolate, Interpolated } from '../../l10n.js';
import { getCookie } from '../../utils.js';

export const FEEDBACK_URL = '/api/v1/subscriptions/feedback/';
export const MIN_STRING_LENGTH = 5;

type Props = {
    setShowForm: (((boolean) => boolean) | boolean) => void,
};

const CancelSubscriptionForm = ({ setShowForm }: Props): React.Node => {
    const [feedback, setFeedback] = React.useState<string>('');
    const [status, setStatus] = React.useState<'success' | 'idle'>('idle');
    const [error, setError] = React.useState<React.Node | null>(null);

    const handleCancel = () => {
        setShowForm(false);
    };
    // const renderSuccess = () => {
    //     return (
    //         <div className="alert success">
    //             {gettext(
    //                 'Your monthly subscription has been successfully canceled.'
    //             )}
    //         </div>
    //     );
    // };

    // const renderError = () => {
    //     return (
    //         <div className="alert danger">
    //             {gettext(
    //                 'There was a problem canceling your subscription. Please contact <email>'
    //             )}
    //         </div>
    //     );
    // };

    const handleSubmit = (event: SyntheticEvent<HTMLFormElement>) => {
        event.preventDefault();
        const trimmedFeedback = feedback.trim();

        // Feedback should be greater than 5 characters
        if (trimmedFeedback.length < MIN_STRING_LENGTH) {
            setError(
                interpolate(
                    'To ensure more constructive feedback, a minimum of %(MIN_STRING_LENGTH)s characters is required.',
                    { MIN_STRING_LENGTH }
                )
            );
            return false;
        }

        fetch(FEEDBACK_URL, {
            method: 'POST',
            body: JSON.stringify({ feedback: trimmedFeedback }),
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
        })
            .then((res) => {
                // Remove focus from button or input
                if (document.activeElement) {
                    document.activeElement.blur();
                }

                if (!res.ok) {
                    throw new Error(`Request (POST) to ${FEEDBACK_URL} failed`);
                }
                return res;
            })
            .then(() => {
                // Clear form, show thank you message
                setFeedback('');
                setError('');
                setStatus('success');
            })
            .catch(() => {
                setError(
                    <Interpolated
                        id={gettext(
                            "We're sorry, something went wrong. Please try again or send your feedback to <emailLink />."
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
                );
            });
    };

    if (status === 'success') {
        return (
            <strong className="success-msg" data-testid="success-msg">
                {gettext('Thank you for submitting your feedback!')}
            </strong>
        );
    }

    return (
        <>
            <form data-testid="feedback-form" onSubmit={handleSubmit}>
                <div className="alert danger">
                    <strong>
                        {gettext('Are you sure you want to cancel?')}
                    </strong>
                    <p>
                        {gettext(
                            'You will have to set up a new subscription if you wish to resume making payments to MDN Web Docs.'
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
            {error && <>There was an error</>}
        </>
    );
};

export default CancelSubscriptionForm;
