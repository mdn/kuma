(function(doc, win, $) {
    'use strict';

    // TODO: handle this better
    var isMobile = $('main').width() < 800;

    
    if ($().tooltip) {
        var tooltipButton = $('#email-tooltip');
        tooltipButton.tooltip({
            items: '#email-tooltip',
            content: tooltipButton.prev().attr('title'),
            position: {
                my: isMobile ? 'center bottom' : 'right right',
                at: isMobile ? 'right top' : 'left left'
            }
        });
        tooltipButton.on({
            'click': function() {
                $(this).tooltip('open');
            },
            'mouseout': function() {  
                $(this).tooltip('disable');   
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
    var isCta = $('.contribution-form').hasClass('cta');
    if (isCta) {
        var cta = $('.contribution-form'),
            collapseButton = cta.find('#collapse'),
            closeButton = cta.find('#close-cta'),
            ctaCollapsedHeight = cta.height(),
            ctaHeight = 400;

        if(win.mdn.features.localStorage) {
            try {
                var hideCta = localStorage.getItem('hideCTA');
                if (hideCta) {
                    cta.addClass('hidden');
                }
            }
            catch (e) {
                // Browser doesn't support Local Storage
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

        // Minimise CTA
        cta.animate({height: ctaCollapsedHeight}, 500, function() {
            cta.addClass('collapsed');
            cta.css('height', 'auto');
            cta.removeClass('collapsing');
        });
    }

    function removeCta() {
        if(win.mdn.features.localStorage) {
            try {
                cta.addClass('hidden');
                localStorage.setItem('hideCTA', true);
            }
            catch (e) {
                // Browser doesn't support Local Storage
            }

        }
    }

    // Register event handlers
    formButton.click(onFormButtonClick);
    amountRadio.change(onAmountSelect);
    customAmountInput.on('input', onAmountSelect);
    customAmountInput.change(onAmountSelect);
    emailField.blur(onChange);
    nameField.blur(onChange);
    if (isCta) {
        closeButton.click(removeCta);
    }

})(document, window, jQuery);
