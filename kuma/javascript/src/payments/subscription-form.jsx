// @flow
import * as React from 'react';
import { useContext, useEffect, useRef, useState } from 'react';

import { getLocale, gettext, Interpolated } from '../l10n.js';
import UserProvider from '../user-provider.jsx';
import { getCookie } from '../utils';

const SUBSCRIPTION_URL = '/api/v1/subscriptions';

/**
 * Loads the script given by the URL and cleans up after itself
 * @returns {(null | Promise)} Indicating whether the script has successfully loaded
 */
function useScriptLoading(url) {
    const [loadingPromise, setLoadingPromise] = useState<null | Promise<void>>(
        null
    );
    useEffect(() => {
        let script;
        if (!loadingPromise) {
            script = document.createElement('script');
            setLoadingPromise(
                new Promise((resolve, reject) => {
                    script.onload = resolve;
                    script.onerror = reject;
                })
            );
            script.src = url;

            if (document.head) {
                document.head.appendChild(script);
            }
        }
        return () => {
            if (document.head && script) {
                document.head.removeChild(script);
            }
        };
    }, [loadingPromise, url]);

    return [loadingPromise, () => setLoadingPromise(null)];
}

export default function SubscriptionForm() {
    const locale = getLocale();
    const userData = useContext(UserProvider.context);

    const [paymentAuthorized, setPaymentAuthorized] = useState(false);
    const [formStep, setFormStep] = useState<
        'initial' | 'stripe_error' | 'stripe' | 'submitting' | 'server_error'
    >('initial');

    const token = useRef(null);

    const [stripeLoadingPromise, reloadStripe] = useScriptLoading(
        'https://checkout.stripe.com/checkout.js'
    );

    useEffect(() => {
        if (!stripeLoadingPromise) {
            return;
        }
        stripeLoadingPromise
            .then(() => {
                if (formStep === 'stripe_error') {
                    setFormStep('initial');
                }
            })
            .catch(() => {
                setFormStep('stripe_error');
            });
    }, [formStep, stripeLoadingPromise]);

    function openStripeModal() {
        if (!stripeLoadingPromise) {
            return;
        }
        setFormStep('stripe');
        stripeLoadingPromise.then(() => {
            const stripeHandler = window.StripeCheckout.configure({
                key: window.mdn.stripePublicKey,
                locale,
                name: 'MDN Web Docs',
                zipCode: true,
                currency: 'usd',
                amount: 500,
                email: userData ? userData.email : '',
                // token is only called if Stripe was able to successfully
                // create a token from the entered info
                token(response) {
                    token.current = response.id;
                    createSubscription();
                },
                closed() {
                    setFormStep(token.current ? 'submitting' : 'initial');
                },
            });
            stripeHandler.open();
        });
    }

    function createSubscription() {
        fetch(SUBSCRIPTION_URL, {
            method: 'POST',
            body: JSON.stringify({
                stripe_token: token.current, // eslint-disable-line camelcase
            }),
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
        }).then((response) => {
            if (response.ok) {
                window.location = `/${locale}/payments/thank-you/`;
            } else {
                console.error(
                    'error while creating subscription',
                    response.statusText
                );
                setFormStep('server_error');
            }
        });
    }

    let content;
    if (formStep === 'server_error') {
        content = (
            <section className="error">
                <h2>{gettext('Sorry!')}</h2>
                <p>
                    {gettext(
                        "An error occurred trying to set up the subscription with Stripe's server. We've recorded the error and will investigate it."
                    )}
                </p>
                <button
                    type="button"
                    className="button cta primary"
                    onClick={() => setFormStep('initial')}
                >
                    {gettext('Try again')}
                </button>
            </section>
        );
    } else if (formStep === 'stripe_error') {
        content = (
            <section className="error">
                <h2>{gettext('Sorry!')}</h2>
                <p>
                    {gettext(
                        'An error happened trying to load the Stripe integration'
                    )}
                </p>
                <button
                    type="button"
                    className="button cta primary"
                    onClick={reloadStripe}
                >
                    {gettext('Try again')}
                </button>
            </section>
        );
    } else {
        content = (
            <form
                method="post"
                onSubmit={(event) => {
                    event.preventDefault();
                    openStripeModal();
                }}
                disabled={formStep !== 'initial'}
            >
                <label className="payment-opt-in">
                    <input
                        type="checkbox"
                        required="required"
                        value={paymentAuthorized}
                        onClick={() => {
                            setPaymentAuthorized(!paymentAuthorized);
                        }}
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
                    disabled={!paymentAuthorized || formStep !== 'initial'}
                >
                    {gettext(
                        formStep === 'submitting' ? 'Submitting...' : 'Continue'
                    )}
                </button>
                <small className="subtext">
                    {gettext('Payments are not tax deductible')}
                </small>
            </form>
        );
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
            {content}
        </div>
    );
}
