// @flow
import * as React from 'react';

import { DocumentRoute } from './document.jsx';
import GAProvider from './ga-provider.jsx';
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
    return (
        <GAProvider>
            <UserProvider>
                <Router
                    routes={[DocumentRoute, SearchRoute]}
                    initialURL={initialURL}
                    initialData={initialData}
                />
            </UserProvider>
        </GAProvider>
    );
}
