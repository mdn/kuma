// @flow
import * as React from 'react';
import { gettext, Interpolated } from '../l10n.js';
import { getCookie } from '../utils.js';

const FeedbackForm = (): React.Node => {
    const [feedback, setFeedback] = React.useState<string>('');
    const [status, setStatus] = React.useState<'success' | 'error' | null>(
        null
    );

    const handleChange = (event: SyntheticInputEvent<HTMLInputElement>) => {
        const { value } = event.target;
        setFeedback(value);
    };

    const handleSubmit = (event: SyntheticEvent<HTMLFormElement>) => {
        event.preventDefault();

        fetch('/payments/feedback', {
            method: 'POST',
            body: JSON.stringify({ feedback: feedback.trim() }),
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
            .then(res => {
                // Remove focus from button or input
                if (document.activeElement) {
                    document.activeElement.blur();
                }

                if (!res.ok) {
                    throw new Error(
                        'Request (POST) to /payments/feedback failed'
                    );
                }
                return res;
            })
            .then(() => {
                // Clear form, show thank you message
                setFeedback('');
                setStatus('success');
            })
            .catch(() => {
                setStatus('error');
            });
    };

    return (
        <form onSubmit={handleSubmit}>
            <input
                data-testid="feedback-input"
                type="text"
                placeholder={gettext('Enter optional feedback…')}
                name="feedback"
                value={feedback}
                onChange={handleChange}
                required
                disabled={status === 'success'}
            />
            <div className="form-footer">
                {status === 'error' && (
                    <span data-testid="error-msg">
                        <Interpolated
                            id={gettext(
                                "We're sorry, something went wrong. Please try again or send your feedback to <emailLink />."
                            )}
                            emailLink={
                                <a
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    href="mailto:mdn-support@mozilla.com"
                                >
                                    {gettext('mdn-support@mozilla.com')}
                                </a>
                            }
                        />
                    </span>
                )}
                {status === 'success' && (
                    <strong data-testid="success-msg">
                        {gettext('Thank you for submitting your feedback!')}
                    </strong>
                )}

                <button data-testid="feedback-button" type="submit">
                    {gettext('Send')}
                </button>
            </div>
        </form>
    );
};

export default FeedbackForm;
