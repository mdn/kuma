// @flow
import * as React from 'react';
import Route from '../route.js';
import Page from '../base/page.jsx';
import LandingPage from './pages/index.jsx';

type AccountRoutesParams = {
    locale: string,
    slug: string,
};

type AccountPageProps = AccountRoutesParams & {
    data: any,
};

export const ACCOUNT_PATHS = {
    MANAGE_EMAIL: 'manage-email',
    SUBSCRIPTION: 'subscription',
};

export function AccountPage(props: AccountPageProps) {
    const { locale } = props;
    const getPage = () => {
        switch (true) {
            default:
                return <LandingPage locale={locale} />;
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

export class AccountRoutes extends Route<AccountRoutesParams, null> {
    locale: string;

    constructor(locale: string) {
        super();
        this.locale = locale;
    }

    getComponent() {
        return AccountPage;
    }

    match(url: string): ?AccountRoutesParams {
        const currentPath = new URL(url, BASEURL).pathname;
        const accountPath = `/${this.locale}/account`;

        if (currentPath.startsWith(accountPath)) {
            return {
                locale: this.locale,
                slug: currentPath.substring(accountPath.length),
            };
        }
        return null;
    }
}
