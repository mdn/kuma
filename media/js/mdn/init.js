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

        if ($this.val() == text) {
            $this.val('').removeClass('placeholder');
        }
    }).blur(function() {
        var $this = $(this),
            text = $this.attr('placeholder');

        if ($this.val() == '') {
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

// $(document).ready(function() {
    $('body').addClass('hasJS');

    // Set up input placeholders.
    $('input[placeholder]').placeholder();

    // replace no-JS search with our built-in one
    var search = $('#site-search,#doc-search');
    if (search.length) search.attr('action', search.attr('data-url'))
          .removeAttr('data-url')
          .children('input[name=sitesearch]').remove();

    // Submit locale form on change
    $('form.languages')
        .find('select').change(function(){
            this.form.submit();
        });


  // Set up nav dropdowns  
  $("#nav .toggle").click(function() {
    $("#nav .sub-menu:visible").slideUp(100).attr("aria-hidden", "true");
    $("#nav .open").removeClass("open");
    $(this).siblings(".sub-menu").slideToggle(150).removeAttr("aria-hidden");
    $(this).toggleClass("open");
    return false;
  });
  
  // Keep the dropdown visible when it's in use
  $("#nav .sub-menu").hover(
    function() {
      $(this).show().removeAttr("aria-hidden");
    },
    function() {
      $(this).delay(100).slideUp(150).attr("aria-hidden", "true");
      $("#nav .toggle").delay(100).removeClass("open").blur();
    }
  );

  // Hide dropdowns when anything else is clicked
  $(document).bind('click', function(e) {
    var $clicked = $(e.target);
    if (! $clicked.parents().hasClass("menu"))
      $("#nav .sub-menu").hide().attr("aria-hidden", "true");
      $("#nav .toggle").removeClass("open");
  });
  
  // or gets focus
  $("a, input, textarea, button, :focus").bind('focus', function(e) {
    var $focused = $(e.target);
    if (! $focused.parents().hasClass("menu"))
      $("#nav .sub-menu").hide().attr("aria-hidden", "true");
      $("#nav .toggle").removeClass("open");
  });

// }); 
