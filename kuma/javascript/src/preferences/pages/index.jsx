// @flow
import * as React from 'react';
import { useContext } from 'react';

import { gettext } from '../../l10n.js';
import UserProvider from '../../user-provider.jsx';

import Titlebar from '../components/titlebar.jsx';
import SignInLink from '../../signin-link.jsx';

type Props = {
    locale: string,
};

export const pageTitle = gettext('Account Settings');

export default function LandingPage({ locale }: Props) {
    const userData = useContext(UserProvider.context);

    return (
        <main id="content" role="main" data-testid="landing-page">
            {userData && userData.isAuthenticated && (
                <Titlebar
                    locale={locale}
                    pageTitle={pageTitle}
                    userData={userData}
                />
            )}

            {userData && !userData.isAuthenticated && (
                <p className="signin-required">
                    {gettext(
                        'You need to be signed in to access user preferences. '
                    )}
                    <SignInLink />
                </p>
            )}
        </main>
    );
}
