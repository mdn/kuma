// @flow
import * as React from 'react';
import { useState } from 'react';

import { gettext, interpolate, Interpolated } from '../../l10n.js';
import { formatDate, formatMoney } from '../../formatters.js';

import { type SubscriptionData } from '../../hooks/useSubscriptionData.js';
import CancelSubscriptionForm from './cancel-subscription-form.jsx';

type Props = {
    contributionSupportEmail: string,
    onDeleteSuccess: Function,
    locale: string,
    subscription: SubscriptionData,
};

const SubscriptionDetail = ({
    contributionSupportEmail,
    onDeleteSuccess,
    locale,
    subscription,
}: Props) => {
    const nextPaymentDate = formatDate(locale, subscription.next_payment_at);
    const amount = formatMoney(locale, subscription.amount / 100);
    const date = new Date(subscription.next_payment_at);
    const lastActiveDate = formatDate(locale, date.setDate(date.getDate() - 1));
    const urls = {
        email: `mailto:${contributionSupportEmail}?Subject=Manage%20monthly%20subscription`,
        paymentsIndex: `/${locale}/payments`,
        paymentsThankyou: `/${locale}/payments/thank-you`,
    };
    const [showForm, setShowForm] = useState<boolean>(false);

    return (
        <>
            <div className="lead-in">
                <p>
                    {interpolate(
                        'Next payment of %(amount)s (monthly) occurs on %(nextPaymentDate)s.',
                        {
                            amount,
                            nextPaymentDate,
                        }
                    )}
                </p>

                <button
                    className="cta negative"
                    onClick={() => {
                        setShowForm(true);
                    }}
                    type="button"
                >
                    {gettext('Cancel subscription')}
                </button>
            </div>

            {showForm && (
                <CancelSubscriptionForm
                    onSuccess={onDeleteSuccess}
                    onCancel={() => setShowForm(false)}
                    date={lastActiveDate}
                />
            )}

            <ul className="active-subscriptions">
                <li className="credit-card">
                    {gettext(
                        `${subscription.brand} ending in ${subscription.last4}`
                    )}
                </li>
                <li>{gettext(`Expires ${subscription.expires_at}`)}</li>
                <li>{gettext(`Postal/Zip Code: ${subscription.zip}`)}</li>
            </ul>

            <footer className="subscription-footer">
                <ul>
                    <li>
                        <Interpolated
                            id={gettext(
                                'To see your member perks, visit the <thankYouLink />'
                            )}
                            thankYouLink={
                                <a href={urls.paymentsThankyou}>
                                    {gettext('thank you page.')}
                                </a>
                            }
                        />
                    </li>
                    <li>
                        <Interpolated
                            id={gettext(
                                'If you have questions, please read the <faqLink /> or you can also <supportEmail />'
                            )}
                            faqLink={
                                <a href={urls.paymentsIndex}>
                                    {gettext('FAQ')}
                                </a>
                            }
                            supportEmail={
                                <a href={urls.email}>
                                    {gettext('contact support.')}
                                </a>
                            }
                        />
                    </li>
                </ul>
            </footer>
        </>
    );
};

export default SubscriptionDetail;
