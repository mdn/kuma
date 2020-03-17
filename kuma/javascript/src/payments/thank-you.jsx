// @flow
import * as React from 'react';

import { getLocale, gettext, Interpolated } from '../l10n.js';
import A11yNav from '../a11y/a11y-nav.jsx';
import Header from '../header/header.jsx';
import SubHeader from './subheader.jsx';
import Footer from '../footer.jsx';
import Route from '../route.js';

type PaymentsThankYouRouteParams = {
    locale: string
};

export default function ThankYouPage() {
    const locale = getLocale();
    return (
        <>
            <A11yNav />
            <Header />
            <SubHeader title="Thank you for becoming a monthly supporter!" />
            <main className="contributions-page thank-you" role="main">
                <section className="section">
                    <header>
                        <h2>{gettext('Useful things')}</h2>
                    </header>
                    <ul id="useful-things" className="clear">
                        <li>
                            <h3>
                                {gettext('Cancel or manage your subscription')}
                            </h3>
                            <p>
                                <Interpolated
                                    id={gettext(
                                        'If you would like to cancel or manage your monthly subscription, go to <subscriptionLink />.'
                                    )}
                                    subscriptionLink={
                                        <a
                                            href={`/${locale}/payments/recurring/management`}
                                        >
                                            {gettext(
                                                'manage monthly subscription page'
                                            )}
                                        </a>
                                    }
                                />
                            </p>
                        </li>
                        <li>
                            <h3>{gettext('Subscription terms')}</h3>
                            <p>
                                <Interpolated
                                    id={gettext(
                                        'Please read our <termsLink /> for more information.'
                                    )}
                                    termsLink={
                                        <a href={`/${locale}/payments/terms`}>
                                            {gettext('subscription terms')}
                                        </a>
                                    }
                                />
                            </p>
                        </li>
                        <li>
                            <h3>{gettext('FAQ')}</h3>
                            <p>
                                <Interpolated
                                    id={gettext(
                                        'To find out more about why MDN is raising money through monthly subscriptions, please visit our <faqLink />.'
                                    )}
                                    faqLink={
                                        <a href={`/${locale}/payments/`}>
                                            {gettext('FAQ')}
                                        </a>
                                    }
                                />
                            </p>
                        </li>
                    </ul>
                </section>
                <section className="section">
                    <header>
                        <h2>{gettext('Feedback')}</h2>
                    </header>
                    <form>
                        <input
                            type="text"
                            placeholder={gettext('Enter optional feedback…')}
                        />
                        <div>
                            <button type="submit">{gettext('Send')}</button>
                        </div>
                    </form>
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

export class PaymentsThankYouRoute extends Route<
    PaymentsThankYouRouteParams,
    null
> {
    locale: string;

    constructor(locale: string) {
        super();
        this.locale = locale;
    }

    getComponent() {
        return ThankYouPage;
    }

    match(url: string): ?PaymentsThankYouRouteParams {
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
