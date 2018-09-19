(function(doc, win, $) {
    'use strict';

    // Quit here if contributions are disabled.
    if (!win.mdn.contributions) {
        return;
    }

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

    var form = $('#contribute-form'),
        // Inputs
        emailField = form.find('#id_email'),
        nameField = form.find('#id_name'),
        defaultAmount = form.find('input[type=\'radio\']:checked'),
        amountRadio = form.find('input[name=donation_choices]'),
        customAmountInput = form.find('#id_donation_amount'),
        // Hidden fields
        stripePublicKey = form.find('#id_stripe_public_key'),
        stripeToken = form.find('#id_stripe_token'),
        // Other
        formButton = form.find('#stripe_submit'),
        amount = formButton.find('#amount');

    // init stripeCheckout handler
    var handler = win.StripeCheckout.configure({
        key: stripePublicKey.val(),
        locale: 'en',
        name: 'MDN Web Docs',
        description: 'One-time donation',
        token: function(token) {
            stripeToken.val(token.id);
            form.submit();
        }
    });

    // Is CTA?
    var isCta = $('.contribution-form').hasClass('contribution-popover');
    if (isCta) {
        var cta = $('.contribution-form'),
            collapseButton = cta.find('#collapse'),
            closeButton = cta.find('#close-cta'),
            ctaCollapsedHeight = cta.height(),
            ctaHeight = 480;

        if (win.mdn.features.localStorage) {
            var hideCta = localStorage.getItem('hideCTA');

            if (hideCta) {
                cta.addClass('hidden');
            }
        }
    }

    // Set initial radio state
    defaultAmount.parent().addClass('active');
    var selectedAmount = defaultAmount.length ? defaultAmount[0].value : 0;
    customAmountInput.val('');

    // Set errors
    form.find('.errorlist').prev().addClass('error');

    function onAmountSelect(ev) {
        // Fires when a radio amount or custom amount input is changed.

        form.find('label.active').removeClass('active');
        clearFieldError(customAmountInput);

        // Validate against minimum value
        // TODO: set minimum as a env varible
        if (parseInt(ev.target.value) < 1 || isNaN(ev.target.value)) {
            defaultAmount.prop('checked', true);
            setFieldError(customAmountInput);
        }

        // Reset custom amount input when selecting radio
        if (ev.target.type === 'radio') {
            customAmountInput.val('');
            $(ev.target).parent().addClass('active');
        } else {
            // reset radio when selecting custom amount
            form.find('input[type=\'radio\']:checked').prop('checked', false);
        }

        selectedAmount = (Math.floor(ev.target.value * 100) / 100);
        var newValue = (selectedAmount < 1 || isNaN(selectedAmount)) ? '' : '$' + selectedAmount;

        amount.html(newValue);
    }

    // Set the error message for any required field
    function setFieldError(field) {
        $(field).addClass('error');
        $(field).next('.errorlist').remove();
        var error = $(field).attr('data-error-message');

        $('<ul class="errorlist"><li>' + error + '</li></ul>').insertAfter($(field));
    }

    // Clear the error message for any required field
    function clearFieldError(field) {
        $(field).removeClass('error');
        $(field).next('.errorlist').remove();
    }

    // Validate email and name inputs
    function onChange(ev) {
        var field = $(ev.target)[0];
        field.checkValidity() ?  clearFieldError(field) : setFieldError(field);
    }

    function onSubmit() {
        // FE form validation
        var valid = form[0].checkValidity();
        if (!valid || (selectedAmount < 1 || isNaN(selectedAmount))) {
            emailField[0].checkValidity() ?  clearFieldError(emailField[0]) : setFieldError(emailField[0]);
            nameField[0].checkValidity() ? clearFieldError(nameField[0]) : setFieldError(nameField[0]);
            selectedAmount >= 1 ? clearFieldError(customAmountInput) : setFieldError(customAmountInput);
            return;
        }

        // on success open Stripe Checkout modal
        handler.open({
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

    function onFormButtonClick() {
        // Calculate the role of the submit button
        isCta && cta.hasClass('collapsed') ? expandCta() : onSubmit();
    }

    function expandCta() {
        // Force style="height: <CTA HEIGHT>"
        cta.height(ctaCollapsedHeight);

        //  Remove collapsed state
        cta.removeClass('collapsed');
        cta.attr('aria-expanded', true);

        // Expand CTA
        cta.animate({height: ctaHeight}, 500, function() {
            cta.css('height', 'auto');
            // listen to minimise button clicks
            collapseButton.click(collapseCta);
            $(doc).keyup(function(e) {
                if (e.keyCode === 27) { // escape key maps to keycode `27`
                    collapseCta();
                }
            });
        });
    }

    function collapseCta() {
        // ignore clicks while collapsing
        collapseButton.off();
        // Force style="height: <CTA HEIGHT>"
        ctaHeight = cta.height();
        cta.height(ctaHeight);
        // Add Transitional class for opacity animation
        cta.addClass('collapsing');
        cta.attr('aria-expanded', false);

        // Minimise CTA
        cta.animate({height: ctaCollapsedHeight}, 500, function() {
            cta.addClass('collapsed');
            cta.css('height', 'auto');
            cta.removeClass('collapsing');
        });
    }

    function removeCta() {
        cta.addClass('hidden');
        cta.attr('aria-hidden', true);

        if (win.mdn.features.localStorage) {
            localStorage.setItem('hideCTA', true);
        }
    }

    // Register event handlers and set things up.
    formButton.click(onFormButtonClick);
    amountRadio.change(onAmountSelect);
    customAmountInput.on('input', onAmountSelect);
    customAmountInput.change(onAmountSelect);
    emailField.blur(onChange);
    nameField.blur(onChange);

    if (isCta) {
        closeButton.click(removeCta);
    }

    setupTooltips();

})(document, window, jQuery);
