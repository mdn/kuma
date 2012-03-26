(function () {

  // Callback functions after CKE is ready
  var setup_ckeditor = function () {

    var $head      = $("#article-head");
    var $tools     = $(".cke_toolbox");
    var contentTop = $("#content").offset();
    var headHeight = $head.height();
    var toolHeight = $tools.height();
    var fixed = false;

    // Switch header and toolbar styles on scroll to keep them on screen
    $(document).scroll(function() {
        if( $(this).scrollTop() >= contentTop.top ) {
            if( !fixed ) {
                fixed = true;
                $head.css({position:'fixed', top:19, width:"95%"});
                $tools.css({position:'fixed', top:headHeight+28, width:$("#cke_id_content").width()-10});
                $("td.cke_top").css({ height: toolHeight+28 });
                $("#cke_id_content").css({ marginTop: headHeight });
            }
        } else {
            if( fixed ) {
                fixed = false;
                $head.css({position:'relative', top:"auto", width:"auto"});
                $tools.css({position:'relative', top:"auto", width:"auto"});
                $("td.cke_top").css({ height: "auto" });
                $("#cke_id_content").css({ marginTop: 0 });
            }
        }
    });

    $(window).resize(function() { // Recalculate box width on resize
      if ( fixed ) {
        $tools.css({width:$("#cke_id_content").width()-10}); // Readjust toolbox to fit
      }
    });

    // remove the id_content required attribute
    $('#id_content').removeAttr("required");

  };

  jQuery("#id_content").each(function () {

      var el = jQuery(this),
          doc_slug = $('#id_slug').val();

      if (doc_slug.toLowerCase().indexOf('template:') === 0) {
          // HACK: If we're on a Template:* page, abort setting up CKEditor
          // because it doesn't work well at all for these pages.
          // See bug 731651 for further work down this path.
          return;
      }

      el.ckeditor(setup_ckeditor, {
          customConfig : '/docs/ckeditor_config.js'
      });

  });

})();
