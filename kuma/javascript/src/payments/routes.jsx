// @flow
import * as React from 'react';
import Route from '../route.js';
import Page from './pages/page.jsx';
import LandingPage from './pages/index.jsx';
import ThankYouPage from './pages/thank-you.jsx';
import TermsPage from './pages/terms.jsx';

type PaymentRoutesParams = {
    locale: string,
    slug: string,
};

type PaymentPageProps = PaymentRoutesParams & {
    data: any,
};

export const PAYMENT_PATHS = {
    TERMS: 'terms',
    THANK_YOU: 'thank-you',
};

export function PaymentPage(props: PaymentPageProps) {
    const { locale, slug, data } = props;
    const getPage = () => {
        switch (true) {
            case slug.includes(PAYMENT_PATHS.TERMS):
                return <TermsPage data={data} />;
            case slug.includes(PAYMENT_PATHS.THANK_YOU):
                return <ThankYouPage locale={locale} />;
            default:
                return <LandingPage data={data} locale={locale} />;
        }
    };

    return <Page>{getPage()}</Page>;
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
