/*
 * wiki.js
 * Scripts for the wiki app.
 */
(function () {
    function init() {
        initPrepopulatedSlugs();
        initReviewModal();
    }

    function initPrepopulatedSlugs() {
        var fields = {
            title: {
                id: '#id_slug',
                dependency_ids: ['#id_title'],
                dependency_list: ['#id_title'],
                maxLength: 50
            }
        }, field = null;

        for (i in fields) {
            field = fields[i];
            $('#id_slug').addClass('prepopulated_field');
            $(field.id).data('dependency_list', field['dependency_list'])
                   .prepopulate($(field['dependency_ids'].join(',')),
                                field.maxLength);
        };
    }

    /*
     * Initialize the modal that shows when the reviewer goes to Approve
     * or Reject a revision.
     */
    function initReviewModal() {
        $('#btn-approve').click(function(ev){
            ev.preventDefault();
            openModal('form.accept-form');
        });
        $('#btn-reject').click(function(ev){
            ev.preventDefault();
            openModal('form.reject-form');
        });

        function openModal(selector) {
            var $modal = $(selector).clone();
            $modal.attr('id', 'review-modal')
                  .append('<a href="#close" class="close">&#x2716;</a>');
            $modal.find('a.close, a.cancel').click(closeModal);

            var $overlay = $('<div id="modal-overlay"></div>');

            $('body').append($overlay).append($modal);

            function closeModal(ev) {
                ev.preventDefault();
                $modal.unbind().remove();
                $overlay.unbind().remove();
                delete $modal;
                delete $overlay;
                return false;
            }
        }
    }

    $(document).ready(init);

}());
