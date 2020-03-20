(function() {
    var stripeConfigElement = document.getElementById('stripe-config');
    var stripeForm = document.getElementById('stripe-form');

    // This script is loaded for both before and after form submission.
    // In the latter case no form is rendered anymore
    if (!stripeForm) {
        return;
    }

    var stripeTokenInput = stripeForm.querySelector('[name="stripe_token"]');
    var stripeEmailInput = stripeForm.querySelector('[name="stripe_email"]');
    var submitButton = stripeForm.querySelector('[type="submit"]');

    var config = JSON.parse(stripeConfigElement.textContent);

    var handler = window.StripeCheckout.configure({
        key: config.STRIPE_PUBLIC_KEY,
        locale: 'auto',
        name: 'MDN Web Docs',
        zipCode: true,
        currency: 'usd',
        amount: 500,
        label: 'Subscribe',
        email: stripeEmailInput.value,
        token: function(response) {
            stripeTokenInput.value = response.id;
            stripeForm.submit();
        },
        closed: function() {
            if (!stripeTokenInput.value) {
                stripeForm.classList.remove('disabled');
            }
        }
    });

    stripeForm.addEventListener('submit', function(e) {
        if (!stripeTokenInput.value) {
            this.classList.add('disabled');
            handler.open();
            e.preventDefault();
        }
    });

    submitButton.removeAttribute('disabled');
})();
