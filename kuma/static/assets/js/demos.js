/** JS enhancements for Demo Room */
$(document).ready(function () {

    // Handle commenting
    $('.comment_reply').each(function () {

        var $el = $(this),
            $form = $el.find('form');

        // Wire up reply form reveal link in threaded comments.
        $el.find('.show_reply').click(function () {
            $form.slideDown();
            return false;
        });

        // Quick and dirty validation for non-empty comment form.
        $form.submit(function () {
            return $(this).find('textarea').val().length;
        });
    });

    /* Learn More popup */
    var $learnPop = $('#learn-pop'),
        $tagsList = $('#tags-list'),
        $tagsListLearnPop = $('#tags-list, #learn-pop'),
        slideSpeed = 150;

    $('#demos-head .learnmore .button').click(function(){
      $learnPop.slideToggle(slideSpeed).removeAttr('aria-hidden');
      $(this).blur();
      if ($tagsList.is(':visible')) {
        $tagsList.hide().attr('aria-hidden', 'true');
      }
      return false;
    });

    /* Browse by Tech menu */
    $('#demos-head .tags .button, #demo-tags .button').click(function() {
      $tagsList.slideToggle(slideSpeed).removeAttr('aria-hidden');
      $(this).blur();
      if ($learnPop.is(':visible')) {
        $learnPop.hide().attr('aria-hidden', 'true');
      }
      return false;
    });

    $tagsListLearnPop.hover(
      function() {
        $(this).show().removeAttr('aria-hidden');
      },
      function() {
        $(this).slideUp('fast').attr('aria-hidden', 'true');
      }
    );

    $(document).bind('click', hider);
    $('a, input, textarea, button').bind('focus', hider);

    function hider(e) {
      var $element = $(e.target);
      if (! $element.parents().hasClass('menu'))
        $tagsListLearnPop.hide().attr('aria-hidden', 'true');
    }
});
