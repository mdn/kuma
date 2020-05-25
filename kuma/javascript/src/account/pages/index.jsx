// @flow
import * as React from 'react';
import { useContext } from 'react';

import { gettext } from '../../l10n.js';
import { type RouteComponentProps } from '../../route.js';
import UserProvider from '../../user-provider.jsx';

import Titlebar from '../components/titlebar.jsx';

export const pageTitle = gettext('Account Settings');

export default function LandingPage({ locale }: RouteComponentProps) {
    const userData = useContext(UserProvider.context);

    return (
        <main role="main" data-testid="landing-page">
            <Titlebar
                locale={locale}
                pageTitle={pageTitle}
                userData={userData}
            />
        </main>
    );
}
