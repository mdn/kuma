// @flow
import * as React from 'react';
import Route from '../route.js';
import Page from '../base/page.jsx';
import { type PageProps, type PageRoutesParams } from '../base/page.jsx';

import LandingPage from './pages/index.jsx';

export const PREFERENCES_PATHS = {
    MANAGE_EMAIL: 'manage-email',
    SUBSCRIPTION: 'subscription',
};

export function PreferencesPage(props: PageProps) {
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

export class PreferencesRoutes extends Route<PageRoutesParams, null> {
    locale: string;

    constructor(locale: string) {
        super();
        this.locale = locale;
    }

    getComponent() {
        return PreferencesPage;
    }

    match(url: string): ?PageRoutesParams {
        const currentPath = new URL(url, BASEURL).pathname;
        const preferencesPath = `/${this.locale}/preferences`;

        if (currentPath.startsWith(preferencesPath)) {
            return {
                locale: this.locale,
                slug: currentPath.substring(preferencesPath.length),
            };
        }
        return null;
    }
}
