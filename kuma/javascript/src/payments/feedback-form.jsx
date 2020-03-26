// @flow
import * as React from 'react';
import { gettext, Interpolated } from '../l10n.js';
import { getCookie } from '../utils.js';

const FeedbackForm = (): React.Node => {
    const [feedback, setFeedback] = React.useState<string>('');
    const [status, setStatus] = React.useState<'success' | 'error' | ''>('');

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
                // Show error message
                setStatus('error');
            });
    };

    // ga('send', {
    //     hitType: 'event',
    //     eventCategory: 'monthly payments',
    //     eventAction: 'feedback',
    //     eventLabel: feedback.trim()
    // });

    return (
        <form onSubmit={handleSubmit}>
            <input
                type="text"
                placeholder={gettext('Enter optional feedback…')}
                name="feedback"
                value={feedback}
                onChange={handleChange}
                required
                disabled={status === 'success'}
            />
            <div className="form-footer">
                <span>
                    {status === 'error' && (
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
                    )}
                    {status === 'success' &&
                        gettext('Thank you for submitting your feedback!')}
                </span>
                <button type="submit">{gettext('Send')}</button>
            </div>
        </form>
    );
};

export default FeedbackForm;
