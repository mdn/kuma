/** JS enhancements for Demo Room */
$(document).ready(function () {

    // Handle commenting
    $(".comment_reply").each(function () {

        var $el = $(this),
            $form = $el.find("form");
        
        // Wire up reply form reveal link in threaded comments.
        $el.find(".show_reply").click(function () {
            $form.slideDown();
            return false;
        });

        // Quick and dirty validation for non-empty comment form.
        $form.submit(function () {
            return $(this).find("textarea").val().length;
        });
    });

    // Ensure gallery works as needed
    var $gallery = $(".gallery");

    $gallery.addClass("js");

    $gallery.find(".demo").hoverIntent({
      interval: 250,
      over: function() {
        var $demo = $(this),
            content = $demo.html(), 
            offs = $demo.offset(),
            $contentContainer = $("#content");

        $contentContainer.prepend('<div class="demo demohover"><div class="in">'+content+'<\/div><\/div>');
        if ($demo.parents("#featured-demos").length) {
          $contentContainer.find("div.demohover").addClass("featured");
        };
        $("div.demohover")
            .addClass( $(this).attr("class") )
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

    /* Learn More popup */
    var $learnPop = $("#learn-pop"),
        $tagsList = $("#tags-list"),
        $tagsListLearnPop = $("#tags-list, #learn-pop");

    $("#demos-head .learnmore .button").click(function(){
      $learnPop.slideToggle(150).removeAttr("aria-hidden");
      $(this).blur();
      if ($tagsList.is(":visible")) { 
        $tagsList.hide().attr("aria-hidden", "true"); 
      }
      return false;
    });

    /* Browse by Tech menu */
    $("#demos-head .tags .button, #demo-tags .button").click(function() {
      $tagsList.slideToggle(150).removeAttr("aria-hidden");
      $(this).blur();
      if ($learnPop.is(":visible")) { 
        $learnPop.hide().attr("aria-hidden", "true"); 
      }
      return false;
    });

    $tagsListLearnPop.hover(
      function() {
        $(this).show().removeAttr("aria-hidden");
      },
      function() {
        $(this).slideUp('fast').attr("aria-hidden", "true");
      }
    );

    $(document).bind('click', function(e) {
      var $clicked = $(e.target);
      if (! $clicked.parents().hasClass("menu"))
        $tagsListLearnPop.hide().attr("aria-hidden", "true");
    });

    $("a, input, textarea, button").bind('focus', function(e) {
      var $focused = $(e.target);
      if (! $focused.parents().hasClass("menu"))
        $tagsListLearnPop.hide().attr("aria-hidden", "true");
    });



});