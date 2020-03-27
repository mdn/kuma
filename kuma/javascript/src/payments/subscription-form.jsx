// @flow
import * as React from 'react';
import { useContext, useEffect, useRef, useState } from 'react';

import { getLocale, gettext, Interpolated } from '../l10n.js';
import UserProvider from '../user-provider.jsx';
import { getCookie } from '../utils';

const SUBSCRIPTION_URL = '/api/v1/subscriptions';

/**
 * Conditionally loads the script given by the URL and cleans up after itself
 * @returns {(Promise|null)} When it shouldLoad a promise indicating whether
 * the script has successfully loaded
 */
function useConditionalScriptLoad(url, shouldLoad) {
    const [loadingPromise, setLoadingPromise] = useState(null);

    useEffect(() => {
        let script;
        if (shouldLoad && !loadingPromise) {
            setLoadingPromise(
                new Promise(resolve => {
                    script = document.createElement('script');
                    script.onload = () => {
                        resolve();
                    };
                    script.src = url;

                    if (document.head) {
                        document.head.appendChild(script);
                    }
                })
            );
        }
        return () => {
            if (document.head && script) {
                document.head.removeChild(script);
            }
        };
    }, [shouldLoad, loadingPromise, url]);

    return loadingPromise;
}

export default function SubscriptionForm() {
    const locale = getLocale();
    const userData = useContext(UserProvider.context);

    const [isSubmitting, setIsSubmitting] = useState(false);
    const [paymentAuthorized, setPaymentAuthorized] = useState(false);

    const token = useRef(null);

    const stripeLoadingPromise = useConditionalScriptLoad(
        'https://checkout.stripe.com/checkout.js',
        paymentAuthorized
    );

    function togglePaymentAuthorized() {
        const newValue = !paymentAuthorized;
        setPaymentAuthorized(newValue);
    }

    function openStripeModal(event) {
        event.preventDefault();

        setIsSubmitting(true);

        if (!stripeLoadingPromise) {
            console.error('stripe script load was not started');
            return;
        }

        stripeLoadingPromise.then(() => {
            const stripeHandler = window.StripeCheckout.configure({
                key: window.mdn.stripePublicKey,
                locale,
                name: 'MDN Web Docs',
                zipCode: true,
                currency: 'usd',
                amount: 500,
                email: userData ? userData.email : '',
                token(response) {
                    token.current = response.id;
                    createSubscription();
                },
                closed() {
                    if (!token.current) {
                        setIsSubmitting(false);
                    }
                }
            });
            stripeHandler.open();
        });
    }

    function createSubscription() {
        fetch(SUBSCRIPTION_URL, {
            method: 'POST',
            body: JSON.stringify({
                stripe_token: token.current // eslint-disable-line camelcase
            }),
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
            .then(() => {
                window.location = `/${locale}/payments/thank-you/`;
            })
            .catch(e => {
                console.error('error while creating subscription', e);
                alert(
                    gettext(
                        "An error occurred trying to set up the subscription with Stripe's server. We've recorded the error and will investigate it."
                    )
                );
            });
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
                name="subscription-form"
                method="post"
                onSubmit={openStripeModal}
                disabled={isSubmitting}
            >
                <label className="payment-opt-in">
                    <input
                        type="checkbox"
                        required="required"
                        onClick={togglePaymentAuthorized}
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
