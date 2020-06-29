// @flow
import * as React from 'react';
import { useContext, useState } from 'react';

import { gettext, Interpolated } from '../../l10n.js';

import { type RouteComponentProps } from '../../route.js';
import UserProvider, { type UserData } from '../../user-provider.jsx';
import SignInLink from '../../signin-link.jsx';
import Subheader from '../components/subheaders/index.jsx';

import Invitation from '../../accountsettings/components/invitation.jsx';
import SubscriptionDetail from '../../accountsettings/components/subscription-detail.jsx';
import { GenericError } from '../../common/errors.jsx';
import useSubscriptionData from '../../hooks/useSubscriptionData.js';

export const title = gettext('Manage monthly subscription');
export const successMsg = gettext(
    'Your monthly subscription has been successfully canceled.'
);

const ManagementPage = ({ data, locale }: RouteComponentProps): React.Node => {
    const email = data.contributionSupportEmail;
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

    const onDeleteSuccess = () => {
        subscription = null;
        setCanceled(true);
        setStatus('success');
    };

    const renderSuccess = () => (
        <p className="alert success" data-testid="success-msg">
            {successMsg}
        </p>
    );

    const renderSubscriptions = () => {
        if (!subscription) {
            return false;
        }

        return (
            <SubscriptionDetail
                locale={locale}
                onDeleteSuccess={onDeleteSuccess}
                subscription={subscription}
                contributionSupportEmail={email}
            />
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
                return <Invitation locale={locale} />;
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
                        {status === 'success' && renderSuccess()}
                        {renderContent()}
                    </div>
                </section>
            </main>
        </>
    );
};

export default ManagementPage;
