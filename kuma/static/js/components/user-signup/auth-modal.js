(function() {
    'use strict';

    var authModalContainer = document.getElementById('auth-modal');

    if (
        !authModalContainer ||
        !window.mdn.modalDialog.shouldShowModal()
    ) {
        return;
    }

    function triggerAuthModal() {

        function handleKeyup(event) {
            if (event.key === 'Escape') {
                closeModalButton.click();
            }
        }

        var closeModalButton = document.getElementById('close-modal');
        var modalContentContainer = authModalContainer.querySelector('section');
        authModalContainer.classList.remove('hidden');
        modalContentContainer.focus();

        closeModalButton.addEventListener('click', function() {
            window.mdn.modalDialog.closeModal(authModalContainer);
            document.removeEventListener('keyup', handleKeyup);
        });

        window.mdn.modalDialog.handleKeyboardEvents(authModalContainer);

        document.addEventListener('keyup', handleKeyup);

    }

    window.mdn.triggerAuthModal = triggerAuthModal;

})();
