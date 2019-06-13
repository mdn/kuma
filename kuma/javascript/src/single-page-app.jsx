// @flow
import * as React from 'react';

import { DocumentRoute } from './document.jsx';
import GAProvider from './ga-provider.jsx';
import { getLocale } from './l10n.js';
import Router from './router.jsx';
import { SearchRoute } from './search-results-page.jsx';
import UserProvider from './user-provider.jsx';

type SinglePageAppProps = {
    initialURL: string,
    initialData: any
};

export default function SinglePageApp({
    initialURL,
    initialData
}: SinglePageAppProps) {
    const locale = getLocale();
    const routes = [new DocumentRoute(locale), new SearchRoute(locale)];

    return (
        <GAProvider>
            <UserProvider>
                <Router
                    routes={routes}
                    initialURL={initialURL}
                    initialData={initialData}
                />
            </UserProvider>
        </GAProvider>
    );
}
