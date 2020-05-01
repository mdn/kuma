// @flow
import * as React from 'react';
import { useContext, useEffect, useRef, useState } from 'react';

import { getLocale, gettext, Interpolated } from '../../l10n.js';
import GAProvider, {
    CATEGORY_MONTHLY_PAYMENTS,
    gaSendOnNextPage,
} from '../../ga-provider.jsx';
import UserProvider from '../../user-provider.jsx';
import { getCookie } from '../../utils';
import { ErrorComponent } from './errors.jsx';
import useScriptLoading from './useScriptLoading.js';

const SUBSCRIPTION_URL = '/api/v1/subscriptions/';
export const STRIPE_CONTINUE_SESSIONSTORAGE_KEY = 'stripe-form-continue';

/**
 * Returns true if the user has previously started the subscription process, but
 * wasn't authenticated yet
 */
function popStartedUnauthenticated() {
    try {
        const startedUnauthenticated = JSON.parse(
            sessionStorage.getItem(STRIPE_CONTINUE_SESSIONSTORAGE_KEY) ||
                JSON.stringify(false)
        );
        sessionStorage.removeItem(STRIPE_CONTINUE_SESSIONSTORAGE_KEY);
        return startedUnauthenticated;
    } catch (e) {
        // If sessionStorage is not supported, it defaults to false
        return false;
    }
}

/**
 * Remembers, in sessionStorage, that the user started unauthenticated
 */
function setStartedUnauthenticated() {
    try {
        sessionStorage.setItem(
            STRIPE_CONTINUE_SESSIONSTORAGE_KEY,
            JSON.stringify(true)
        );
    } catch (e) {
        // No sessionStorage support
    }
}

export default function SubscriptionForm() {
    const ga = useContext(GAProvider.context);
    const userData = useContext(UserProvider.context);
    const locale = getLocale();

    const [paymentAuthorized, setPaymentAuthorized] = useState(false);
    const [formStep, setFormStep] = useState<
        'initial' | 'stripe_error' | 'stripe' | 'submitting' | 'server_error'
    >('initial');
    const [openStripeModal, setOpenStripeModal] = useState(false);

    const token = useRef(null);
    const startedUnauthenticated = useRef<boolean | null>(null);

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

    useEffect(() => {
        startedUnauthenticated.current = popStartedUnauthenticated();
    }, []);

    /**
     * If you arrived on this page, being anonymous, you'd have to first sign in.
     * Suppose that you do that, we will make sure to send you back to this page
     * with the sessionStorage key set.
     * Basically, if you have that sessionStorage key, it will, for you, check the
     * checkbox and press the "Continue" button.
     */
    useEffect(() => {
        if (
            userData &&
            userData.isAuthenticated &&
            startedUnauthenticated.current
        ) {
            setPaymentAuthorized(true);
            setOpenStripeModal(true);
        }
    }, [userData]);

    useEffect(() => {
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
                    // We're sending two events because it is cumbersome to
                    // aggregate events inside of Analytics
                    // See: https://github.com/mdn/kuma/pull/6877
                    gaSendOnNextPage([
                        {
                            hitType: 'event',
                            eventCategory: CATEGORY_MONTHLY_PAYMENTS,
                            eventAction: 'successful subscription',
                            eventLabel: 'subscription-landing-page',
                        },
                        {
                            hitType: 'event',
                            eventCategory: CATEGORY_MONTHLY_PAYMENTS,
                            eventAction: `successful subscription (${
                                startedUnauthenticated.current
                                    ? 'unauthenticated'
                                    : 'authenticated'
                            })`,
                            eventLabel: 'subscription-landing-page',
                        },
                    ]);
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

        if (stripeLoadingPromise && openStripeModal) {
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
                        setOpenStripeModal(false);
                        setFormStep(token.current ? 'submitting' : 'initial');
                    },
                });
                stripeHandler.open();
            });
        }
    }, [stripeLoadingPromise, openStripeModal, userData, locale]);

    function handleSubmit(event) {
        event.preventDefault();

        // We're sending two events because it is cumbersome to
        // aggregate events inside of Analytics
        // See: https://github.com/mdn/kuma/pull/6877
        ga('send', {
            hitType: 'event',
            eventCategory: CATEGORY_MONTHLY_PAYMENTS,
            eventAction: `subscribe intent (${
                userData && userData.isAuthenticated
                    ? 'authenticated'
                    : 'unauthenticated'
            })`,
            eventLabel: 'subscription-landing-page',
        });
        ga('send', {
            hitType: 'event',
            eventCategory: CATEGORY_MONTHLY_PAYMENTS,
            eventAction: 'subscribe intent',
            eventLabel: 'subscription-landing-page',
        });

        // Not so fast! If you're not authenticated yet, trigger the
        // authentication modal instead.
        if (userData && userData.isAuthenticated) {
            setOpenStripeModal(true);
        } else {
            setStartedUnauthenticated();
            const next = encodeURIComponent(window.location.pathname);
            if (window.mdn && window.mdn.triggerAuthModal) {
                window.mdn.triggerAuthModal(
                    gettext(
                        "Sign in to support MDN. If you haven't already created an account, you will be prompted to do so after signing in."
                    )
                );
            } else {
                // If window.mdn.triggerAuthModal is falsy, it most likely means
                // it deliberately doesn't want this user to use a modal. E.g.
                // certain mobile clients.
                window.location.assign(
                    `/${locale}/users/account/signup-landing?next=${next}`
                );
            }
        }
    }

    let content;
    if (formStep === 'server_error') {
        content = (
            <ErrorComponent
                text={gettext(
                    "An error occurred trying to set up the subscription with Stripe's server. We've recorded the error and will investigate it."
                )}
                onClick={() => setFormStep('initial')}
            />
        );
    } else if (formStep === 'stripe_error') {
        content = (
            <ErrorComponent
                text={gettext(
                    'An error happened trying to load the Stripe integration'
                )}
                onClick={reloadStripe}
            />
        );
    } else {
        content = (
            <form
                method="post"
                onSubmit={handleSubmit}
                data-testid="subscription-form"
            >
                <label className="payment-opt-in">
                    <input
                        type="checkbox"
                        required
                        checked={paymentAuthorized}
                        onChange={(event) => {
                            setPaymentAuthorized(event.target.checked);
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
                <button type="submit" className="button cta primary">
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
                        perMontSub={<span>{gettext('/mo')}</span>}
                    />
                </h2>
            </header>
            {content}
        </div>
    );
}
