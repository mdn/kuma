// @flow
import * as React from 'react';
import { useContext, useEffect, useState } from 'react';

import { gettext, Interpolated } from '../../l10n.js';
import Subheader from '../components/subheaders/index.jsx';
import CancelSubscriptionForm from '../components/cancel-subscription-form.jsx';
import ErrorMessage from '../components/error-message.jsx';

import UserProvider, { type UserData } from '../../user-provider.jsx';

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
const SUBSCRIPTIONS_URL = '/api/v1/subscriptions/';

const formatDate = (
    locale,
    date,
    options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
    }
) => {
    const dateObj = new Date(date);
    return new Intl.DateTimeFormat(locale, options).format(dateObj);
};

const ManagementPage = ({ locale }: Props) => {
    const [showForm, setShowForm] = React.useState<boolean>(false);
    const [status, setStatus] = React.useState<'success' | 'error' | 'idle'>(
        'idle'
    );
    const [subscription, setSubscription] = useState<?SubscriptionData>(null);

    const userData: ?UserData = useContext(UserProvider.context);
    const isSubscriber: ?boolean = userData && userData.isSubscriber;

    useEffect(() => {
        if (isSubscriber) {
            fetch(SUBSCRIPTIONS_URL)
                .then((res) => {
                    if (res.ok) {
                        return res.json();
                    } else {
                        throw new Error(
                            `${res.status} ${res.statusText} fetching ${SUBSCRIPTIONS_URL}`
                        );
                    }
                })
                .then((data) => {
                    const [subscription] = data.subscriptions;
                    setSubscription(subscription);
                })
                .catch(() => {
                    setStatus('error');
                });
        }
    }, [isSubscriber]);

    const handleClick = (event) => {
        event.preventDefault();
        setShowForm(true);
    };

    const renderInvitation = () => {
        return (
            <div className="active-subscriptions">
                <p>
                    <Interpolated
                        id={gettext(
                            'You have no active subscriptions. Why not <signupLink />?'
                        )}
                        signupLink={
                            <a href={`/${locale}/payments`}>
                                {gettext('set one up')}
                            </a>
                        }
                    />
                </p>
            </div>
        );
    };

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
                <p>Next payment occurs on {nextPaymentDate}.</p>
                <div className="active-subscriptions">
                    <table>
                        <thead>
                            <tr>
                                <th className="amount">{gettext('Amount')}</th>
                                <th className="credit-card">
                                    {gettext('Card Number')}
                                </th>
                                <th className="credit-card">
                                    {gettext('Expiry')}
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr
                                key={`${subscription.brand}-${subscription.last4}`}
                            >
                                <td>{`$${subscription.amount}`}</td>
                                <td>{`**** **** **** ${subscription.last4}`}</td>
                                <td>{subscription.expires_at}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <button
                    className="confirm toggle"
                    onClick={handleClick}
                    type="button"
                >
                    {gettext('Cancel subscription')}
                </button>
                {showForm && (
                    <CancelSubscriptionForm
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
        return 'Loading...';
    };

    return (
        <>
            <Subheader title="Manage monthly subscription" />
            <main
                className="contributions-page manage-subscriptions"
                role="main"
                data-testid="management-page"
            >
                <section>
                    <div className="column-8">
                        <h2>Subscriptions</h2>
                        {renderContent()}
                    </div>
                </section>
            </main>
        </>
    );
};

export default ManagementPage;
