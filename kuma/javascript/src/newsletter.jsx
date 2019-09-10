// @flow
import * as React from 'react';
import { useEffect, useState, useRef, useContext } from 'react';

import GAProvider from './ga-provider.jsx';
import { getLocale, gettext } from './l10n.js';
import CloseIcon from './icons/close.svg';

/**
 * Called once a user has either successfully subscribed to the
 * newsletter or clicked the close icon. The function stores a
 *`newsletterHide` item in localStorage
 */
function permanentlyHideNewsletter() {
    try {
        localStorage.setItem('newsletterHide', 'true');
    } catch (error) {
        console.error(
            'Error thrown while setting newsletterHide entry in localStorage: ',
            error
        );
    }
}

export default function Newsletter() {
    const newsletterFormRef = useRef(null);

    const ga = useContext(GAProvider.context);

    const locale = getLocale();
    const newsletterType = 'app-dev';
    const newsletterFormat = 'H';
    const newsletterSubscribeURL = 'https://www.mozilla.org/en-US/newsletter/';
    const privacyPolicyURL = 'https://www.mozilla.org/privacy/';

    const [errors, setError] = useState([]);
    const [showNewsletter, setShowNewsletter] = useState(true);
    const [showPrivacyCheckbox, setShowPrivacyCheckbox] = useState(false);
    const [
        showSuccessfulSubscription,
        setShowSuccessfulSubscription
    ] = useState(false);

    /* If this is not en-US, show message informing the user
       that newsletter is only available in English */
    const showNewsletterLang = locale !== 'en-US';
    const hasErrors = errors.length > 0;

    /**
     * Closes the newsletter, sets the visibility state
     * in `localStorage` and sends the relevant event
     * to Google Analytics
     */
    const closeNewsletter = () => {
        setShowNewsletter(false);
        permanentlyHideNewsletter();
        ga('send', {
            hitType: 'event',
            eventCategory: 'newsletter',
            eventAction: 'prompt',
            eventLabel: 'hide'
        });
    };

    /**
     * Shows the privacy checkbox when the email
     * input field receives focus.
     */
    const inputFocusHandler = () => {
        setShowPrivacyCheckbox(true);
        ga('send', {
            hitType: 'event',
            eventCategory: 'newsletter',
            eventAction: 'prompt',
            eventLabel: 'focus'
        });
    };

    /**
     * Attempts to subscribe the user to the `app-dev` newsletter. If an
     * error occurs when attempting to subscribe the user, it will either:
     * 1. Present the errors returned to the user
     * 2. If no reason was provided, it will abandon the XHR request and
     * send the user directly to the subscription page on www.mozilla.org
     *
     * On successful subscription, a thank you message will be shown to the
     * user, and the visibility state will be stored in `localStorage`
     * @param {Object} event - The MouseEvent object
     */
    const submit = event => {
        let newsletterForm = newsletterFormRef.current;

        if (!newsletterForm) {
            return;
        }

        // if skipFetch
        if (newsletterForm.dataset['skipFetch']) {
            /*
             * An error occured while attempting to subscribe
             * the user via Ajax, but no specific error was provided. We
             * therefore just send the user directly to the Mozorg
             * newsletter subscription page and log the occurence
             */
            ga('send', {
                hitType: 'event',
                eventCategory: 'newsletter',
                eventAction: 'progression',
                eventLabel: 'error-forward'
            });
            return true;
        }

        event.preventDefault();
        let params = new URLSearchParams(
            new FormData(newsletterForm)
        ).toString();
        fetch(newsletterSubscribeURL, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-type': 'application/x-www-form-urlencoded'
            },
            body: params
        })
            .then(response => response.json())
            .then(({ success, errors }) => {
                if (success) {
                    permanentlyHideNewsletter();
                    setShowSuccessfulSubscription(true);
                    ga('send', {
                        hitType: 'event',
                        eventCategory: 'newsletter',
                        eventAction: 'progression',
                        eventLabel: 'complete'
                    });
                    return;
                }

                if (errors && errors.length) {
                    setError(errors);
                    // if there was an error, but there are no items in the array
                } else if (errors && errors.length === 0) {
                    // set the skip-fetch data attribute on the form
                    newsletterForm.dataset.skipFetch = 'true';
                    // and submit again for diagnoses on the server
                    newsletterForm.submit();
                }
            })
            .catch(e => {
                setError([e.toString()]);
            });
    };

    useEffect(() => {
        // if `newsletterHide` is set
        if (localStorage.getItem('newsletterHide') === 'true') {
            // do not show the newsletter
            setShowNewsletter(false);
        }
    }, []);

    if (!showNewsletter) {
        return null;
    }

    if (showSuccessfulSubscription) {
        return (
            <section className="newsletter-container">
                <div className="newsletter-thanks">
                    <h2>
                        {gettext(
                            'Thanks! Please check your inbox to confirm your subscription.'
                        )}
                    </h2>
                    <p>
                        {gettext(
                            'If you haven’t previously confirmed a subscription to a Mozilla - related newsletter you may have to do so. Please check your inbox or your spam filter for an email from us.'
                        )}
                    </p>
                </div>
            </section>
        );
    }

    return (
        <section className="newsletter-container">
            <div id="newsletter-form-container" className="newsletter">
                <form
                    ref={newsletterFormRef}
                    className="newsletter-form nodisable"
                    name="newsletter-form"
                    action={newsletterSubscribeURL}
                    method="post"
                >
                    <section className="newsletter-head">
                        <h2 className="newsletter-teaser">
                            {gettext('Learn the best of web development')}
                        </h2>
                        <p className="newsletter-description">
                            {gettext(
                                'Get the latest and greatest from MDN delivered straight to your inbox.'
                            )}
                        </p>
                        <p
                            className={
                                showNewsletterLang
                                    ? 'newsletter-lang'
                                    : 'hidden'
                            }
                            aria-hidden={showNewsletterLang ? false : true}
                        >
                            {gettext(
                                'The newsletter is offered in English only at the moment.'
                            )}
                        </p>
                    </section>
                    <fieldset className="newsletter-fields">
                        <input
                            type="hidden"
                            name="fmt"
                            value={newsletterFormat}
                        />
                        <input
                            type="hidden"
                            name="newsletters"
                            value={newsletterType}
                        />
                        {hasErrors && (
                            <div className="newsletter-errors">
                                <ul className="errorlist">
                                    {errors.map((error, index) => (
                                        <li key={index + error}>{error}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        <div className="form-group newsletter-group-email">
                            <label
                                htmlFor="newsletter-email-input"
                                className="form-label offscreen"
                            >
                                {gettext('E-mail')}
                            </label>
                            <input
                                onFocus={inputFocusHandler}
                                type="email"
                                id="newsletter-email-input"
                                name="email"
                                className="form-input newsletter-input-email"
                                placeholder={gettext('you@example.com')}
                                required
                            />
                        </div>

                        <div
                            id="newsletter-privacy"
                            className={
                                showPrivacyCheckbox
                                    ? 'form-group form-group-agree newsletter-group-privacy'
                                    : 'hidden'
                            }
                            aria-hidden={showPrivacyCheckbox ? false : true}
                        >
                            <input
                                type="checkbox"
                                id="newsletter-privacy-input"
                                name="privacy"
                                required
                            />
                            <label htmlFor="newsletter-privacy-input">
                                {gettext(
                                    'I’m okay with Mozilla handling my info as explained in this '
                                )}
                                <a href={privacyPolicyURL}>
                                    {gettext('Privacy Policy')}
                                </a>
                                .
                            </label>
                        </div>
                        <div className="newsletter-group-submit">
                            <button
                                onClick={submit}
                                id="newsletter-submit"
                                type="submit"
                                className="button neutral newsletter-submit"
                            >
                                {gettext('Sign up now')}
                            </button>
                        </div>
                    </fieldset>
                </form>
                <button
                    onClick={closeNewsletter}
                    type="button"
                    className="only-icon newsletter-hide"
                    aria-controls="newsletter-form-container"
                >
                    <span>{gettext('Hide Newsletter Sign-up')}</span>
                    <CloseIcon />
                </button>
            </div>
        </section>
    );
}
