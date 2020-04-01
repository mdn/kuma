// @flow
import * as React from 'react';

import { DocumentRoute } from './document.jsx';
import { getLocale } from './l10n.js';
import Router from './router.jsx';
import { SearchRoute } from './search-results-page.jsx';
import UserProvider from './user-provider.jsx';
import { PaymentsIndexRoute } from './payments/index.jsx';
import { PaymentsThankYouRoute } from './payments/thank-you.jsx';

type SinglePageAppProps = {
    initialURL: string,
    initialData: any,
};

export default function SinglePageApp({
    initialURL,
    initialData,
}: SinglePageAppProps) {
    const locale = getLocale();
    const routes = [
        new DocumentRoute(locale),
        new SearchRoute(locale),
        new PaymentsThankYouRoute(locale),
        new PaymentsIndexRoute(locale),
    ];

    return (
        <UserProvider>
            <Router
                routes={routes}
                initialURL={initialURL}
                initialData={initialData}
            />
        </UserProvider>
    );
}
