// @flow
import * as React from 'react';
import { gettext, interpolate } from '../../l10n.js';
import ErrorMessage from '../components/error-message.jsx';
import { sendFeedback } from '../api.js';

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

        const reqBody = JSON.stringify({ feedback: trimmedFeedback });
        const handleSuccess = () => {
            // Remove focus from button or input
            if (document.activeElement) {
                document.activeElement.blur();
            }
            // Clear form, show thank you message
            setFeedback('');
            setError('');
            setStatus('success');
        };
        const handleError = () => {
            setError(<ErrorMessage />);
        };
        sendFeedback(reqBody, handleSuccess, handleError);
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
                <button
                    data-testid="feedback-button"
                    type="submit"
                    className="cta primary"
                >
                    {gettext('Send')}
                </button>
            </div>
        </form>
    );
};

export default FeedbackForm;
