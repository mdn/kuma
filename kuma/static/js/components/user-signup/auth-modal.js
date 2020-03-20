(function() {
    'use strict';

    var authModalContainer = document.getElementById('auth-modal');

    if (
        !authModalContainer ||
        !window.mdn.modalDialog.shouldShowModal()
    ) {
        return;
    }

    var pageHeader = document.querySelector('.page-header');
    pageHeader.addEventListener('click', function(event) {
        function handleKeyup(event) {
            if (event.key === 'Escape') {
                closeModalButton.click();
            }
        }

        var closeModalButton = document.getElementById('close-modal');

        if (event.target.classList.contains('signin-link')) {
            event.preventDefault();
            var modalContentContainer = authModalContainer.querySelector(
                'section'
            );

            authModalContainer.classList.remove('hidden');
            modalContentContainer.focus();

            closeModalButton.addEventListener('click', function() {
                window.mdn.modalDialog.closeModal(
                    authModalContainer,
                    event.target
                );
                document.removeEventListener('keyup', handleKeyup);
            });

            window.mdn.modalDialog.handleKeyboardEvents(authModalContainer);

            document.addEventListener('keyup', handleKeyup);
        }
    });
})();
