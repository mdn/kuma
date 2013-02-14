(function ($) {

  var $body = $("body"),
      $window = $(window);

  // Callback functions after CKE is ready
  var setup_ckeditor = function () {
  
    var $appBoxes  = $(".approved .boxed"),
        $head      = $("#article-head"),
        $transdesc = $("#trans-description"),
        $transcont = $("#content-fields"),
        $tools     = $("div.cke_toolbox"),
        $wikiArt   = $("#cke_wikiArticle"),
        contentTop = $("#content").offset(),
        transTop   = $transcont.offset(),
        headHeight = $head.height(),
        toolHeight = $tools.height(),
        fixed = false;
        
    $("#content-fields .approved .boxed").css({ paddingTop: toolHeight+54});
  
    // Switch header and toolbar styles on scroll to keep them on screen
    $window.scroll(function() {

      var scrollTop = $window.scrollTop(),
          transTop  = $transcont.offset();
          
    	if( scrollTop >= contentTop.top ) {
        if( !fixed ) {
          fixed = true;
          $head.css({position:"fixed", top:19, width:"95%"});
          $transdesc.css({ marginTop: headHeight });
        }
      } 
      else {
        if( fixed ) {
          fixed = false;
          $head.css({position:"relative", top:"auto", width:"auto"});
          $transdesc.css({ marginTop: 0 });
        }
      }

      if( scrollTop >= ( transTop.top - headHeight ) ) {
        $tools.css({position:"fixed", top:headHeight+45, width:$("#cke_id_content").width()-10});
        $transcont.addClass("fixed");
        $("#content-fields header").css({ position: "fixed", top:headHeight });
        $("td.cke_top").css({ height: toolHeight+38 });
      }
      else {
        $tools.css({position:"relative", top:"auto", width:"auto"});
        $transcont.removeClass("fixed");
        $("#content-fields header").css({ position: "static", top:"auto" });
        $("td.cke_top").css({ height: "auto" });
      }

      $("#cke_contents_id_content").css({ height: $appBoxes.height() });

      // remove the id_content required attribute
      $('#id_content').removeAttr("required");

    });
    
    $window.resize(function() { // Recalculate box width on resize
      if (fixed) {
        $tools.css({ width: $wikiArt.width()-10 }); // Readjust toolbox to fit
      }
    });

  };

  $("#id_content").each(function () {
      if (!$body.is(".edit.is-template")) {
          $(this).ckeditor(setup_ckeditor, {
              customConfig: "/docs/ckeditor_config.js"
          });
      }
  });

})(jQuery);