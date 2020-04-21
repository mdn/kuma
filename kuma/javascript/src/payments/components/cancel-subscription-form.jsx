// @flow
import * as React from 'react';
import { gettext, interpolate } from '../../l10n.js';
import ErrorMessage from '../components/error-message.jsx';
import { deleteSubscriptions } from '../api.js';

export const FEEDBACK_URL = '/api/v1/subscriptions/feedback/';

type Props = {
    setShowForm: (((boolean) => boolean) | boolean) => void,
    onSuccess: () => void,
    date: string,
};

const CancelSubscriptionForm = ({
    setShowForm,
    onSuccess,
    date,
}: Props): React.Node => {
    const [status, setStatus] = React.useState<'error' | 'submitting' | 'idle'>(
        'idle'
    );

    const handleCancel = () => setShowForm(false);

    const handleSubmit = (event: SyntheticEvent<HTMLFormElement>) => {
        event.preventDefault();
        setStatus('submitting');

        // success is handled by parent component
        const handleSuccess = () => onSuccess();
        const handleError = () => setStatus('error');
        deleteSubscriptions(handleSuccess, handleError);
    };

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
                disabled={status === 'submitting'}
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
