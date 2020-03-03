// @flow
import * as React from 'react';

import { gettext } from '../l10n.js';
import A11yNav from '../a11y/a11y-nav.jsx';
import Header from '../header/header.jsx';
import Footer from '../footer.jsx';
import UserProvider from '../user-provider.jsx';
import Route from '../route.js';

type PaymentsRouteParams = {
    locale: string
};

export default function PaymentsLandingPage() {
    return (
        <>
            <UserProvider>
                <A11yNav />
                <Header />
                <Footer />
            </UserProvider>
        </>
    );
}

// In order to use new URL() with relative URLs, we need an absolute base
// URL. If we're running in the browser we can use our current page URL.
// But if we're doing SSR, we just have to make something up.
const BASEURL =
    typeof window !== 'undefined' && window.location
        ? window.location.origin
        : 'http://ssr.hack';

export class PaymentsRoute extends Route<PaymentsRouteParams, null> {
    locale: string;

    constructor(locale: string) {
        super();
        this.locale = locale;
    }

    getComponent() {
        return PaymentsLandingPage;
    }

    match(url: string): ?PaymentsRouteParams {
        let path = new URL(url, BASEURL).pathname;

        if (path !== `/${this.locale}/payments/`) {
            return null;
        }

        return {
            locale: this.locale
        };
    }

    fetch() {
        return Promise.resolve(null);
    }

    getTitle() {
        return `${gettext('Contribute')} | MDN`;
    }
}
