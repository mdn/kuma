// @flow
import * as React from 'react';

// import { getLocale, gettext, Interpolated } from '../l10n.js';
import A11yNav from '../a11y/a11y-nav.jsx';
import Header from '../header/header.jsx';
import Footer from '../footer.jsx';
import Route from '../route.js';

type ExampleRouteParams = {
    locale: string
};

export default function ExamplePage() {
    return (
        <>
            <A11yNav />
            <Header />
            Hello!
            <Footer />
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

export class ExampleRoute extends Route<ExampleRouteParams, null> {
    locale: string;

    constructor(locale: string) {
        super();
        this.locale = locale;
    }

    getComponent() {
        return ExamplePage;
    }

    match(url: string): ?ExampleRouteParams {
        const path = new URL(url, BASEURL).pathname;
        const examplePath = `/${this.locale}/payments/thank-you`;
        const regex = new RegExp(examplePath, 'g');

        if (regex.test(path)) {
            return {
                locale: this.locale
            };
        }
        return null;
    }

    fetch() {
        return Promise.resolve(null);
    }
}
