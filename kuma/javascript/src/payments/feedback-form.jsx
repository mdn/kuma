// @flow
import * as React from 'react';
import { gettext } from '../l10n.js';
import GAProvider from '../ga-provider.jsx';

const FeedbackForm = () => {
    const [feedback, setFeedback] = React.useState('');
    const [showMessage, setShowMessage] = React.useState(false);
    const ga = React.useContext(GAProvider.context);

    const handleChange = event => {
        const { value } = event.target;
        setFeedback(value);

        // cases where user submitted feedback already
        // and start typing in text input again
        if (showMessage) {
            setShowMessage(false);
        }
    };

    const handleSubmit = event => {
        event.preventDefault();

        ga('send', {
            hitType: 'event',
            eventCategory: 'monthly payments',
            eventAction: 'feedback',
            eventLabel: feedback.trim()
        });

        // Clear form and show thank you message
        setFeedback('');
        setShowMessage(true);
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
            />
            <div className="form-footer">
                <strong>
                    {showMessage && gettext('Thank you for your feedback!')}
                </strong>
                <button type="submit">{gettext('Send')}</button>
            </div>
        </form>
    );
};

export default FeedbackForm;
