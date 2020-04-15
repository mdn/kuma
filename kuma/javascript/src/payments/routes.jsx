// @flow
import * as React from 'react';
import Route, { type RouteComponentProps } from '../route.js';
import Page from './pages/page.jsx';
import LandingPage from './pages/index.jsx';
import ThankYouPage from './pages/thank-you.jsx';
import TermsPage from './pages/terms.jsx';

type PaymentRoutesParams = {
    locale: string,
    slug: string,
};

export const PAYMENT_PATHS = {
    THANK_YOU: 'thank-you',
    TERMS: 'terms',
};

export default function PaymentPage(props: RouteComponentProps) {
    const { locale, slug, data } = props;

    // remove forward slashes
    const pathname = slug.replace(/\//g, '');

    return (
        <Page>
            {{
                [PAYMENT_PATHS.THANK_YOU]: <ThankYouPage locale={locale} />,
                [PAYMENT_PATHS.TERMS]: <TermsPage />,
            }[pathname] || <LandingPage data={data} locale={locale} />}
        </Page>
    );
}

// In order to use new URL() with relative URLs, we need an absolute base
// URL. If we're running in the browser we can use our current page URL.
// But if we're doing SSR, we just have to make something up.
const BASEURL =
    typeof window !== 'undefined' && window.location
        ? window.location.origin
        : 'http://ssr.hack';

export class PaymentRoutes extends Route<PaymentRoutesParams, null> {
    locale: string;

    constructor(locale: string) {
        super();
        this.locale = locale;
    }

    getComponent() {
        return PaymentPage;
    }

    match(url: string): ?PaymentRoutesParams {
        const currentPath = new URL(url, BASEURL).pathname;
        const paymentsPath = `/${this.locale}/payments`;

        if (currentPath.startsWith(paymentsPath)) {
            return {
                locale: this.locale,
                slug: currentPath.substring(paymentsPath.length),
            };
        }
        return null;
    }
}
