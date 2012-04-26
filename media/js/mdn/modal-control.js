$('.modal').click(function (ev) {
        
    var link = $(this),
        width  = 600,
        height = 400,
        href   = link.attr('href');

    href += ((href.indexOf('?') == -1) ? '?' : '&') + 'popup=1';
    $.modal(
        '<iframe style="border:0" scrolling="no" src="'+href+'"' +
            ' height="'+height+'" width="'+width+'">', 
        {
            overlayClose:true,
            containerCss: { width: width, height: height },
            dataCss: { overflow: 'hidden' },
            onOpen: function (dialog) {
                dialog.wrap.css({ overflow: 'hidden' });
                dialog.overlay.show();
                dialog.container.show();
                dialog.data.show();
            }
        }
    );

    return false;
});

$('.closeModal').click(function () {
    if (top.$ && top.$.modal) {
        top.$.modal.close();
    }
    return false;
});