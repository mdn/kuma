(function($, doc) {
    'use strict';

    $(doc).ready(function() {
        var id = 'modal-content';
        var $content;

        $('.modal').on('click', function(e) {
            e.preventDefault();

            var href;

            // Create the iframe if not yet created
            if(!$content) {
                $content = $('<div id="' + id + '" title="' + gettext('Demo Studio') + '"><iframe style="border:0;" scrolling="no" height="450" width="600"></iframe></div>').appendTo(doc.body);
            }

            // Set the address
            href = e.target.href;
            href += ((href.indexOf('?') == -1) ? '?' : '&') + 'popup=1';
            $content.find('iframe').attr('src', href);

            // Launch the modal
            $('#' + id).dialog({
                width: 620,
                height: 500,
                modal: true
            });
        });
    });

})(jQuery, document);
