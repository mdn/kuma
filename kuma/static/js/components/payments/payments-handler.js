(function(doc, win, $) {
    'use strict';

    // Quit here if contributions are disabled.
    if (!win.mdn.contributions) {
        return;
    }

    var form = $('#contribute-form');
    // Inputs.
    var emailField = form.find('#id_email');
    var nameField = form.find('#id_name');
    var recurringConfirmationCheckbox = form.find('#id_accept_checkbox');
    var customAmountInput = form.find('#id_donation_amount');
    var defaultAmount = customAmountInput.val()
        ? customAmountInput
        : form.find('input[type=\'radio\']:checked');
    var amountRadio = form.find('input[name=donation_choices]');
    // Hidden fields.
    var stripePublicKey = form.find('#id_stripe_public_key');
    var stripeToken = form.find('#id_stripe_token');
    var stripeHandler = null;
    // Other.
    var formButton = form.find('#stripe_submit');
    var formErrorMessage = form.find('#contribution-error-message');
    var amountToUpdate = form.find('[data-dynamic-amount]');

    var currrentPaymentForm = form.attr('data-payment-type');
    var requestUserLogin = doc.getElementById('login-popover');
    var githubRedirectButton = doc.getElementById('github_redirect_payment');

    var hasPaymentSwitch = Boolean(
        doc.getElementById('dynamic-payment-switch')
    );
    var paymentTypeSwitch = doc.querySelectorAll(
        'input[type=radio][name="payment_selector"]'
    );
    var recurringConfirmationContainer = doc.getElementById(
        'recurring-confirmation-container'
    );

    var selectedAmount = 0;
    var submitted = false;

    var amountRadioInputs = doc.querySelectorAll(
        'input[data-dynamic-choice-selector]'
    );
    var paymentChoices =
        typeof window.payments !== 'undefined' &&
        'paymentChoices' in window.payments
            ? win.payments.paymentChoices
            : null;

    /* Following recurring payments flow the user may be redirected back to the form to submit payment.
       We're tracking this with a localstorage item as this should percist across various pages. */
    var triggerAnalyticEvents = !hasUserBeenRedirected();

    /**
     * Check storage to see if user is being redirected
     * @returns {boolean}
     */
    function hasUserBeenRedirected() {
        if (!win.mdn.features.localStorage) {
            return false;
        }

        return Boolean(
            localStorage.getItem('userAuthenticationOnFormSubmission')
        );
    }

    /**
     * Initialise the stripeCheckout handler.
     */
    function initStripeHandler() {
        var stripeOptions = {
            key: stripePublicKey.val(),
            locale: 'en',
            name: 'MDN Web Docs',
            description: 'One-time donation',
            source: function(token) {
                submitted = true;
                stripeToken.val(token.id);
                /* Multiply selection to get value in pennies.
                Following Stripe's convention so this is comparable with analytics. */
                sessionStorage.setItem(
                    'submissionDetails',
                    JSON.stringify({
                        amount: selectedAmount * 100,
                        page: isPopoverBanner ? 'Banner' : 'FAQ'
                    })
                );
                form.submit();
            }
        };
        return win.StripeCheckout.configure(stripeOptions);
    }

    // Ensure we only show the form if js is enabled
    if (win.StripeCheckout) {
        $('#mdn-payments').removeClass('hidden');
    }

    var isPopoverBanner = $('.contribution-banner').hasClass(
        'contribution-popover'
    );

    /* If `isPopoverBanner` is false then this is the contribute page.
     Init the handler immediately */
    if (!isPopoverBanner && win.StripeCheckout) {
        stripeHandler = initStripeHandler();
    }

    if (isPopoverBanner) {
        var popoverBanner = $('.contribution-banner');
    }

    // Set initial form selected amount state
    if (defaultAmount.get(0)) {
        onAmountSelect({ target: defaultAmount.get(0) }, true);
    }

    // Set errors.
    form.find('.errorlist')
        .prev()
        .addClass('error');

    /**
     * Emits an event for recurring payments
     * @param {Object} event - The event to be emitted
     * @param {string} event.action - The event's action name
     * @param {number} [event.value] - the event's numerical value
     * @param {boolean} [storeUserForLaterEvents] - store user auth level for later analytic events
     */
    function triggerRecurringPaymentEvent(event, storeUserForLaterEvents) {
        // To preserve conversion rate % we should not emit events if localStorage is disabled.
        if (!triggerAnalyticEvents || !win.mdn.features.localStorage) {
            return;
        }

        //  We're duplicating event semantics due to an Analytics issue with the event label
        mdn.analytics.trackEvent({
            category: 'Recurring payments',
            action: event.action,
            label: win.payments.isAuthenticated ? 'authenticated' : 'anonymous',
            value: event.value
        });
        mdn.analytics.trackEvent({
            category: 'Recurring payments v2',
            action:
                event.action + ' - ' + win.payments.isAuthenticated
                    ? 'authenticated'
                    : 'anonymous',
            label: win.payments.isAuthenticated ? 'authenticated' : 'anonymous',
            value: event.value
        });

        /* Save the user authentication level so that we can track conversion rates of
           authenticated vs anonymous users at a later stage in the payment flow. */
        if (storeUserForLaterEvents) {
            var item = win.payments.isAuthenticated
                ? 'authenticated'
                : 'anonymous';
            localStorage.setItem('userAuthenticationOnFormSubmission', item);
            triggerAnalyticEvents = false;
        }
    }

    /**
     * Emits an event for recurring payments
     * @param {Object} event - The event to be emitted
     * @param {string} event.action - The event's action name
     * @param {string} [event.label] - The event's label name
     * @param {number} [event.value] - the event's numerical value
     */
    function triggerOneTimePaymentEvent(event) {
        if (!triggerAnalyticEvents) {
            return;
        }

        mdn.analytics.trackEvent({
            category: 'payments',
            action: event.action,
            label: event.label,
            value: event.value
        });
    }

    /**
     * Handles adjusting amount.
     * @param {jQuery.Event} event Event object.
     * @param {boolean} automatedSelection  - stops validation and events being sent
     */
    function onAmountSelect(event, automatedSelection) {
        form.find('label.active').removeClass('active');

        clearFieldError(customAmountInput);

        // Validate against minimum value.
        if (
            !automatedSelection &&
            (parseInt(event.target.value) < 1 || isNaN(event.target.value))
        ) {
            defaultAmount.prop('checked', true);
            setFieldError(customAmountInput);
        }

        // Reset custom amount input when selecting radio.
        if (event.target.type === 'radio') {
            customAmountInput.val('');

            if (!automatedSelection) {
                // Send GA Event.
                triggerOneTimePaymentEvent({
                    action: 'banner',
                    label: 'Amount radio selected',
                    value: (selectedAmount * 100).toFixed(0)
                });
            }

            $(event.target)
                .parent()
                .addClass('active');
        } else {
            // Reset radio when selecting custom amount.
            form.find('input[type=\'radio\']:checked').prop('checked', false);
        }

        selectedAmount = mdn.paymentsHandlerUtils.getSelectedAmount(
            event.target.value
        );
        var newValue = mdn.paymentsHandlerUtils.addCurrencyPrefix(
            selectedAmount
        );
        amountToUpdate.html(newValue);

        // Explicitly add `/month` on the payment button for the banner
        newValue +=
            currrentPaymentForm === 'recurring' &&
            newValue !== '' &&
            isPopoverBanner
                ? '/month'
                : '';
        amountToUpdate[1].textContent = newValue;
    }

    /**
     * Set the error message for any required field.
     * @param {Element} field Field element.
     */
    function setFieldError(field) {
        $(field).addClass('error');
        $(field)
            .next('.errorlist')
            .remove();
        var error = $(field).attr('data-error-message');
        $('<ul class="errorlist"><li>' + error + '</li></ul>').insertAfter(
            $(field)
        );
    }

    /**
     * Clear the error message for any required field.
     * @param {Element} field Field element.
     */
    function clearFieldError(field) {
        $(field).removeClass('error');
        $(field)
            .next('.errorlist')
            .remove();
    }

    /**
     * Checks field validity and sets any errors if required.
     * @param {jQuery.Event} event Event object.
     */
    function onChange(event) {
        var field = $(event.target)[0];
        field.value = field.value.trim();
        if (field.checkValidity()) {
            clearFieldError(field);
        } else {
            setFieldError(field);
        }
    }

    /**
     * Handles the form submit. Checks for field validity using built in browser
     * checkValidity functionality and then attempts to open the Stripe modal if
     * the form is valid.
     */
    function onSubmit() {
        // FE form validation.
        var valid = form[0].checkValidity();

        if (!valid || (selectedAmount < 1 || isNaN(selectedAmount))) {
            if (emailField[0].checkValidity()) {
                clearFieldError(emailField[0]);
            } else {
                setFieldError(emailField[0]);
            }

            if (nameField[0].checkValidity()) {
                clearFieldError(nameField[0]);
            } else {
                setFieldError(nameField[0]);
            }

            if (selectedAmount >= 1) {
                clearFieldError(customAmountInput);
            } else {
                setFieldError(customAmountInput);
            }

            if (recurringConfirmationCheckbox[0].checkValidity()) {
                clearFieldError(recurringConfirmationCheckbox[0]);
            } else if (currrentPaymentForm === 'recurring') {
                setFieldError(recurringConfirmationCheckbox[0]);
            }

            return;
        }

        // Send GA Event.
        currrentPaymentForm === 'recurring'
            ? triggerRecurringPaymentEvent(
                {
                    action: 'Form completed',
                    value: (selectedAmount * 100).toFixed(0)
                },
                true
            )
            : triggerOneTimePaymentEvent({
                action: 'submission',
                label: isPopoverBanner ? 'On pop over' : 'On FAQ page',
                value: (selectedAmount * 100).toFixed(0)
            });

        if (requestUserLogin && currrentPaymentForm === 'recurring') {
            requestUserLogin.classList.remove('hidden');
            form.get(0).classList.add('hidden');
            return;
        }

        if (stripeHandler !== null) {
            // On success open Stripe Checkout modal.
            stripeHandler.open({
                image:
                    'https://avatars1.githubusercontent.com/u/7565578?s=280&v=4',
                name: 'MDN Web Docs',
                description: 'Contribute to MDN Web Docs',
                zipCode: true,
                allowRememberMe: false,
                panelLabel:
                    currrentPaymentForm === 'recurring'
                        ? 'Pay {{amount}}/month'
                        : 'Pay',
                amount: parseInt((selectedAmount * 100).toFixed(0)),
                email: $(emailField).val(),
                closed: function() {
                    // Send GA Event.
                    if (!submitted) {
                        triggerOneTimePaymentEvent({
                            action: 'submission',
                            label: 'canceled'
                        });
                    }
                    form.removeClass('disabled');
                }
            });
        }
    }

    /**
     * Handles the form button click. This will either attempt to submit the form
     * or will expand the popover depending on the current state of the popover.
     */
    function onFormButtonClick() {
        // Calculate the role of the submit button
        if (isPopoverBanner && popoverBanner.hasClass('is-collapsed')) {
            expandPopover();
        } else {
            onSubmit();
        }
    }

    /**
     * Gets and executes stripe's checkout.js script to be used when submitting
     * also handles errors when getting the resource
     */
    function getStripeCheckoutScript() {
        if (stripeHandler) {
            return;
        }

        $.ajax({
            url: 'https://checkout.stripe.com/checkout.js',
            dataType: 'script',
            cache: true
        })
            .done(function() {
                // Init stripeCheckout handler.
                stripeHandler = initStripeHandler();
            })
            .fail(function(error) {
                console.error('Failed to load stripe checkout library', error);
                toggleScriptError();
            });
    }

    /**
     * Displays a visual error if we cannot load the checkout script
     * also disables the submission button
     */
    function toggleScriptError() {
        formButton.attr('disabled')
            ? formButton.removeAttr('disabled')
            : formButton.attr('disabled', 'true');

        formErrorMessage.toggle();
    }

    /**
     * Expands the popover to show the full contents.
     */
    function expandPopover() {
        getStripeCheckoutScript();
        var secondaryHeader = popoverBanner[0].querySelector('h4');

        popoverBanner.addClass('expanded is-expanding');
        popoverBanner.removeClass('is-collapsed');

        popoverBanner.on('transitionend', function() {
            popoverBanner.removeClass('is-expanding');
            popoverBanner.attr('aria-expanded', true);

            // move focus to the secondary header text
            secondaryHeader.focus();

            // remove the event listener
            popoverBanner.off('transitionend');
        });

        currrentPaymentForm === 'recurring'
            ? triggerRecurringPaymentEvent({
                action: 'banner expanded'
            })
            : triggerOneTimePaymentEvent({
                action: 'banner',
                label: 'expand'
            });
    }

    /**
     * Builds correct URL param and directs to GitHub for authentication.
     * @param {jQuery.Event} event Event object.
     */
    function redirectUserToLogin(event) {
        event.preventDefault();
        var gitHubLink = $(this).attr('href');
        var gitHubNext = $(this).data('next');
        var getFormFields = form.serialize();
        gitHubLink +=
            '&next=' + gitHubNext + '?' + encodeURIComponent(getFormFields);
        window.location.href = encodeURI(gitHubLink);
    }

    // Register event handlers and set things up.
    if (requestUserLogin) {
        $(githubRedirectButton).on('click', redirectUserToLogin);
    }
    formButton.click(onFormButtonClick);
    amountRadio.change(onAmountSelect);
    customAmountInput.on('input', onAmountSelect);
    emailField.blur(onChange);
    nameField.blur(onChange);
    customAmountInput.blur(function(event) {
        var value = parseFloat(event.target.value);
        if (!isNaN(value) && value >= 1) {
            this.value = selectedAmount;
            // Send GA Event.
            triggerOneTimePaymentEvent({
                action: 'banner',
                label: 'custom amount',
                value: (value * 100).toFixed(0)
            });
        } else {
            triggerOneTimePaymentEvent({
                action: 'banner',
                label: 'Invalid amount selected'
            });
        }
    });

    // Clear validation for checkbox confirmation
    if (currrentPaymentForm === 'recurring') {
        recurringConfirmationCheckbox.change(function() {
            clearFieldError(recurringConfirmationCheckbox[0]);
        });
    }

    /**
     * Runs when the payment switch changes
     * Toggles the payment type between one-time or recurring payments
     * Updates the form action and method to post to the correct view
     * Updated the visual styling between one-time and recurring
     * Updates the state of the form
     */
    function switchPaymentTypeHandler() {
        var action = form.get(0).getAttribute('action');
        var checkedInput = null;
        customAmountInput.get(0).value = '';
        selectedAmount = 0;

        if (this.value === 'one_time' && currrentPaymentForm === 'recurring') {
            // Switch to one-time payment form only if we're not on the one-time payment form already.
            currrentPaymentForm = 'one_time';

            // Ensure we show the form and don't request login
            if (requestUserLogin) {
                requestUserLogin.classList.add('hidden');
                form.get(0).classList.remove('hidden');
            }

            // Hide the checkbox and mark as not required
            recurringConfirmationCheckbox.get(0).removeAttribute('required');
            recurringConfirmationContainer.classList.add('hidden');

            // Change the form action to submit to the one-time payment view
            action = form.get(0).getAttribute('data-one-time-action');
            [].forEach.call(amountRadioInputs, function(radio, i) {
                radio.setAttribute('value', paymentChoices.oneTime[i]);
                radio.nextSibling.nodeValue = '$' + paymentChoices.oneTime[i];
            });

            // Visually update the form
            form.get(0).classList.remove('recurring-form');
            popoverBanner.get(0).classList.add('expanded');
        } else if (
            this.value === 'recurring' &&
            currrentPaymentForm === 'one_time'
        ) {
            // Switch to recurring payment form only if we're not on the recurring payment form already.
            currrentPaymentForm = 'recurring';

            // Show the confirmation checkbox and mark as required
            recurringConfirmationContainer.classList.remove('hidden');
            recurringConfirmationCheckbox.get(0).setAttribute('required', '');

            // Change the form action to submit to the recurring subscription view
            action = form.get(0).getAttribute('data-recurring-action');
            [].forEach.call(amountRadioInputs, function(radio, i) {
                radio.setAttribute('value', paymentChoices.recurring[i]);
                radio.nextSibling.nodeValue =
                    '$' + paymentChoices.recurring[i] + '/mo';
            });

            // Identify form as recurring
            form.get(0).classList.add('recurring-form');
        }

        // Update the form action
        form.get(0).setAttribute('action', action);

        // Ensure the new amount is reflected
        checkedInput = form.find('input[type=\'radio\']:checked')[0];
        if (checkedInput) {
            onAmountSelect({ target: { value: NaN } }, true);
        } else if (customAmountInput.get(0).value) {
            onAmountSelect({ target: customAmountInput.get(0) });
        }
    }

    // Init the popover banner for recurring payments
    if (hasPaymentSwitch && isPopoverBanner) {
        [].forEach.call(paymentTypeSwitch, function(radio) {
            radio.addEventListener('change', switchPaymentTypeHandler);
        });

        // Force options for popover
        if (currrentPaymentForm === 'recurring') {
            [].forEach.call(amountRadioInputs, function(radio, i) {
                radio.setAttribute('value', paymentChoices.recurring[i]);
                radio.nextSibling.nodeValue =
                    '$' + paymentChoices.recurring[i] + '/mo';
            });

            // Force required checkbox if recurring payment form
            recurringConfirmationCheckbox.get(0).setAttribute('required', '');

            // Ensure the new amount is reflected
            var checkedInput = form.find('input[type=\'radio\']:checked')[0];
            if (checkedInput) {
                onAmountSelect({ target: checkedInput }, true);
            }
        }
    }

    // Send to GA if popover is displayed.
    if (popoverBanner && popoverBanner.is(':visible')) {
        currrentPaymentForm === 'recurring'
            ? triggerRecurringPaymentEvent({
                action: 'banner shown'
            })
            : triggerOneTimePaymentEvent({
                action: 'banner',
                label: 'shown'
            });
    } else if (!popoverBanner && currrentPaymentForm === 'recurring') {
        triggerRecurringPaymentEvent({
            action: 'banner shown on FAQ'
        });
    }
})(document, window, jQuery);
