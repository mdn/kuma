// @flow
import * as React from 'react';
import { useContext, useState } from 'react';

import { gettext, interpolate, Interpolated } from '../../l10n.js';
import UserProvider, { type UserData } from '../../user-provider.jsx';
import { formatDate, formatMoney } from '../../formatters.js';
import SignInLink from '../../signin-link.jsx';
import Subheader from '../components/subheaders/index.jsx';
import CancelSubscriptionForm from '../components/cancel-subscription-form.jsx';
import { GenericError } from '../components/errors.jsx';
import useSubscriptionData from '../../hooks/useSubscriptionData.js';

type Props = {
    locale: string,
};
export const title = gettext('Manage monthly subscription');
export const successMsg = gettext(
    'Your monthly subscription has been successfully canceled.'
);

const ManagementPage = ({ locale }: Props): React.Node => {
    const [showForm, setShowForm] = React.useState<boolean>(false);
    const [status, setStatus] = React.useState<'success' | 'error' | 'idle'>(
        'idle'
    );
    const [canceled, setCanceled] = useState<?boolean>(false);
    const userData: ?UserData = useContext(UserProvider.context);
    let { subscription, error } = useSubscriptionData(userData);

    // if there's no user data yet, don't render anything
    if (!userData) {
        return null;
    }

    if (error && status !== 'error') {
        setStatus('error');
    }

    const handleClick = (event) => {
        event.preventDefault();
        setShowForm(true);
    };

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

    const renderInvitation = () => (
        <div className="active-subscriptions">
            <Interpolated
                id={gettext(
                    'You have no active subscription. Why not <signupLink />?'
                )}
                signupLink={
                    <a href={`/${locale}/payments/`}>{gettext('set one up')}</a>
                }
            />
        </div>
    );

    const renderSubscriptions = () => {
        if (!subscription) {
            return false;
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

                <dl className="active-subscriptions">
                    <div>
                        <dt className="amount">{gettext('Amount')}</dt>
                        <dd>
                            {/* amount is in cents, so divide by 100 to get dollars */}
                            {formatMoney(locale, subscription.amount / 100)}
                        </dd>
                    </div>
                    <div>
                        <dt className="credit-card">
                            {gettext('Card number')}
                        </dt>
                        <dd>{`**** **** **** ${subscription.last4}`}</dd>
                    </div>
                    <div>
                        <dt className="credit-card">{gettext('Expiry')}</dt>
                        <dd>{subscription.expires_at}</dd>
                    </div>
                </dl>

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
                return <GenericError />;
            default:
                // Fetching data
                return <strong>{gettext('Loading…')}</strong>;
        }
    };

    return (
        <>
            <Subheader title={title} />
            <main
                id="content"
                className="contributions-page manage-subscriptions"
                role="main"
                data-testid="management-page"
            >
                <section>
                    <div className="column-8">
                        <h2>{gettext('Subscription')}</h2>
                        {renderContent()}
                        {status === 'success' && renderSuccess()}
                    </div>
                </section>
            </main>
        </>
    );
};

export default ManagementPage;
