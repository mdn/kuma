// @flow
import * as React from 'react';
import { useRef, useState } from 'react';

import { getLocale, gettext, Interpolated } from '../l10n.js';

type Props = {
    showSubscriptionForm: boolean
};

export default function SubscriptionForm({ showSubscriptionForm }: Props) {
    const locale = getLocale();
    const subscriptionFormRef = useRef(null);
    const [subscribeFormDisabled, setSubscribeFormDisabled] = useState(false);
    const [subscribeButtonEnabled, setSubscribeButtonEnabled] = useState(false);

    if (!showSubscriptionForm) {
        return null;
    }

    const toggleButton = () => {
        setSubscribeButtonEnabled(!subscribeButtonEnabled);
    };

    /**
     * Opens Stripe modal allowing a user to complete their subscription.
     * @param {Object} event - The form submit event
     */
    const submit = event => {
        event.preventDefault();

        const subscriptionForm = subscriptionFormRef.current;
        if (subscriptionForm) {
            const formData = new FormData(subscriptionForm);
            setSubscribeFormDisabled(true);

            const stripeHandler = window.StripeCheckout.configure({
                key: window.mdn.stripePublicKey,
                locale: 'auto',
                name: 'MDN Web Docs',
                zipCode: true,
                currency: 'usd',
                amount: 500,
                email: '',
                token: function(response) {
                    formData.set('stripe_token', response.id);
                    subscriptionForm.submit();
                },
                closed: function() {
                    if (!formData.get('stripe_token')) {
                        setSubscribeFormDisabled(false);
                    }
                }
            });

            stripeHandler.open();
        }
    };

    return (
        <div className="subscriptions-form">
            <header className="subscriptions-form-header">
                <h2>
                    <Interpolated
                        id={gettext('$5 <perMontSub />')}
                        perMontSub={<sub>{gettext('/mo')}</sub>}
                    />
                </h2>
            </header>
            <form
                ref={subscriptionFormRef}
                name="subscription-form"
                method="post"
                onSubmit={submit}
                disabled={subscribeFormDisabled ? 'disabled' : ''}
            >
                <label className="payment-opt-in">
                    <input
                        type="checkbox"
                        required="required"
                        onClick={toggleButton}
                    />
                    <small>
                        <Interpolated
                            id={gettext(
                                'By clicking this button, I authorize Mozilla to charge this payment method each month, according to the <paymentTermsLink />, until I cancel my subscription.'
                            )}
                            paymentTermsLink={
                                <a
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    href={`/${locale}/payments/`}
                                >
                                    {gettext('Payment Terms')}
                                </a>
                            }
                        />
                    </small>
                </label>
                <input type="hidden" name="stripe_token" />
                <input type="hidden" name="stripe_email" />
                <button
                    type="submit"
                    className="button cta primary"
                    disabled={subscribeButtonEnabled ? '' : 'disabled'}
                >
                    {gettext('Continue')}
                </button>
                <small className="subtext">
                    {gettext('Payments are not tax deductible')}
                </small>
            </form>
        </div>
    );
}
