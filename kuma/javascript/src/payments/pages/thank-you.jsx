// @flow
import * as React from 'react';
import { useContext } from 'react';

import { gettext, Interpolated } from '../../l10n.js';
import ThankYouSubheader from '../components/subheaders/thank-you.jsx';
import Incentives from '../components/incentives.jsx';
import FeedbackForm from '../components/feedback-form.jsx';
import UserProvider from '../../user-provider.jsx';

type Props = {
    locale: string,
};

const ThankYouPage = ({ locale }: Props) => {
    const userData = useContext(UserProvider.context);
    const isSubscriber = userData && userData.isSubscriber;
    const subscriberNumber = userData && userData.subscriberNumber;

    return (
        <>
            <ThankYouSubheader num={isSubscriber ? subscriberNumber : null} />
            <Incentives isSubscriber={isSubscriber} />
            <main
                className="contributions-page thank-you"
                role="main"
                data-testid="thank-you-page"
            >
                <section>
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
        </>
    );
};

export default ThankYouPage;
