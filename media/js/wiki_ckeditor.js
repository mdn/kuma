(function() {

  // Callback functions after CKE is ready
  var setup_ckeditor = function() {

    var $head = $("#article-head"),
      $tools = $(".cke_toolbox"),
      contentTop = $("#content").offset(),
      headHeight = $head.height(),
      toolHeight = $tools.height(),
      contentBottom = $(".page-meta").first().offset().top - 300,
      fixed = false;

    // Switch header and toolbar styles on scroll to keep them on screen
    $(document).scroll(function() {
      //Position of the first metadata at 300px of the top
      if ($(this).scrollTop() >= contentTop.top && $(this).scrollTop() < contentBottom) { // If top of the window is betwen top of #content and top of metadata (first .page-meta) blocks, the header is fixed
        if (!fixed) {
          fixed = true;
          $head.css({
            position: "fixed",
            top: 19,
            width: "95%"
          });
          $tools.css({
            position: "fixed",
            top: headHeight + 28,
            width: $("#cke_id_content").width() - 11
          });
          $("td.cke_top").css({
            height: toolHeight + 28
          });
          $("#cke_id_content").css({
            marginTop: headHeight
          });
        }
      } else { // If not, header is relative
        if (fixed) {
          fixed = false;
          $head.css({
            position: "relative",
            top: "auto",
            width: "auto"
          });
          $tools.css({
            position: "relative",
            top: "auto",
            width: "auto"
          });
          $("td.cke_top").css({
            height: "auto"
          });
          $("#cke_id_content").css({
            marginTop: 0
          });
        }
      }
    });

    $(window).resize(function() { // Recalculate box width on resize
      if (fixed) {
        $tools.css({
          width: $("#cke_id_content").width() - 10
        }); // Readjust toolbox to fit
      }
    });

    // remove the id_content required attribute
    $("#id_content").removeAttr("required");

  };

  $("#id_content").each(function() {
    if (!$("body").is(".edit.is-template")) {
      $(this).ckeditor(setup_ckeditor, {
        customConfig: "/docs/ckeditor_config.js"
      });
    }
  });

})(jQuery);