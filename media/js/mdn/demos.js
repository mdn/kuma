/** JS enhancements for Demo Room */
$(document).ready(function () {

    $('.comment_reply').each(function () {

        var el = $(this);
        
        // Wire up reply form reveal link in threaded comments.
        el.find('.show_reply').click(function () {
            el.find('form').slideDown();
            return false;
        });

        // Quick and dirty validation for non-empty comment form.
        el.find('form').submit(function () {
            if ($(this).find('textarea').val().length == 0) {
                return false;
            }
            return true;
        });


    });

});

$(".gallery").ready(function(){
    $(".gallery").addClass("js");

    $(".gallery .demo").hoverIntent({
      interval: 250,
      over: function() {
        var content = $(this).html(),
            demo = $(this), 
            offs = $(this).offset();
        $("#content").prepend('<div class="demo demohover"><div class="in">'+content+'<\/div><\/div>');
        if (demo.parents("#featured-demos").length) {
          $("#content").find("div.demohover").addClass("featured");
        };
        // $("div.demohover").addClass( $(this).attr("class") ).css({ left: offs.left, top: offs.top }).fadeIn(200).mouseleave(function() {
        $("div.demohover")
            //.addClass( $(this).attr("class") )
            .css({ left: offs.left, top: offs.top })
            .fadeIn(200)
            .mouseleave(function() {
                $(this).fadeOut(200, function(){ 
                    $(this).remove(); 
                });
            });
      }, 
      out: function() { /* do nothing */ }
    });

});	

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
