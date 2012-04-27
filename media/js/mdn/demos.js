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
});	

/* Learn More popup */
$("#demos-head .learnmore .button").click(function(){
  $("#learn-pop").slideToggle(150).removeAttr("aria-hidden");
  $(this).blur();
  if ($("#tags-list").is(":visible")) { 
    $("#tags-list").hide().attr("aria-hidden", "true"); 
  }
  return false;
});

/* Browse by Tech menu */
$("#demos-head .tags .button, #demo-tags .button").click(function() {
  $("#tags-list").slideToggle(150).removeAttr("aria-hidden");
  $(this).blur();
  if ($("#learn-pop").is(":visible")) { 
    $("#learn-pop").hide().attr("aria-hidden", "true"); 
  }
  return false;
});

$("#tags-list, #learn-pop").hover(
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
    $("#tags-list, #learn-pop").hide().attr("aria-hidden", "true");
});

$("a, input, textarea, button").bind('focus', function(e) {
  var $focused = $(e.target);
  if (! $focused.parents().hasClass("menu"))
    $("#tags-list, #learn-pop").hide().attr("aria-hidden", "true");
});
