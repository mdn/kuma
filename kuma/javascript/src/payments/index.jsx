// @flow
import * as React from 'react';

import { getLocale, gettext, Interpolated } from '../l10n.js';
import A11yNav from '../a11y/a11y-nav.jsx';
import Header from '../header/header.jsx';
import Footer from '../footer.jsx';
import UserProvider from '../user-provider.jsx';
import Route from '../route.js';
import SubHeader from './subheader.jsx';
import ListItem from './list-item.jsx';

type PaymentsRouteParams = {
    locale: string
};

export default function PaymentsLandingPage() {
    const locale = getLocale();
    const urls = {
        annualReport:
            'https://www.mozilla.org/en-US/foundation/annualreport/2016/',
        email:
            'mailto:mdn-support@mozilla.com?Subject=Manage%20monthly%20payment',
        moco: 'https://www.mozilla.org/foundation/moco/',
        mozillaFoundation: 'https://www.mozilla.org/foundation/',
        managePayments: `/${locale}/payments/recurring/management`,
        stripe: 'https://stripe.com/',
        taxDeductible: 'https://donate.mozilla.org/faq#item_tax_a',
        terms: `/${locale}/payments/terms`
    };

    return (
        <>
            <UserProvider>
                <A11yNav />
                <Header />
                <SubHeader
                    title="Become a monthly supporter"
                    description="Support MDN with a $5 monthly subscription and get back more of the knowledge and tools you rely on for when your work has to work."
                    columnWidth="7"
                />
                <main
                    id="contributions-page"
                    className="contributions-page"
                    role="main"
                >
                    <section className="section">
                        <img
                            src="/static/img/hero-dino-blank.png"
                            className="backdrop-image"
                            alt=""
                            role="presentation"
                        />
                        <header>
                            <h2>{gettext('FAQs')}</h2>
                        </header>
                        <ol id="contribute-faqs" className="faqs clear">
                            <ListItem
                                title="Why is MDN asking me for money?"
                                number="1"
                            >
                                <p>
                                    {gettext(
                                        'MDN is experimenting with seeking direct support from our users in order to accelerate growing and maintaining our content and platform, with assistance from those who use it.'
                                    )}
                                </p>
                                <p>
                                    {gettext(
                                        'Our user base has grown exponentially in the last few years (with corresponding costs of maintaining the platform) and we have a large list of improvements we’d like to make. While MDN is currently wholly funded by Mozilla, and has been since its inception, we are looking to create a tighter, healthier loop between our audience (you), our content (written for you), and our supporters (also, you, again) that lets us accelerate those improvements.'
                                    )}
                                </p>
                            </ListItem>
                            <ListItem
                                title="How is my payment handled? Is it secure?"
                                number="2"
                            >
                                <p>
                                    <Interpolated
                                        id={gettext(
                                            'All payment information goes through payment processor <stripeLink />, and a record of your payment will be stored by Mozilla. Mozilla does not receive or store your credit card number.'
                                        )}
                                        stripeLink={
                                            <a
                                                href={urls.stripe}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                            >
                                                {gettext('Stripe')}
                                            </a>
                                        }
                                    />
                                </p>
                            </ListItem>
                            <ListItem
                                title="What data is Mozilla collecting about me?"
                                number="3"
                            >
                                <p>
                                    {gettext(
                                        'Mozilla will collect and store your name and email, which will be used to send transactional emails (e.g. receipt). Mozilla will not have access to or store your credit card number.'
                                    )}
                                </p>
                            </ListItem>
                            <ListItem
                                title="What does money go towards?"
                                number="4"
                            >
                                <p>
                                    {gettext(
                                        'The money collected through MDN (minus processing fees, taxes, etc.) will be reinvested back into MDN. We will publish a monthly report on MDN Web Docs showing what work was completed.'
                                    )}
                                </p>
                            </ListItem>
                            <ListItem
                                title="If I just donate to the Mozilla Foundation, will that help MDN?"
                                number="5"
                            >
                                <p>
                                    <Interpolated
                                        id={gettext(
                                            'The <mozillaLink /> and MDN are separate organizations and programs. Donations to the Mozilla Foundation are <taxLink /> to the fullest extent permitted by law, and go to support Mozilla public and charitable programs in one general fund. MDN is part of <mocoLink /> and payments to MDN are not used in Mozilla’s charitable programs but are reinvested into MDN’s content, tools, and platform.'
                                        )}
                                        mozillaLink={
                                            <a
                                                href={urls.mozillaFoundation}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                            >
                                                {gettext('Mozilla Foundation')}
                                            </a>
                                        }
                                        taxLink={
                                            <a href={urls.taxDeductible}>
                                                {gettext(
                                                    'tax-deductible in the U.S.'
                                                )}
                                            </a>
                                        }
                                        mocoLink={
                                            <a href={urls.moco}>
                                                {gettext('Mozilla Corporation')}
                                            </a>
                                        }
                                    />
                                </p>
                            </ListItem>
                            <ListItem
                                title="Is support of MDN tax-deductible?"
                                number="6"
                            >
                                <p>
                                    {gettext(
                                        'No. Payments to Mozilla Corporation in support of MDN are not tax deductible in the United States or other countries.'
                                    )}
                                </p>
                            </ListItem>
                            <ListItem
                                title="What will MDN user funding pay for?"
                                number="7"
                            >
                                <p>
                                    {gettext(
                                        'Currently, Mozilla pays for site operations and overhead (including writers and web developers). MDN user payments will fund accelerating current projects or launching new ones, including:'
                                    )}
                                </p>
                                <ul>
                                    <li>
                                        {gettext(
                                            'Adding more content, and updating current content'
                                        )}
                                    </li>
                                    <li>
                                        {gettext(
                                            'Improving performance of the site'
                                        )}
                                    </li>
                                    <li>
                                        {gettext(
                                            'Modernizing the MDN platform'
                                        )}
                                    </li>
                                    <li>
                                        {gettext(
                                            'Adding offline access to MDN'
                                        )}
                                    </li>
                                    <li>
                                        {gettext(
                                            'Supporting integrations with popular developer tools'
                                        )}
                                    </li>
                                    <li>
                                        {gettext('More tutorials and guides')}
                                    </li>
                                    <li>{gettext('Training and webinars')}</li>
                                </ul>
                            </ListItem>
                            <ListItem
                                title="Why can’t you just open a Crowdsourcing campaign?"
                                number="8"
                            >
                                <p>
                                    {gettext(
                                        'Because we aren’t looking for a lump sum. Our goal is to create a broad base of financial support from the people who benefit from the work of MDN.'
                                    )}
                                </p>
                            </ListItem>
                            <ListItem
                                title="How has MDN been funded to date?"
                                number="9"
                            >
                                <p>
                                    {gettext(
                                        'MDN is funded out of the Mozilla Corporation general budget (and has been since it was founded in 2005). Mozilla Corporation intends to continue to financially support MDN into the future, even as we broaden and diversify the sources of MDN funding. We just want to do more things with you and for you!'
                                    )}
                                </p>
                            </ListItem>
                            <ListItem
                                title="How does Mozilla make money?"
                                number="10"
                            >
                                <p>
                                    {gettext(
                                        'The Mozilla Corporation, which funds MDN, makes money primarily from royalties from search providers on Firefox (such as Google, Amazon, DuckDuckGo, and others).'
                                    )}
                                </p>
                                <p>
                                    <Interpolated
                                        id={gettext(
                                            'Separately, the Mozilla Foundation is a not-for-profit, making its money primarily from donations and royalties from Mozilla Corporation. As a not-for-profit, the Mozilla Foundation reports these revenues publicly every trailing year, as in our most recent <annualReportLink />.'
                                        )}
                                        annualReportLink={
                                            <a href={urls.annualReport}>
                                                {gettext(
                                                    '2016 Mozilla Annual Report'
                                                )}
                                            </a>
                                        }
                                    />
                                </p>
                            </ListItem>
                        </ol>
                    </section>
                    <section className="section">
                        <header>
                            <h2>{gettext('Monthly payments')}</h2>
                        </header>
                        <ol id="contribute-monthly-faqs" className="faqs clear">
                            <ListItem
                                title="How do I manage my monthly payment?"
                                number="11"
                            >
                                <p>
                                    <Interpolated
                                        id={gettext(
                                            'If you would like to manage your monthly payment, such as changing your card account details or the amount you pay, please cancel your subscription on the <subscriptionsLink /> and sign up again using the new card details. If you have any questions please contact <emailLink />.'
                                        )}
                                        subscriptionsLink={
                                            <a href={urls.managePayments}>
                                                {gettext(
                                                    'manage monthly subscriptions page'
                                                )}
                                            </a>
                                        }
                                        emailLink={
                                            <a href={urls.email}>
                                                {gettext(
                                                    'mdn-support@mozilla.com'
                                                )}
                                            </a>
                                        }
                                    />
                                </p>
                            </ListItem>
                            <ListItem
                                title="How do I apply for a refund or cancel my payment?"
                                number="12"
                            >
                                <p>
                                    <Interpolated
                                        id={gettext(
                                            'If you would like to cancel your monthly payment or apply for a refund, you are free to do so at any point. Please cancel your subscription on the <subscriptionsLink /> . If you choose to cancel, we will not charge your payment card for subsequent months.'
                                        )}
                                        subscriptionsLink={
                                            <a href={urls.managePayments}>
                                                {gettext(
                                                    'manage monthly subscriptions page'
                                                )}
                                            </a>
                                        }
                                    />
                                </p>
                            </ListItem>

                            <ListItem
                                title="What are the payment terms?"
                                number="13"
                            >
                                <p>
                                    <Interpolated
                                        id={gettext(
                                            'Please read our <paymentLink /> for more information.'
                                        )}
                                        paymentLink={
                                            <a href={urls.terms}>
                                                {gettext('payment terms')}
                                            </a>
                                        }
                                    />
                                </p>
                            </ListItem>
                            <ListItem
                                title="Does deleting my MDN account cancel my subscription?"
                                number="14"
                            >
                                <p>
                                    {gettext(
                                        'When you request to delete your account we will also cancel your subscription and not charge you for subsequent months.'
                                    )}
                                </p>
                            </ListItem>
                        </ol>
                    </section>
                </main>
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
