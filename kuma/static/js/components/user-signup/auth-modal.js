(function() {
    'use strict';

    var authModalContainer = document.getElementById('auth-modal');

    if (!window.mdn.modalDialog.showModal(authModalContainer)) {
        return;
    }

    /* The React header takes just a couple of milliseconds to
       long to load so, we need to wrap the code below in a 
       setTimeout */
    setTimeout(function() {
        var pageHeader = document.querySelector('.page-header');
        pageHeader.addEventListener('click', function(event) {
            if (event.target.classList.contains('signin-link')) {
                event.preventDefault();
                var modalContentContainer = authModalContainer.querySelector(
                    'section'
                );
                var closeModalButton = document.getElementById('close-modal');

                authModalContainer.classList.remove('hidden');
                modalContentContainer.focus();

                closeModalButton.addEventListener('click', function() {
                    window.mdn.modalDialog.closeModal(
                        authModalContainer,
                        event.target
                    );
                });

                window.mdn.modalDialog.handleKeyboardEvents(
                    authModalContainer,
                    event.target
                );
            }
        });
    }, 100);
})();
