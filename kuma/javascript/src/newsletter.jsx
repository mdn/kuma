// @flow
import * as React from 'react';
import { useEffect, useState, useRef, useContext } from 'react';

import GAProvider from './ga-provider.jsx';
import { initAjaxRequest, getAjaxResponse } from './utils.js';
import { getLocale, gettext } from './l10n.js';
import CloseIcon from './icons/close.svg';

/**
 * Returns the Array of error messages as an unordered list element
 * @param {Array} errorsArray - Array of error messages returned from server
 * @returns unordered list element
 */
function getErrorList(errorsArray) {
    const errorList = document.createElement('ul');
    errorList.className = 'errorlist';

    errorsArray.forEach(error => {
        let item = document.createElement('li');
        item.appendChild(document.createTextNode(error));
        errorList.appendChild(item);
    });

    return errorList;
}

/**
 * Checks for the `newsletterHide` entry in `localStorage`. If
 * it is found, the newsletter signup form should not be shown.
 * @returns true or false depending on the presence of `newsletterHide` in `localStorage`
 */
function isHidden() {
    try {
        return localStorage.getItem('newsletterHide') === 'true' ? true : false;
    } catch (error) {
        console.error(
            'Error thrown while getting newsletterHide entry from localStorage: ',
            error
        );
    }
}

/**
 * Called once a user has either successfully subscribed to the
 * newsletter or clicked the close icon. The function stores a
 *`newsletterHide` item in localStorage
 */
function saveNewsletterVisibleState() {
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
    const emailRef = useRef(null);
    const errorsRef = useRef(null);
    const newsletterFormRef = useRef(null);
    const privacyCheckboxRef = useRef(null);

    const ga = useContext(GAProvider.context);

    const locale = getLocale();
    const newsletterType = 'app-dev';
    const newsletterFormat = 'H';
    const newsletterSubscribeURL = 'https://www.mozilla.org/en-US/newsletter/';
    const privacyPolicyURL = 'https://www.mozilla.org/privacy/';

    const [showFormErrors, setShowFormErrors] = useState(false);
    const [showNewsletter, setShowNewsletter] = useState(true);
    const [showNewsletterLang, setShowNewsletterLang] = useState(false);
    const [showPrivacyCheckbox, setShowPrivacyCheckbox] = useState(false);
    const [
        showSuccessfulSubscription,
        setShowSuccessfulSubscription
    ] = useState(false);

    /**
     * Closes the newsletter, sets the visibility state
     * in `localStorage` and sends the relevant event
     * to Google Analytics
     */
    const closeNewsletter = () => {
        setShowNewsletter(false);
        saveNewsletterVisibleState();
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
        let emailInput = emailRef.current;
        let newsletterForm = newsletterFormRef.current;
        let privacyPolicyCheckbox = privacyCheckboxRef.current;

        // if skipXHR
        if (newsletterForm && newsletterForm.dataset['skipXhr']) {
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
        let ajaxRequest = initAjaxRequest('POST', newsletterSubscribeURL, {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-type': 'application/x-www-form-urlencoded'
        });

        let privacy =
            privacyPolicyCheckbox && privacyPolicyCheckbox.checked
                ? '&privacy=true'
                : '';
        let documentLocation = encodeURIComponent(document.location.href);
        let emailInputValue =
            emailInput && emailInput.value
                ? encodeURIComponent(emailInput.value)
                : '';
        let params = `email=${emailInputValue}&newsletters=${newsletterType}${privacy}&fmt=${newsletterFormat}&source_url=${documentLocation}`;

        ajaxRequest.send(params);

        getAjaxResponse(ajaxRequest).then(response => {
            let parsedResponse = JSON.parse(response);
            if (parsedResponse.success !== 'success') {
                let errorsArray = parsedResponse.errors;

                // if there are erros and the array contain at least one item
                if (errorsArray && errorsArray.length) {
                    // show the errors
                    let errorListContainer = errorsRef.current;

                    if (errorListContainer) {
                        let currentErrorList = errorListContainer.querySelector(
                            '.errorlist'
                        );

                        if (currentErrorList) {
                            errorListContainer.removeChild(currentErrorList);
                        }

                        errorListContainer.appendChild(
                            getErrorList(errorsArray)
                        );

                        setShowFormErrors(true);
                    }
                    // if there was an error, but there are no items in the array
                } else if (errorsArray && errorsArray.length === 0) {
                    if (newsletterForm) {
                        // set the skip-xhr data attribute on the form
                        newsletterForm.dataset.skipXhr = 'true';
                        // and submit again for diagnoses on the server
                        newsletterForm.submit();
                    }
                } else {
                    setShowNewsletter(false);
                    saveNewsletterVisibleState();
                    setShowSuccessfulSubscription(true);
                    ga('send', {
                        hitType: 'event',
                        eventCategory: 'newsletter',
                        eventAction: 'progression',
                        eventLabel: 'complete'
                    });
                }
            }
        });
    };

    /* If this is not en-US, show message informing the user
       that newsletter is only acailable in English */
    if (locale !== 'en-US') {
        setShowNewsletterLang(true);
    }

    useEffect(() => {
        // if `isHidden` is true
        if (isHidden()) {
            // do not show the newsletter
            setShowNewsletter(false);
        }
    }, []);

    return (
        <section className="newsletter-container">
            <div
                id="newsletter-form-container"
                className={showNewsletter ? 'newsletter' : 'hidden'}
                aria-hidden={showNewsletter ? false : true}
            >
                <form
                    ref={newsletterFormRef}
                    id="newsletter-form"
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
                    <legend className="newsletter-fields">
                        <input
                            type="hidden"
                            id="fmt"
                            name="fmt"
                            value={newsletterType}
                        />
                        <input
                            type="hidden"
                            id="newsletterNewslettersInput"
                            name="newsletters"
                            value={newsletterFormat}
                        />
                        <div
                            ref={errorsRef}
                            id="newsletter-errors"
                            className={
                                showFormErrors ? 'newsletter-errors' : 'hidden'
                            }
                            aria-hidden={showFormErrors ? true : false}
                        />

                        <div
                            id="newsletterEmail"
                            className="form-group newsletter-group-email"
                        >
                            <label
                                htmlFor="newsletterEmailInput"
                                className="form-label offscreen"
                            >
                                {gettext('E-mail')}
                            </label>
                            <input
                                ref={emailRef}
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
                                ref={privacyCheckboxRef}
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
                        <div
                            id="newsletterSubmit"
                            className="newsletter-group-submit"
                        >
                            <button
                                onClick={submit}
                                id="newsletter-submit"
                                type="submit"
                                className="button neutral newsletter-submit"
                            >
                                {gettext('Sign up now')}
                            </button>
                        </div>
                    </legend>
                </form>
                <button
                    onClick={closeNewsletter}
                    id="newsletter-hide"
                    type="button"
                    className="only-icon newsletter-hide"
                    aria-controls="newsletter-form-container"
                >
                    <span>{gettext('Hide Newsletter Sign-up')}</span>
                    <CloseIcon />
                </button>
            </div>
            <div
                id="newsletter-thanks"
                className={
                    showSuccessfulSubscription ? 'newsletter-thanks' : 'hidden'
                }
                aria-hidden={showSuccessfulSubscription ? false : true}
            >
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
