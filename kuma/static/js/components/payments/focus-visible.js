(function() {
    'use strict';
    var contributeForm = document.getElementById('contribute-form');

    function removeFocusVisible() {
        this.classList.remove('focus-visible');
        this.removeEventListener('focusout', removeFocusVisible);
    }

    // When a keyup event is triggered on the contribute form,
    contributeForm.addEventListener('keyup', function(event) {
        var currentTarget = event.target;
        var targetType = currentTarget.type;

        /* The key pressed was the tab key, and the target field
           type is one of `text`, `email`, or `number */
        if (
            event.key === 'Tab' &&
            (targetType === 'text' ||
                targetType === 'email' ||
                targetType === 'number')
        ) {
            // add the `focus-visible` class.
            currentTarget.classList.add('focus-visible');
            // listen for when the field loses focus,
            currentTarget.addEventListener('focusout', removeFocusVisible);
        }
    });
})();
