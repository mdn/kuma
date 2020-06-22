// @flow
import * as React from 'react';
import { gettext, interpolate } from '../../l10n.js';
import { GenericError } from '../../common/errors.jsx';
import { deleteSubscriptions } from '../../payments/api.js';

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
                <GenericError />
            </p>
        );
    }

    return (
        <form
            name="cancel-subscription"
            className="cancel-subscription"
            onSubmit={handleSubmit}
            aria-labelledby="subscription-form-heading"
        >
            <h4 id="subscription-form-heading">{title}</h4>
            <p>
                {interpolate(
                    'Your monthly subscription will end on %(date)s, but if you cancel now it will end immediately. You will have to set up a new subscription if you wish to resume making payments to MDN Web Docs.',
                    { date }
                )}
            </p>
            <footer className="form-footer">
                <button
                    type="button"
                    className="cta neutral"
                    onClick={handleCancel}
                >
                    {gettext('Keep subscription')}
                </button>
                <button
                    type="submit"
                    className="cta negative solid"
                    disabled={status === 'submitting'}
                >
                    {gettext('Yes, cancel subscription')}
                </button>
            </footer>
        </form>
    );
};

export default CancelSubscriptionForm;
