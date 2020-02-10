(function() {
    'use strict';

    var deleteUserConfirm = document.getElementById('delete-user-confirm');
    var deleteUserForm = document.getElementById('delete-user-form');

    if (!deleteUserForm) {
        return;
    }

    /* once a user select one of the attribution choices,
        enable the submit button */
    deleteUserForm.addEventListener('change', function(event) {
        if (event.target.checked) {
            deleteUserConfirm.classList.remove('disabled');
            deleteUserConfirm.classList.add('negative');
            deleteUserConfirm.removeAttribute('disabled');
        }
    });
})();
