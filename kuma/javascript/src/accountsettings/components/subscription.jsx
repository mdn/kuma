// @flow
import * as React from 'react';
import { useState } from 'react';

import { gettext } from '../../l10n.js';
import { GenericError } from '../../common/errors.jsx';

import useSubscriptionData from '../../hooks/useSubscriptionData.js';

import Invitation from './invitation.jsx';
import SubscriptionDetails from './subscription-detail.jsx';

type Props = {
    contributionSupportEmail: string,
    locale: string,
    userData: Object,
};

export const successMsg = gettext(
    'Your monthly subscription has been successfully canceled.'
);

const Subscription = ({
    contributionSupportEmail,
    locale,
    userData,
}: Props) => {
    const [canceled, setCanceled] = useState<?boolean>(false);
    const [status, setStatus] = useState<'success' | 'error' | 'idle'>('idle');

    let { subscription, error } = useSubscriptionData(userData);

    if (error && status !== 'error') {
        setStatus('error');
    }

    const handleDeleteSuccess = () => {
        subscription = null;
        setCanceled(true);
        setStatus('success');
    };

    const renderSuccess = () => (
        <p className="alert success" data-testid="success-msg">
            {successMsg}
        </p>
    );

    const renderSubscriptionDetail = () => {
        if (!subscription) {
            return false;
        }

        return (
            <SubscriptionDetails
                locale={locale}
                handleDeleteSuccess={handleDeleteSuccess}
                subscription={subscription}
                contributionSupportEmail={contributionSupportEmail}
            />
        );
    };

    const renderContent = () => {
        switch (true) {
            case !userData.isSubscriber || canceled:
                // Not a subscriber or just canceled their subscription
                return <Invitation locale={locale} />;
            case userData.isSubscriber && !!subscription:
                // Is a subscriber and has subscriptions
                return renderSubscriptionDetail();
            case status === 'error':
                // Something went wrong with fetching data
                return <GenericError />;
            default:
                // Fetching data
                return <strong>{gettext('Loading…')}</strong>;
        }
    };

    return (
        <section
            className="subscription account-girdle"
            aria-labelledby="subscription-heading"
        >
            <h2 id="subscription-heading">{gettext('Subscription')}</h2>
            {status === 'success' && renderSuccess()}
            {renderContent()}
        </section>
    );
};

export default Subscription;
