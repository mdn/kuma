$(document).ready(function() {
    var $content,
        id = 'modal-content';
        
    $('.modal').on('click', function(e) {
        e.preventDefault();

        // Create the iframe if not yet created
        if(!$content) {
            $content = $('<div id="' + id + '" title="' + gettext('Demo Studio') + '"><iframe style="border:0;" scrolling="no" height="400" width="600"></iframe></div>').appendTo(document.body);
        }

        // Set the address
        var href = e.target.href;
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