// @flow
import { useEffect, useState } from 'react';
import { getSubscriptions } from '../payments/api.js';
import { type UserData } from '../user-provider.jsx';

export type SubscriptionData = {
    id: string,
    amount: number,
    brand: string,
    expires_at: string,
    last4: string,
    zip: string,
    next_payment_at: string,
};

function useSubscriptionData(userData: ?UserData) {
    const [subscription, setSubscription] = useState<?SubscriptionData>(null);
    const [error, setError] = useState<?string>(null);

    useEffect(() => {
        if (userData && userData.isSubscriber) {
            const handleSuccess = (data) => {
                const [subscription] = data.subscriptions;
                setSubscription(subscription);
            };
            const handleError = (error) => setError(error);
            getSubscriptions(handleSuccess, handleError);
        }
    }, [userData]);

    return { subscription, error };
}

export default useSubscriptionData;
