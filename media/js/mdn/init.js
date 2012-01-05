/* Global initialization script */

/* Fake the placeholder attribute since Firefox doesn't support it. */
jQuery.fn.placeholder = function(new_value) {

    if (new_value) {
        this.attr('placeholder', new_value);
    }

    /* Bail early if we have built-in placeholder support. */
    if ('placeholder' in document.createElement('input')) {
        return this;
    }

    if (new_value && this.hasClass('placeholder')) {
        this.val('').blur();
    }

    return this.focus(function() {
        var $this = $(this),
            text = $this.attr('placeholder');

        if ($this.val() === text) {
            $this.val('').removeClass('placeholder');
        }
    }).blur(function() {
        var $this = $(this),
            text = $this.attr('placeholder');

        if ($this.val() === '') {
            $this.val(text).addClass('placeholder');
        }
    }).each(function(){
        /* Remove the placeholder text before submitting the form. */
        var self = $(this);
        self.closest('form').submit(function() {
            if (self.hasClass('placeholder')) {
                self.val('');
            }
        });
    }).blur();
};

// HACK: This ready() call is commented out, because all of our JS is at the
// end of the page where the DOM is pretty much ready anyway. This shaves a few
// dozen ms off page setup time.
//
// $(document).ready(function() {
    $('body').addClass('hasJS');

    // Set up input placeholders.
    $('input[placeholder]').placeholder();

    // replace no-JS search with our built-in one
    var search = $('#site-search,#doc-search');
    if (search.length) {
        search.attr('action', search.attr('data-url'))
          .removeAttr('data-url')
          .children('input[name=sitesearch]').remove();
    }

    // Submit locale form on change
    $('form.languages')
        .find('select').change(function(){
            this.form.submit();
        });


  // Set up nav dropdowns  
  $("#masthead .toggle").click(function() {
    $("#masthead .sub-menu:visible").slideUp(100).attr("aria-hidden", "true");
    $("#masthead .open").removeClass("open");
    $(this).siblings(".sub-menu").slideToggle(150).removeAttr("aria-hidden");
    $(this).toggleClass("open");
    return false;
  });
  
  // Keep the dropdown visible when it's in use
  $("#masthead .sub-menu").hover(
    function() {
      $(this).show().removeAttr("aria-hidden");
    },
    function() {
      $(this).delay(100).slideUp(150).attr("aria-hidden", "true");
      $("#masthead .toggle").delay(100).removeClass("open").blur();
    }
  );

  // Hide dropdowns when anything else is clicked
  $(document).bind('click', function(e) {
    var $clicked = $(e.target);
    if (! $clicked.parents().hasClass("menu")){
      $("#masthead .sub-menu").hide().attr("aria-hidden", "true");
      $("#masthead .toggle").removeClass("open");
    }
  });
  
  // or gets focus
  $("a, input, textarea, button, :focus").bind('focus', function(e) {
    var $focused = $(e.target);
    if (! $focused.parents().hasClass("menu")) {
      $("#masthead .sub-menu").hide().attr("aria-hidden", "true");
      $("#masthead .toggle").removeClass("open");
    }
  });

  // If found, wire up the BrowserID sign in button
  $('.browserid-signin').click(function (e) {
    if ( !$(this).hasClass('toggle') ) {
      navigator.id.getVerifiedEmail(function(assertion) {
          if (!assertion) { return; }
          $('#id_assertion')
              .val(assertion.toString())
              .parent().submit();
      });
      return false;
    }
  });

// });
