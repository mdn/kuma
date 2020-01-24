(function() {
    var stripeConfigElement = document.getElementById('stripe-config');
    var stripeSection = document.querySelector('.stripe-subscription');
    var stripeForm = document.getElementById('stripe-form');

    // The query parameter is added when the user submits the form
    if (
        stripeSection.scrollIntoView &&
        location.search.indexOf('has_stripe_error') !== -1
    ) {
        history.replaceState(null, '', location.pathname);
        stripeSection.scrollIntoView({behavior: 'smooth'});
    }

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
