// @flow
import React from 'react';

import SinglePageApp from './single-page-app.jsx';
import LandingPage from './landing-page.jsx';
import SignupFlow from './signup-flow.jsx';
import UserAccount from './user-account/user-account.jsx';

export type AppProps = {
    // The root component name of the page - SPA, landing or signupflow
    componentName: string,

    // Data needed to hydrate or render the UI
    data: any
};

export default function App({ componentName, data }: AppProps) {
    switch (componentName) {
        case 'SPA':
            // Ideally, we want as much as possible of MDN to be part
            // of the single page app so that we can get client-side
            // navigation between pages. Currently the single page app
            // handles document pages and search results
            return (
                <SinglePageApp
                    initialURL={data.url}
                    initialData={data.documentData}
                />
            );
        case 'landing':
            // This is the React UI for the MDN homepage.
            // The homepage has a React-based header, but most of the
            // content is still based on Jinja templates, so we can't
            // currently make it part of the single page app and have
            // to handle it as a special case here.
            return <LandingPage />;
        case 'signupflow':
            // This is the React UI for the MDN sign-up flow.
            // The signup flow has a React-based header, but most of the
            // content is still based on Jinja templates, so we can't
            // currently make it part of the single page app and have
            // to handle it as a special case here.
            return <SignupFlow />;
        case 'user-account':
            // This is the React UI for the MDN user account page.
            // The user account has a React-based header, but most of the
            // content is still based on Jinja templates, so we can't
            // currently make it part of the single page app and have
            // to handle it as a special case here.
            return <UserAccount />;
        default:
            return null;
    }
}
