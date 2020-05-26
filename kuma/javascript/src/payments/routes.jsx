// @flow
import * as React from 'react';
import Route from '../route.js';
import Page from '../base/page.jsx';
import { type PageProps, type PageRoutesParams } from '../base/page.jsx';

import LandingPage from './pages/index.jsx';
import ManagementPage from './pages/management.jsx';
import ThankYouPage from './pages/thank-you.jsx';
import TermsPage from './pages/terms.jsx';

export const PAYMENT_PATHS = {
    MANAGEMENT: 'management',
    TERMS: 'terms',
    THANK_YOU: 'thank-you',
};

export function PaymentPage(props: PageProps) {
    const { locale, slug = '', data } = props;
    const getPage = () => {
        switch (true) {
            case slug.includes(PAYMENT_PATHS.MANAGEMENT):
                return <ManagementPage locale={locale} />;
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

export class PaymentRoutes extends Route<PageRoutesParams, null> {
    locale: string;

    constructor(locale: string) {
        super();
        this.locale = locale;
    }

    getComponent() {
        return PaymentPage;
    }

    match(url: string): ?PageRoutesParams {
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
