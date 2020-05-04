// @flow
import * as React from 'react';
import { gettext, interpolate } from '../../l10n.js';
import ErrorMessage from '../components/error-message.jsx';
import { deleteSubscriptions } from '../api.js';

type Props = {
    setShowForm: (((boolean) => boolean) | boolean) => void,
    onSuccess: () => void,
    date: string,
};

export const title = gettext('Are you sure you want to cancel?');

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
        <form onSubmit={handleSubmit}>
            <div>
                <h4>{title}</h4>
                <p>
                    {interpolate(
                        'Your monthly subscription will end on %(date)s, but if you cancel now it will end immediately. You will have to set up a new subscription if you wish to resume making payments to MDN Web Docs.',
                        { date }
                    )}
                </p>
                <div className="form-footer">
                    <button
                        type="button"
                        className="cta keep-membership"
                        onClick={handleCancel}
                    >
                        {gettext('Keep my membership')}
                    </button>
                    <button
                        type="submit"
                        className="cta negative"
                        disabled={status === 'submitting'}
                    >
                        {gettext('Yes, cancel subscription')}
                    </button>
                </div>
            </div>
        </form>
    );
};

export default CancelSubscriptionForm;
