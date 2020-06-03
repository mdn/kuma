// @flow
import * as React from 'react';
import { useContext } from 'react';

import { gettext } from '../../l10n.js';
import { type RouteComponentProps } from '../../route.js';
import UserProvider from '../../user-provider.jsx';

import SignInLink from '../../signin-link.jsx';
import Titlebar from '../components/titlebar.jsx';
import UserDetails from '../components/user-details.jsx';

export const pageTitle = gettext('Account Settings');
const pageSubtitle = gettext('Update your details and manage your preferences');

export default function LandingPage({ data, locale }: RouteComponentProps) {
    const userData = useContext(UserProvider.context);

    return (
        <main id="content" role="main" data-testid="landing-page">
            {userData && userData.isAuthenticated && (
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
                </>
            )}

            {userData && !userData.isAuthenticated && (
                <p className="account-girdle signin-required">
                    {gettext(
                        'You need to be signed in to access account settings. '
                    )}
                    <SignInLink />
                </p>
            )}
        </main>
    );
}
