// @flow
import * as React from 'react';
import { useContext, useEffect, useState } from 'react';

import { gettext, interpolate, Interpolated } from '../../l10n.js';
import UserProvider, { type UserData } from '../../user-provider.jsx';
import Subheader from '../components/subheaders/index.jsx';
import CancelSubscriptionForm from '../components/cancel-subscription-form.jsx';
import ErrorMessage from '../components/error-message.jsx';
import { getSubscriptions } from '../api.js';
import { formatDate } from '../formatDate.js';

export type SubscriptionData = {
    id: string,
    amount: number,
    brand: string,
    expires_at: string,
    last4: string,
    zip: string,
    next_payment_at: string,
};

type Props = {
    locale: string,
};
export const title = gettext('Manage monthly subscriptions');
export const successMsg = gettext(
    'Your monthly subscription has been successfully canceled.'
);

const ManagementPage = ({ locale }: Props) => {
    const [showForm, setShowForm] = React.useState<boolean>(false);
    const [status, setStatus] = React.useState<'success' | 'error' | 'idle'>(
        'idle'
    );
    const [subscription, setSubscription] = useState<?SubscriptionData>(null);
    const [isSubscriber, setIsSubscriber] = useState<?boolean>(null);
    const userData: ?UserData = useContext(UserProvider.context);

    // Currently we don't have a way to update the UserProvider context, so
    // we are saving the context value `isSubscriber` to local state. It will be
    // out-of-sync with context upon a successful delete, but I think it's ok
    // for now, since actions after deleting are limited-- nothing builds upon
    // `isSubscriber`. The only thing you can do from this point is go to
    // /payments which will refresh the UserProvider context.
    useEffect(() => {
        setIsSubscriber(userData && userData.isSubscriber);
    }, [userData]);

    useEffect(() => {
        if (isSubscriber) {
            const handleSuccess = (data) => {
                const [subscription] = data.subscriptions;
                setSubscription(subscription);
            };
            const handleError = () => setStatus('error');
            getSubscriptions(handleSuccess, handleError);
        }
    }, [isSubscriber]);

    const handleClick = (event) => {
        event.preventDefault();
        setShowForm(true);
    };

    const handleDeleteSuccess = () => {
        setSubscription(null);
        setIsSubscriber(false);
        setStatus('success');
    };

    const renderSuccess = () => (
        <p className="alert success" data-testid="success-msg">
            {successMsg}
        </p>
    );

    const renderInvitation = () => (
        <div className="active-subscriptions">
            <Interpolated
                id={gettext(
                    'You have no active subscriptions. Why not <signupLink />?'
                )}
                signupLink={
                    <a href={`/${locale}/payments/`}>{gettext('set one up')}</a>
                }
            />
        </div>
    );

    const renderSubscriptions = () => {
        if (!subscription) {
            return;
        }
        const date = new Date(subscription.next_payment_at);
        const nextPaymentDate = formatDate(
            locale,
            subscription.next_payment_at
        );
        const lastActiveDate = formatDate(
            locale,
            date.setDate(date.getDate() - 1)
        );

        return (
            <>
                <p>
                    {interpolate(
                        'Next payment occurs on %(nextPaymentDate)s.',
                        {
                            nextPaymentDate,
                        }
                    )}
                </p>
                <div className="active-subscriptions">
                    <ul>
                        <li>
                            <span className="label amount">
                                {gettext('Amount')}
                            </span>
                            <span className="value">{`$${subscription.amount}`}</span>
                        </li>
                        <li>
                            <span className="label credit-card">
                                {gettext('Card number')}
                            </span>
                            <span className="value">{`**** **** **** ${subscription.last4}`}</span>
                        </li>
                        <li>
                            <span className="label credit-card">
                                {gettext('Expiry')}
                            </span>
                            <span className="value">
                                {subscription.expires_at}
                            </span>
                        </li>
                    </ul>
                </div>
                <button
                    className="cta cancel"
                    onClick={handleClick}
                    type="button"
                >
                    {gettext('Cancel subscription')}
                </button>
                {showForm && (
                    <CancelSubscriptionForm
                        onSuccess={handleDeleteSuccess}
                        setShowForm={setShowForm}
                        date={lastActiveDate}
                    />
                )}
            </>
        );
    };

    const renderContent = () => {
        if (userData && !isSubscriber) {
            return renderInvitation();
        } else if (isSubscriber && subscription) {
            return renderSubscriptions();
        } else if (status === 'error') {
            return <ErrorMessage />;
        }
        return <strong>{gettext('Loading…')}</strong>;
    };

    return (
        <>
            <Subheader title={title} />
            <main
                className="contributions-page manage-subscriptions"
                role="main"
                data-testid="management-page"
            >
                <section>
                    <div className="column-8">
                        <h2>{gettext('Subscriptions')}</h2>
                        {renderContent()}
                        {status === 'success' && renderSuccess()}
                    </div>
                </section>
            </main>
        </>
    );
};

export default ManagementPage;
