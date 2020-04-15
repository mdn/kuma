// @flow
import * as React from 'react';

import { DocumentRoute } from './document.jsx';
import { getLocale } from './l10n.js';
import Router from './router.jsx';
import { SearchRoute } from './search-results-page.jsx';
import UserProvider from './user-provider.jsx';
import { PaymentRoutes } from './payments/routes.jsx';

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
        new PaymentRoutes(locale),
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
