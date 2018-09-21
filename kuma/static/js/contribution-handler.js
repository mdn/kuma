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
     * Handles setting up and binding events for tooltips.
     */
    function setupTooltips() {
        var buttons = $('.tooltip-button');

        if (!buttons.length) {
            return;
        }

        /**
         * Shows the tooltip and sets the relevant element properties.
         * @param {Element} tooltip Tooltip element to show.
         */
        function openTooltip(tooltip) {
            tooltip.appendTo('body'); // Moves tooltip to the end of the body so we can position correctly.
            tooltip.addClass('is-open')
                .attr('aria-hidden', false);

            $(doc).on('click.tooltipHandler', function(event) {
                if (!tooltip.get(0).contains(event.target) || $(event.target).hasClass('tooltip-close')) {
                    event.preventDefault();

                    closeTooltip(tooltip);
                }
            });

            $(win).on('resize.tooltipHandler', function() {
                closeTooltip(tooltip);
            });

            // Send GA Event.
            mdn.analytics.trackEvent({
                category: 'Contribution popover',
                action: 'Tooltip Opened',
                value: 1
            });
        }

        /**
         * Hides the tooltip and sets the relevant element properties.
         * @param {Element} tooltip Tooltip element to hide.
         */
        function closeTooltip(tooltip) {
            tooltip.removeClass('is-open has-arrow-top')
                .attr('aria-hidden', true)
                .css({
                    left: 0,
                    top: 0
                });

            $(doc).off('click.tooltipHandler');
            $(win).off('resize.tooltipHandler');

            // Send GA Event.
            mdn.analytics.trackEvent({
                category: 'Contribution popover',
                action: 'Tooltip Closed',
                value: 1
            });
        }

        /**
         * Positioning the tooltip to the left or below the button depending on the available space.
         * @param {Element} tooltip Tooltip element.
         * @param {Element} element Tooltip button element.
         */
        function positionTooltip(tooltip, element) {
            // Is opening is added to remove display: none, but still keep the tooltip hidden
            // so we can get its dimensions and positino without showing it.
            tooltip.addClass('is-opening');

            var tooltipDomRect = tooltip.get(0).getBoundingClientRect();
            var elementDomRect = element.get(0).getBoundingClientRect();
            var position;

            // Checks for available width to the left of the button and positions the tooltip below the button if none
            // there isn't enough.
            if (tooltipDomRect.width > elementDomRect.left) {
                position = {
                    left: elementDomRect.left + elementDomRect.width - tooltipDomRect.width + 4,
                    top: elementDomRect.top + elementDomRect.height + win.scrollY + 10
                };

                tooltip.addClass('has-arrow-top');
            } else {
                position = {
                    left: elementDomRect.left - (elementDomRect.width / 2) - (tooltipDomRect.width - 10),
                    top: elementDomRect.top + (elementDomRect.height / 2) - (tooltipDomRect.height / 2) + win.scrollY
                };
            }

            $(tooltip).css(position);

            // Switch back to display: none; which will be removed when openTooltip() is called.
            tooltip.removeClass('is-opening');
        }

        // Handle clicks to the tooltip button.
        buttons.on('click', function(event) {
            event.stopImmediatePropagation();
            event.preventDefault();

            var target = $(event.target).closest('[aria-controls]');

            if (!target.length) {
                return;
            }

            var tooltipId = target.get(0).getAttribute('aria-controls');
            var tooltip = doc.getElementById(tooltipId);

            if (!tooltip) {
                return;
            }

            tooltip = $(tooltip);

            if (tooltip.hasClass('is-open')) {
                closeTooltip(tooltip);
            } else {
                positionTooltip(tooltip, target);
                openTooltip(tooltip);
            }
        });
    }

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

                if (disabledStorageItem.value) {
                    if (disabledStorageItem.timestamp + CONTRIBUTIONS_DISABLED_EXPIRATION > date) {
                        // Keep the popover hidden if we aren't passed the expiration date yet.
                        popoverBanner.addClass('hidden');
                        popoverBanner.attr('aria-hidden', true);
                    } else {
                        // Remove the item if it has expired.
                        localStorage.removeItem('contributionsPopoverDisabled');
                    }
                }
            }
        }
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
    // Other.
    var formButton = form.find('#stripe_submit');
    var amount = formButton.find('#amount');

    // init stripeCheckout handler.
    var stripeHandler = win.StripeCheckout.configure({
        key: stripePublicKey.val(),
        locale: 'en',
        name: 'MDN Web Docs',
        description: 'One-time donation',
        token: function(token) {
            stripeToken.val(token.id);
            form.submit();
        }
    });

    // Ensure we only show the form if js is enabled
    if (win.StripeCheckout) {
        $('#contribution-popover-container').removeClass('hidden');
    }


    var isPopoverBanner = $('.contribution-banner').hasClass('contribution-popover');

    if (isPopoverBanner) {
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
                category: 'Contribution popover',
                action: 'Amount radio selected',
                value: event.target.value
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

        if ($(field).is('#id_donation_amount')) {
            mdn.analytics.trackEvent({
                category: 'Contribution popover',
                action: 'Invalid amount selected',
                value: 1
            });
        }
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
            category: 'Contribution submission',
            action: isPopoverBanner ? 'On Popover' : 'On Page',
            value: 1
        });

        // On success open Stripe Checkout modal.
        stripeHandler.open({
            image: 'https://avatars1.githubusercontent.com/u/7565578?s=280&v=4',
            name: 'MDN Web Docs',
            description: 'Contribute to MDN Web Docs',
            zipCode: true,
            amount: (selectedAmount * 100),
            email: $(emailField).val(),
            closed: function() {
                form.removeClass('disabled');
            }
        });
    }

    /**
     * Handles the form button click. This will either attempt to submit the form
     * or will expand the popover depending on the current state of the popover.
     */
    function onFormButtonClick() {
        // Calculate the role of the submit button
        if (isPopoverBanner && popoverBanner.hasClass('is-collapsed')) {
            expandCta();
        } else {
            onSubmit();
        }
    }

    /**
     * Expands the popover to show the full contents.
     */
    function expandCta() {
        // Add transitional class for opacity animation.
        popoverBanner.addClass('expanded is-expanding');
        popoverBanner.removeClass('is-collapsed');

        popoverBanner.on('transitionend', function() {
            popoverBanner.removeClass('is-expanding');
            popoverBanner.attr('aria-expanded', true);

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
    }

    /**
     * Collapses popover.
     */
    function collapseCta() {
        collapseButton.off();

        // Add transitional class for opacity animation.
        popoverBanner.addClass('is-collapsing');
        popoverBanner.removeClass('expanded');
        popoverBanner.attr('aria-expanded', false);

        popoverBanner.on('transitionend', function() {
            popoverBanner.addClass('is-collapsed');
            popoverBanner.removeClass('is-collapsing');
            // remove the event listener
            popoverBanner.off('transitionend');
        });

        // Send GA Event.
        mdn.analytics.trackEvent({
            category: 'Contribution popover',
            action: 'collapse',
            value: 1
        });

        $(doc).off('keydown.popoverCloseHandler');
    }

    /**
     * Removes the popover from the page and stores the hidden state in local storge.
     */
    function disablePopover() {
        popoverBanner.addClass('hidden');
        popoverBanner.attr('aria-hidden', true);

        // Send GA Event.
        mdn.analytics.trackEvent({
            category: 'Contribution popover',
            action: 'close',
            value: 1
        });

        if (win.mdn.features.localStorage) {
            var item = JSON.stringify({
                value: true,
                // Sets the timestamp to today so we can check its expiration subsequent each page load.
                timestamp: new Date().getTime()
            });

            localStorage.setItem('contributionsPopoverDisabled', item);
        }
    }

    // Register event handlers and set things up.
    formButton.click(onFormButtonClick);
    amountRadio.change(onAmountSelect);
    customAmountInput.on('input', onAmountSelect);
    emailField.blur(onChange);
    nameField.blur(onChange);
    customAmountInput.blur(function(event) {
        // Send GA Event.
        mdn.analytics.trackEvent({
            category: 'Contribution popover',
            action: 'Amount manually selected',
            value: event.target.value
        });
    });

    if (isPopoverBanner) {
        closeButton.click(disablePopover);
    }

    setupTooltips();

    // Send GA Event.
    mdn.analytics.trackEvent({
        category: 'Contribution banner',
        action: 'shown',
        value: 1
    });

})(document, window, jQuery);
