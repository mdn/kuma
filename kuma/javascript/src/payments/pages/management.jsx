// @flow
import * as React from 'react';
import { useContext, useEffect, useState } from 'react';

import { gettext, interpolate, Interpolated } from '../../l10n.js';
import UserProvider, { type UserData } from '../../user-provider.jsx';
import { formatDate, formatMoney } from '../../formatters.js';
import SignInLink from '../../signin-link.jsx';
import Subheader from '../components/subheaders/index.jsx';
import CancelSubscriptionForm from '../components/cancel-subscription-form.jsx';
import ErrorMessage from '../components/error-message.jsx';
import { getSubscriptions } from '../api.js';

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

const ManagementPage = ({ locale }: Props): React.Node => {
    const [showForm, setShowForm] = React.useState<boolean>(false);
    const [status, setStatus] = React.useState<'success' | 'error' | 'idle'>(
        'idle'
    );
    const [subscription, setSubscription] = useState<?SubscriptionData>(null);
    const [canceled, setCanceled] = useState<?boolean>(false);
    const userData: ?UserData = useContext(UserProvider.context);

    useEffect(() => {
        if (userData && userData.isSubscriber) {
            const handleSuccess = (data) => {
                const [subscription] = data.subscriptions;
                setSubscription(subscription);
            };
            const handleError = () => setStatus('error');
            getSubscriptions(handleSuccess, handleError);
        }
    }, [userData]);

    // if there's no user data yet, don't render anything
    if (!userData) {
        return null;
    }

    const handleClick = (event) => {
        event.preventDefault();
        setShowForm(true);
    };

    const handleDeleteSuccess = () => {
        setSubscription(null);
        setCanceled(true);
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
                            <span className="value">
                                {/* amount is in cents, so divide by 100 to get dollars */}
                                {formatMoney(locale, subscription.amount / 100)}
                            </span>
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
        switch (true) {
            case !userData.isAuthenticated:
                // User is not logged in
                return (
                    <Interpolated
                        id={gettext('Please <signInLink /> to continue.')}
                        signInLink={<SignInLink text={gettext('sign in')} />}
                    />
                );
            case !userData.isSubscriber || canceled:
                // Not a subscriber or just canceled their subscription
                return renderInvitation();
            case userData.isSubscriber && !!subscription:
                // Is a subscriber and has subscriptions
                return renderSubscriptions();
            case status === 'error':
                // Something went wrong with fetching data
                return <ErrorMessage />;
            default:
                // Fetching data
                return <strong>{gettext('Loading…')}</strong>;
        }
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
