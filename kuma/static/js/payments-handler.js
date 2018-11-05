(function(doc, win, $) {
    'use strict';

    // Quit here if contributions are disabled.
    if (!win.mdn.contributions) {
        return;
    }

    /**
     * Expiration date for how long the contributions modal should be hidden for
     * after it's been disabled by clicking the close button.
     * @const
     */
    var CONTRIBUTIONS_DISABLED_EXPIRATION =  5 * 24 * 60 * 60 * 1000; // 5 days.

    /**
     * Runs on page load and checks the localStorage item timestamp to see if
     * it's expired yet and we can show the popover again.
     */
    function checkPopoverDisabled() {
        if (win.mdn.features.localStorage) {
            var disabledStorageItem = localStorage.getItem('contributionsPopoverDisabled');
            var date = new Date().getTime();

            if (disabledStorageItem) {
                // Parses the stringified storage item
                disabledStorageItem = JSON.parse(disabledStorageItem);

                if (disabledStorageItem.value
                        && disabledStorageItem.timestamp + CONTRIBUTIONS_DISABLED_EXPIRATION < date) {
                    // Remove the item if it has expired.
                    removeDisabledLocaleStorageItem();
                    showPopover();
                }
            } else {
                // Show if LS does not exist
                showPopover();
            }
        } else {
            // Show if LS does not exist
            showPopover();
        }
    }

    /**
     * Removes 'is-hidden' class and sets the aria-hidden attribute from popover
     */
    function showPopover() {
        popoverBanner.removeClass('is-hidden');
        popoverBanner.attr('aria-hidden', false);
    }

    var form = $('#contribute-form');
    // Inputs.
    var emailField = form.find('#id_email');
    var nameField = form.find('#id_name');
    var defaultAmount = form.find('input[type=\'radio\']:checked');
    var amountRadio = form.find('input[name=donation_choices]');
    var customAmountInput = form.find('#id_donation_amount');
    // Hidden fields.
    var stripePublicKey = form.find('#id_stripe_public_key');
    var stripeToken = form.find('#id_stripe_token');
    var stripeHandler = null;
    // Other.
    var formButton = form.find('#stripe_submit');
    var formErrorMessage = form.find('#contribution-error-message');
    var amount = formButton.find('#amount');

    var submitted = false;

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
                addDisabledLocaleStorageItem();
                // Multiply selection to get value in pennies.
                // Following Stripe's convention so this is comparable with analytics.
                sessionStorage.setItem('submissionDetails', JSON.stringify({
                    amount: selectedAmount * 100,
                    page: isPopoverBanner ? 'Banner' : 'FAQ'
                }));
                form.submit();
            }
        };
        return win.StripeCheckout.configure(stripeOptions);
    }

    // Ensure we only show the form if js is enabled
    if (win.StripeCheckout) {
        $('#contribution-popover-container').removeClass('is-hidden');
    }

    var isPopoverBanner = $('.contribution-banner').hasClass('contribution-popover');

    /* If `isPopoverBanner` is false then this is the contribute page.
     Init the handler immediately */
    if (!isPopoverBanner && win.StripeCheckout) {
        stripeHandler = initStripeHandler();
    }

    if (isPopoverBanner) {
        var activeElement = null;
        var popoverBanner = $('.contribution-banner');
        var collapseButton = popoverBanner.find('#collapse-popover-button');
        var closeButton = popoverBanner.find('#close-popover-button');

        checkPopoverDisabled();
    }

    // Set initial radio state.
    defaultAmount.parent().addClass('active');

    var selectedAmount = defaultAmount.length ? defaultAmount[0].value : 0;

    customAmountInput.val('');

    // Set errors.
    form.find('.errorlist').prev().addClass('error');

    /**
     * Handles adjusting amount.
     * @param {jQuery.Event} event Event object.
     */
    function onAmountSelect(event) {
        form.find('label.active').removeClass('active');

        clearFieldError(customAmountInput);

        // Validate against minimum value.
        if (parseInt(event.target.value) < 1 || isNaN(event.target.value)) {
            defaultAmount.prop('checked', true);
            setFieldError(customAmountInput);
        }

        // Reset custom amount input when selecting radio.
        if (event.target.type === 'radio') {
            customAmountInput.val('');

            // Send GA Event.
            mdn.analytics.trackEvent({
                category: 'payments',
                action: 'banner',
                label: 'Amount radio selected',
                value: event.target.value * 100
            });

            $(event.target).parent().addClass('active');

        } else {
            // Reset radio when selecting custom amount.
            form.find('input[type=\'radio\']:checked').prop('checked', false);
        }

        selectedAmount = (Math.floor(event.target.value * 100) / 100);

        var newValue = (selectedAmount < 1 || isNaN(selectedAmount)) ? '' : '$' + selectedAmount;

        amount.html(newValue);
    }

    /**
     * Set the error message for any required field.
     * @param {Element} field Field element.
     */
    function setFieldError(field) {
        $(field).addClass('error');
        $(field).next('.errorlist').remove();

        var error = $(field).attr('data-error-message');

        $('<ul class="errorlist"><li>' + error + '</li></ul>').insertAfter($(field));

    }

    /**
     * Clear the error message for any required field.
     * @param {Element} field Field element.
     */
    function clearFieldError(field) {
        $(field).removeClass('error');
        $(field).next('.errorlist').remove();
    }

    /**
     * Checks field validity and sets any errors if required.
     * @param {jQuery.Event} event Event object.
     */
    function onChange(event) {
        var field = $(event.target)[0];

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

            return;
        }

        // Send GA Event.
        mdn.analytics.trackEvent({
            category: 'payments',
            action: 'submission',
            label: isPopoverBanner ? 'On pop over' : 'On FAQ page',
            value: selectedAmount * 100
        });

        if (stripeHandler !== null) {
            // On success open Stripe Checkout modal.
            stripeHandler.open({
                image: 'https://avatars1.githubusercontent.com/u/7565578?s=280&v=4',
                name: 'MDN Web Docs',
                description: 'Contribute to MDN Web Docs',
                zipCode: true,
                allowRememberMe: false,
                amount: (selectedAmount * 100),
                email: $(emailField).val(),
                closed: function() {
                    // Send GA Event.
                    if (!submitted) {
                        mdn.analytics.trackEvent({
                            category: 'payments',
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

    var mediaQueryList = null;

    /**
     * Increases or decreases the height of the `popoverBanner`
     * based on a `mediaQueryList` match
     */
    function handleViewportChange(evt) {
        if (evt.matches) {
            popoverBanner.removeClass('expanded');
            popoverBanner.addClass('expanded-extend');
        } else {
            popoverBanner.removeClass('expanded-extend');
            popoverBanner.addClass('expanded');
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
        }).done(function() {
            // Init stripeCheckout handler.
            stripeHandler = initStripeHandler();
        }).fail(function(error) {
            console.error('Failed to load stripe checkout library', error);
            toggleScriptError();
        });
    }

    /**
     * Displays a visual error if we cannot load the checkout script
     * also disables the submission button
     */
    function toggleScriptError() {
        formButton.attr('disabled') ? formButton.removeAttr('disabled') : formButton.attr('disabled', 'true');
        formErrorMessage.toggle();
    }

    /**
     * Expands the popover to show the full contents.
     */
    function expandPopover() {
        getStripeCheckoutScript();
        var secondaryHeader = popoverBanner[0].querySelector('h4');
        var smallDesktop = '(max-width: 1092px)';

        mediaQueryList = window.matchMedia(smallDesktop);
        var initialExpandedClass = mediaQueryList.matches ? 'expanded-extend' : 'expanded';

        popoverBanner.addClass(initialExpandedClass + ' is-expanding');
        popoverBanner.removeClass('is-collapsed');

        // listens for, and responds to, matchMedia events
        mediaQueryList.addListener(handleViewportChange);

        popoverBanner.on('transitionend', function() {
            popoverBanner.removeClass('is-expanding');
            popoverBanner.attr('aria-expanded', true);

            // store the current activeElement
            activeElement = document.activeElement;
            // move focus to the secondary header text
            secondaryHeader.focus();

            // remove the event listener
            popoverBanner.off('transitionend');

            // listen to minimise button clicks.
            collapseButton.click(collapseCta);

            $(doc).on('keydown.popoverCloseHandler', function(event) {
                if (event.keyCode === 27) { // Escape key.
                    collapseCta();
                }
            });
        });

        mdn.analytics.trackEvent({
            category: 'payments',
            action: 'banner',
            label: 'expand'
        });
    }

    /**
     * Collapses popover.
     */
    function collapseCta() {
        collapseButton.off();

        // Remove error if it exists
        if (formButton.hasClass('disabled')) {
            toggleScriptError();
        }

        // Add transitional class for opacity animation.
        popoverBanner.addClass('is-collapsing');
        popoverBanner.removeClass('expanded expanded-extend');
        popoverBanner.attr('aria-expanded', false);

        // remove the mediaQuery listener when in collapsed state
        mediaQueryList.removeListener(handleViewportChange);

        popoverBanner.on('transitionend', function() {
            popoverBanner.addClass('is-collapsed');
            popoverBanner.removeClass('is-collapsing');
            // remove the event listener
            popoverBanner.off('transitionend');
            // move focus back to the previous activeElement
            activeElement.focus();
        });

        // Send GA Event.
        mdn.analytics.trackEvent({
            category: 'payments',
            action: 'banner',
            label: 'collapse',
        });

        $(doc).off('keydown.popoverCloseHandler');
    }

    /**
     * Removes the popover from the page
     */
    function disablePopover() {
        popoverBanner.addClass('is-hidden');
        popoverBanner.attr('aria-hidden', true);

        // Send GA Event.
        mdn.analytics.trackEvent({
            category: 'payments',
            action: 'banner',
            label: 'close',
        });
        addDisabledLocaleStorageItem();
    }

    /**
     * Stores popover hidden state in local storge.
     */
    function addDisabledLocaleStorageItem() {
        if (win.mdn.features.localStorage) {
            var item = JSON.stringify({
                value: true,
                // Sets the timestamp to today so we can check its expiration subsequent each page load.
                timestamp: new Date().getTime()
            });
            localStorage.setItem('contributionsPopoverDisabled', item);
        }
    }

    /**
     * Removed popover hidden state in local storge.
     */
    function removeDisabledLocaleStorageItem() {
        if (win.mdn.features.localStorage) {
            localStorage.removeItem('contributionsPopoverDisabled');
        }
    }

    // Register event handlers and set things up.
    formButton.click(onFormButtonClick);
    amountRadio.change(onAmountSelect);
    customAmountInput.on('input', onAmountSelect);
    emailField.blur(onChange);
    nameField.blur(onChange);
    customAmountInput.blur(function(event) {
        var value = parseFloat(event.target.value);
        if (!isNaN(value) && value >= 1) {
            // Send GA Event.
            mdn.analytics.trackEvent({
                category: 'payments',
                action: 'banner',
                label: 'custom amount',
                value: Math.floor(value * 100)
            });
        } else {
            mdn.analytics.trackEvent({
                category: 'payments',
                action: 'banner',
                label: 'Invalid amount selected',
            });
        }
    });

    if (isPopoverBanner) {
        closeButton.click(disablePopover);
    }

    // Send to GA if popover is displayed.
    if (popoverBanner && popoverBanner.is(':visible')) {
        mdn.analytics.trackEvent({
            category: 'payments',
            action: 'banner',
            label: 'shown',
        });
    }

})(document, window, jQuery);
