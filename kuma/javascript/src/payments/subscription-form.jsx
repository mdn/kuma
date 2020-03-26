// @flow
import * as React from 'react';
import { useContext, useEffect, useRef, useState } from 'react';

import { getLocale, gettext, Interpolated } from '../l10n.js';
import UserProvider from '../user-provider.jsx';

export default function SubscriptionForm() {
    const userData = useContext(UserProvider.context);
    const locale = getLocale();

    const subscriptionFormRef = useRef(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [paymentAuthorized, setPaymentAuthorized] = useState(false);

    const toggleButton = event => {
        setPaymentAuthorized(event.target.checked);
    };

    const STRIPE_CONTINUE_SESSIONSTORAGE_KEY = 'strip-form-continue';

    /**
     * If you arrived on this page, being anonymous, you'd have to first sign in.
     * Suppose that you do that, we will make sure to send you back to this page
     * with the '#continuestripe' hash.
     * Basically, if this is your location hash, it will, for you, check the
     * checkbox and press the "Continue" button.
     */
    useEffect(() => {
        if (userData.isAuthenticated) {
            let autoTriggerStripe = false;
            try {
                autoTriggerStripe = JSON.parse(
                    sessionStorage.getItem(
                        STRIPE_CONTINUE_SESSIONSTORAGE_KEY
                    ) || 'false'
                );
            } catch (e) {
                // If sessionStorage is not supported, they'll have to manually click
                // the Continue button again.
            }
            if (autoTriggerStripe) {
                const subscriptionForm = subscriptionFormRef.current;
                if (subscriptionForm) {
                    setPaymentAuthorized(true);
                    initStripeForm();
                }
            }
        }
    }, [userData.isAuthenticated]);

    /**
     * Opens Stripe modal allowing a user to complete their subscription.
     * @param {Object} event - The form submit event
     */
    const submit = event => {
        event.preventDefault();

        if (!userData.isAuthenticated) {
            try {
                sessionStorage.setItem(
                    STRIPE_CONTINUE_SESSIONSTORAGE_KEY,
                    JSON.stringify(true)
                );
            } catch (e) {
                // No sessionStorage, no remembering to trigger opening the Stripe
                // form automatically next time.
            }
            const next = encodeURIComponent(window.location.pathname);
            // XXX Waiting for window.mdn.triggerAuthModal
            // https://github.com/mdn/kuma/pull/6749
            if (window.mdn && window.mdn.triggerAuthModal) {
                window.mdn.triggerAuthModal();
            } else {
                window.location.href = `/${locale}/users/account/signup-landing?next=${next}`;
            }
            return;
        }

        initStripeForm();
    };

    function initStripeForm() {
        const subscriptionForm = subscriptionFormRef.current;
        const formData = new FormData(subscriptionForm);
        setIsSubmitting(true);

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
                    setIsSubmitting(false);
                }
            }
        });

        stripeHandler.open();
    }

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
                disabled={isSubmitting}
            >
                <label className="payment-opt-in">
                    <input
                        type="checkbox"
                        required="required"
                        checked={paymentAuthorized}
                        onChange={toggleButton}
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
                                    href={`/${locale}/payments/terms/`}
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
                    disabled={!paymentAuthorized}
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
