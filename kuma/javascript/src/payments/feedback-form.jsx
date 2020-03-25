// @flow
import * as React from 'react';
import { gettext } from '../l10n.js';
import GAProvider from '../ga-provider.jsx';

const FeedbackForm = () => {
    const [feedback, setFeedback] = React.useState('');
    const [submitted, setSubmitted] = React.useState(false);
    const ga = React.useContext(GAProvider.context);

    const handleChange = event => {
        const { value } = event.target;
        setFeedback(value);
    };

    const handleSubmit = event => {
        event.preventDefault();

        ga('send', {
            hitType: 'event',
            eventCategory: 'monthly payments',
            eventAction: 'feedback',
            eventLabel: feedback.trim()
        });

        // Clear form, show thank you message, disable input
        setFeedback('');
        setSubmitted(true);
    };

    return (
        <form onSubmit={handleSubmit}>
            <input
                type="text"
                placeholder={gettext('Enter optional feedback…')}
                name="feedback"
                value={feedback}
                onChange={handleChange}
                required
                disabled={!!submitted}
            />
            <div className="form-footer">
                <strong>
                    {submitted &&
                        gettext('Thank you for submitting your feedback!')}
                </strong>
                <button type="submit">{gettext('Send')}</button>
            </div>
        </form>
    );
};

export default FeedbackForm;
