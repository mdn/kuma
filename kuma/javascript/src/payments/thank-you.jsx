// @flow
import * as React from 'react';
import { useContext } from 'react';

import { getLocale, gettext, Interpolated } from '../l10n.js';
import A11yNav from '../a11y/a11y-nav.jsx';
import Header from '../header/header.jsx';
import ThankYouSubheader from './subheaders/thank-you.jsx';
import Incentives from './incentives.jsx';
import Footer from '../footer.jsx';
import Route from '../route.js';
import FeedbackForm from './feedback-form.jsx';
import UserProvider from '../user-provider.jsx';

type PaymentsThankYouRouteParams = {
    locale: string,
};

export default function ThankYouPage() {
    const locale = getLocale();
    const userData = useContext(UserProvider.context);
    const isSubscriber = userData && userData.isSubscriber;
    const subscriberNumber = userData && userData.subscriberNumber;

    return (
        <>
            <A11yNav />
            <Header />
            <ThankYouSubheader num={isSubscriber ? subscriberNumber : null} />
            <Incentives isSubscriber={isSubscriber} locale="locale" />
            <main className="contributions-page thank-you" role="main">
                <section className="section">
                    <header>
                        <h2>{gettext('Useful things')}</h2>
                    </header>
                    <ul data-testid="useful-things" className="clear">
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
                                            href={`/${locale}/payments/recurring/management/`}
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
                                        <a href={`/${locale}/payments/terms/`}>
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
                    <FeedbackForm />
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
                locale: this.locale,
            };
        }
        return null;
    }

    fetch() {
        throw new Error('Payments should never need to post-fetch more data');
    }
}
