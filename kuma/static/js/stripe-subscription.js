(function() {
    var stripeConfigElement = document.getElementById('stripe-config');
    var stripeForm = document.getElementById('stripe-form');
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
        token: function(response) {
            stripeTokenInput.value = response.id;
            stripeEmailInput.value = response.email;
            stripeForm.submit();
        }
    });

    stripeForm.addEventListener('submit', function(e) {
        if (!stripeTokenInput.value) {
            handler.open();
            e.preventDefault();
        }
    });

    submitButton.removeAttribute('disabled');
})();
