// @flow
import * as React from 'react';

import { gettext } from '../l10n.js';
import A11yNav from '../a11y/a11y-nav.jsx';
import Header from '../header/header.jsx';
import Footer from '../footer.jsx';
import Route from '../route.js';

type ThankYouRouteParams = {
    locale: string
};

export default function ThankYouPage() {
    return (
        <>
            <A11yNav />
            <Header />
            <main
                id="contributions-page"
                className="contributions-page"
                role="main"
            >
                <section className="section">
                    <header>
                        <h2>{gettext('Useful things')}</h2>
                        <ul id="useful-things" className="faqs clear">
                            <li>
                                <h3>Cancel or manage your subscription</h3>
                                <p>
                                    If you would like to cancel or manage your
                                    monthly subscription, go to manage monthly
                                    subscription page.
                                </p>
                            </li>
                            <li>
                                <h3>Subscription terms</h3>
                                <p>
                                    Please read our subscription terms for more
                                    information.
                                </p>
                            </li>
                            <li>
                                <h3>FAQ</h3>
                                <p>
                                    To find out more about why MDN is raising
                                    money through monthly subscriptions, please
                                    visit our FAQ.
                                </p>
                            </li>
                        </ul>
                    </header>
                </section>
                <section className="section">
                    <header>
                        <h2>{gettext('Feedback')}</h2>
                        <form>
                            <input
                                type="text"
                                placeholder={gettext('Enter optional feedback')}
                            />
                            <button type="submit">{gettext('Send')}</button>
                        </form>
                    </header>
                </section>
            </main>
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

export class ThankYouRoute extends Route<ThankYouRouteParams, null> {
    locale: string;

    constructor(locale: string) {
        super();
        this.locale = locale;
    }

    getComponent() {
        return ThankYouPage;
    }

    match(url: string): ?ThankYouRouteParams {
        const currentPath = new URL(url, BASEURL).pathname;
        const thankYouPath = `/${this.locale}/payments/thank-you`;
        if (currentPath.startsWith(thankYouPath)) {
            return {
                locale: this.locale
            };
        }
        return null;
    }

    fetch() {
        return Promise.resolve(null);
        // throw new Error('Payments should never need to post-fetch more data');
    }
}
