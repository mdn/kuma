// @flow
import * as React from 'react';
import { gettext, interpolate, Interpolated } from '../l10n.js';
import { getCookie } from '../utils.js';

export const FEEDBACK_URL = '/api/v1/subscriptions/feedback/';
export const MIN_STRING_LENGTH = 5;

const FeedbackForm = (): React.Node => {
    const [feedback, setFeedback] = React.useState<string>('');
    const [status, setStatus] = React.useState<'success' | 'idle'>('idle');
    const [error, setError] = React.useState<React.Node | null>(null);

    const handleChange = (event: SyntheticInputEvent<HTMLInputElement>) => {
        const { value } = event.target;
        setFeedback(value);
    };

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
        <form data-testid="feedback-form" onSubmit={handleSubmit}>
            <input
                data-testid="feedback-input"
                type="text"
                placeholder={gettext('Enter optional feedback…')}
                name="feedback"
                value={feedback}
                onChange={handleChange}
                required
            />
            <div className="form-footer">
                {error && <span data-testid="error-msg">{error}</span>}
                <button data-testid="feedback-button" type="submit">
                    {gettext('Send')}
                </button>
            </div>
        </form>
    );
};

export default FeedbackForm;
