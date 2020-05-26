// @flow
import * as React from 'react';
import { useContext } from 'react';

import { gettext } from '../../l10n.js';
import UserProvider from '../../user-provider.jsx';

import Titlebar from '../components/titlebar.jsx';

type Props = {
    locale: string,
};

export const pageTitle = gettext('Account Settings');

export default function LandingPage({ locale }: Props) {
    const userData = useContext(UserProvider.context);

    return (
        <main id="content" role="main" data-testid="landing-page">
            <Titlebar
                locale={locale}
                pageTitle={pageTitle}
                userData={userData}
            />
        </main>
    );
}
