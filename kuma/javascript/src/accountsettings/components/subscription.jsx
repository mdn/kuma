// @flow
import * as React from 'react';
import { useState } from 'react';

import { gettext } from '../../l10n.js';
import { GenericError } from '../../common/errors.jsx';

import { type UserData } from '../../user-provider.jsx';
import useSubscriptionData from '../../hooks/useSubscriptionData.js';

import Invitation from './invitation.jsx';
import SubscriptionDetails from './subscription-detail.jsx';

type Props = {
    contributionSupportEmail: string,
    locale: string,
    userData: UserData,
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

    let content = null;
    let { subscription, error } = useSubscriptionData(userData);

    if (error && status !== 'error') {
        setStatus('error');
    }

    const onDeleteSuccess = () => {
        subscription = null;
        setCanceled(true);
        setStatus('success');
    };

    if (!userData.isSubscriber || canceled) {
        // Not a subscriber or just canceled their subscription
        content = <Invitation locale={locale} />;
    } else if (userData.isSubscriber && !!subscription) {
        // Is a subscriber and has subscriptions
        content = (
            <SubscriptionDetails
                locale={locale}
                onDeleteSuccess={onDeleteSuccess}
                subscription={subscription}
                contributionSupportEmail={contributionSupportEmail}
            />
        );
    } else if (status === 'error') {
        // Something went wrong with fetching data
        content = <GenericError />;
    } else {
        content = <strong>{gettext('Loading…')}</strong>;
    }

    return (
        <section
            className="subscription account-girdle"
            aria-labelledby="subscription-heading"
        >
            <h2 id="subscription-heading">{gettext('Subscription')}</h2>
            {status === 'success' && (
                <p className="alert success" data-testid="success-msg">
                    {successMsg}
                </p>
            )}
            {content}
        </section>
    );
};

export default Subscription;
