(function() {
    'use strict';

    var otherEmailInput = document.getElementById('id_other_email');
    var signupForm = document.getElementById('social-signup-form');

    /**
     * Hides the specified static content container, shows the edit
     * container and sets focus to input element.
     * @param {Object} staticContainer - The container to hide
     */
    function showEditFields(staticContainer) {
        staticContainer.classList.add('hidden');
        staticContainer.nextElementSibling.classList.remove('hidden');
        staticContainer.nextElementSibling.querySelector('input').focus();
    }

    /**
     * Hide all containers with class `error` inside the `form`
     * @param {Object} form - The form from which to clear visible error messages
     */
    function clearErrors(form) {
        var errors = form.querySelectorAll('.error');

        for (var i = 0, l = errors.length; i < l; i++) {
            errors[i].classList.add('hidden');
        }
    }

    signupForm.addEventListener('click', function(event) {
        var staticContainer;

        var editUsernameContainer = document.getElementById(
            'change-username-container'
        );
        var editEmailContainer = document.getElementById(
            'change-email-container'
        );

        if (event.target.id === 'change-username') {
            staticContainer = document.getElementById(
                'username-static-container'
            );
            showEditFields(staticContainer);
        } else if (event.target.id === 'change-email') {
            staticContainer = document.getElementById('email-static-container');
            showEditFields(staticContainer);
        } else if (event.target.id === 'create-mdn-account') {
            var formValid = true;
            var signupFields = [
                editUsernameContainer.querySelector('input'),
                editEmailContainer.querySelector('input')
            ];

            clearErrors(signupForm);

            for (var i = 0, l = signupFields.length; i < l; i++) {
                var currentField = signupFields[i];
                if (currentField.value.trim() === '') {
                    signupForm
                        .querySelector('#' + currentField.id + '-error')
                        .classList.remove('hidden');
                    showEditFields(
                        signupForm.querySelector(
                            '#' + currentField.name + '-static-container'
                        )
                    );
                    formValid = false;
                }
            }

            if (!formValid) {
                event.preventDefault();
            }
        }
    });

    /* when the "other" email input field lose focus, set its
       associated radio button to the checked state if the
       data entered was valid */
    if (otherEmailInput) {
        otherEmailInput.addEventListener('blur', function(event) {
            if (event.target.validity.valid) {
                event.target.parentElement.querySelector(
                    'input[type="radio"]'
                ).checked = true;
            }
        });
    }
})();
