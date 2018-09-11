(function(win, doc, $, StripeCheckout) {
    'use strict';

    var isMobile = $('main').width() < 800;

    $('#id_email').tooltip({
        position: {
            my: isMobile ? 'center bottom' : 'right right',
            at: isMobile ? 'right top' : 'left left'
        }
    });

    var form = $('#contribute-form-2'),
        // Inputs
        emailField = form.find('#id_email'),
        nameField = form.find('#id_name'),
        defaultAmount = form.find('input[type=\'radio\']:checked'),
        amountRadio = form.find('input[name=donation_choices]'),
        customAmountInput = form.find('#id_donation_amount'),
        submitButton = form.find('#stripe_submit'),
        // Hidden fields
        stripePublicKey = form.find('#id_stripe_public_key'),
        stripeToken = form.find('#id_stripe_token');

    // init stripeCheckout handler
    var handler = StripeCheckout.configure({
        key: stripePublicKey.val(),
        locale: 'en',
        name: 'Sand Castles United',
        description: 'One-time donation',
        token: function(token) {
            stripeToken.val(token.id);
            form.submit();
        }
    });

    // Set initial radio state
    defaultAmount.parent().addClass('active');
    var selectedAmount = defaultAmount.length ? defaultAmount[0].value * 100 : 0;

    // Set errors
    form.find('.errorlist').prev().addClass('error');

    function onAmountSelect(ev) {
        // Fires when a radio amount or custom amount input is changed.

        form.find('label.active').removeClass('active');
        clearFieldError(customAmountInput);

        // Validate against minimum value
        // TODO: set minimum as a env varible
        if (ev.target.value < 1) {
            setFieldError(customAmountInput);
        }

        // Reset custom amount input when selecting radio
        if (ev.target.type === 'radio') {
            customAmountInput.val('');
            $(ev.target).parent().addClass('active');
        }

        selectedAmount = ev.target.value * 100;
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
        if (!valid || selectedAmount < 1) {
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
            amount: selectedAmount,
            closed: function() {
                form.removeClass('disabled');
            }
        });
    }

    // Register event handlers
    submitButton.click(onSubmit);
    amountRadio.change(onAmountSelect);
    customAmountInput.change(onAmountSelect);
    emailField.blur(onChange);
    nameField.blur(onChange);

// TODO: Ensure StripeCheckout is declared globally
})(window, document, jQuery, null /* StripeCheckout */);
