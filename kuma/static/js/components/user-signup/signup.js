(function() {
    'use strict';

    var signupForm = document.getElementById('social-signup-form');

    /**
     * Hides the specified static content container, shows the edit
     * container and sets focus to the specified element.
     * @param {Object} staticContainer - The container to hide
     * @param {Object} editContainer - The container to show
     * @param {Object} focusElement - The element to focus
     */
    function showEditFields(staticContainer, editContainer, focusElement) {
        staticContainer.classList.add('hidden');
        editContainer.classList.remove('hidden');
        focusElement.focus();
    }

    signupForm.addEventListener('click', function(event) {
        var editContainer;
        var focusElement;
        var staticContainer;

        if (event.target.id === 'change-username') {
            staticContainer = document.getElementById(
                'username-static-container'
            );
            editContainer = document.getElementById(
                'change-username-container'
            );
            focusElement = editContainer.querySelector('input');
            showEditFields(staticContainer, editContainer, focusElement);
        }
    });
})();
