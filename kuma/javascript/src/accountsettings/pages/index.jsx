// @flow
import * as React from 'react';
import { useContext } from 'react';

import { gettext, Interpolated } from '../../l10n.js';
import { type RouteComponentProps } from '../../route.js';
import UserProvider from '../../user-provider.jsx';

import SignInLink from '../../signin-link.jsx';
import Titlebar from '../components/titlebar.jsx';
import UserDetails from '../components/user-details.jsx';
import Subscription from '../components/subscription.jsx';
import CloseAccount from '../components/close-account.jsx';

export const pageTitle = gettext('Account Settings');
const pageSubtitle = gettext('Update your details and manage your preferences');

export default function LandingPage({ data, locale }: RouteComponentProps) {
    const contributionSupportEmail = data.contributionSupportEmail;
    const userData = useContext(UserProvider.context);

    return (
        <main id="content" role="main" data-testid="landing-page">
            {userData && !userData.isAuthenticated && (
                <p className="account-girdle signin-required">
                    <Interpolated
                        id={gettext(
                            'You need to be <signInLink /> to access account settings.'
                        )}
                        signInLink={<SignInLink text={gettext('signed in')} />}
                    />
                </p>
            )}

            {userData && userData.isAuthenticated && userData.username && (
                <>
                    <Titlebar
                        pageTitle={pageTitle}
                        pageSubtitle={pageSubtitle}
                        userData={userData}
                    />
                    <UserDetails
                        locale={locale}
                        userData={userData}
                        sortedLanguages={data.sortedLanguages}
                    />
                    <Subscription
                        locale={locale}
                        userData={userData}
                        contributionSupportEmail={contributionSupportEmail}
                    />
                    <CloseAccount
                        locale={locale}
                        username={userData.username}
                    />
                </>
            )}
        </main>
    );
}
