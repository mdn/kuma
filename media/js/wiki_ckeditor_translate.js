(function () {

  // Callback functions after CKE is ready
  var setup_ckeditor = function () {
  
    var $head      = $("#article-head");
    var $transdesc = $("#trans-description");
    var $transcont = $("#content-fields");
    var $tools     = $("div.cke_toolbox");
    var contentTop = $("#content").offset();
    var transTop   = $transcont.offset();
  	var headHeight = $head.height();
  	var descHeight = $transdesc.height();
  	var toolHeight = $tools.height();
    var fixed = false;
        
    $("#content-fields .approved .boxed").css({ paddingTop: toolHeight+54});
  
    // Switch header and toolbar styles on scroll to keep them on screen
    $(window).scroll(function() {
      transTop   = $transcont.offset();
          
    	if( $(window).scrollTop() >= contentTop.top ) {
    	  if( !fixed ) {
    	    fixed = true;
    	    $head.css({position:'fixed', top:19, width:"95%"});
    	    $transdesc.css({ marginTop: headHeight });
    	  }
    	} 
    	else {
    	  if( fixed ) {
    	    fixed = false;
    	    $head.css({position:'relative', top:"auto", width:"auto"});
    	    $transdesc.css({ marginTop: 0 });
    	  }
    	}

      if( $(window).scrollTop() >= ( transTop.top - headHeight ) ) {
        $tools.css({position:'fixed', top:headHeight+45, width:$("#cke_id_content").width()-10});
        $transcont.addClass('fixed');
        $("#content-fields header").css({ position: "fixed", top:headHeight });
        $("td.cke_top").css({ height: toolHeight+38 });
      }
      else {
        $tools.css({position:"relative", top:"auto", width:"auto"});
        $transcont.removeClass('fixed');
        $("#content-fields header").css({ position: "static", top:"auto" });
        $("td.cke_top").css({ height: "auto" });
      }

      $("#cke_contents_id_content").css({ height: $(".approved .boxed").height() });

    });
    
    $(window).resize(function() { // Recalculate box width on resize
      if ( fixed ) {
        $tools.css({width:$("#cke_wikiArticle").width()-10}); // Readjust toolbox to fit
      }
    });

  }

  jQuery("#id_content").each(function () {

      var el = jQuery(this),
          doc_slug = $('#id_slug').val();

      if (!$('body').is('.edit.is-template')) {
          el.ckeditor(setup_ckeditor, {
              customConfig : '/docs/ckeditor_config.js'
          });
      }

  });

})();
