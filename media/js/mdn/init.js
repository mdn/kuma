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

/* Parse a querystring into an object */
jQuery.extend({
	parseQuerystring: function(str){
		var nvpair = {},
			qs = (str || window.location.search).replace("?", ""),
			pairs = qs.split("&");
			
		$.each(pairs, function(i, v){
			var pair = v.split("=");
			nvpair[pair[0]] = pair[1];
		});
		
		return nvpair;
	}
});

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
  $(".toggle").click(function() {
    $(".sub-menu:visible").slideUp(100).attr("aria-hidden", "true");
    $(".toggle.open").removeClass("open");
    $(this).siblings(".sub-menu").slideToggle(150).removeAttr("aria-hidden");
    $(this).toggleClass("open");
    return false;
  });
  
  // Keep the dropdown visible when it's in use
  $(".sub-menu").hover(
    function() {
      $(this).show().removeAttr("aria-hidden");
    },
    function() {
      $(this).delay(100).slideUp(150).attr("aria-hidden", "true");
      $("a.toggle").delay(100).removeClass("open").blur();
    }
  );

  // Hide dropdowns when anything else is clicked
  $(document).bind('click', function(e) {
    var $clicked = $(e.target);
    if (! $clicked.parents().hasClass("menu"))
      $(".sub-menu").hide().attr("aria-hidden", "true");
      $("a.toggle").removeClass("open");
  });
  
  // or gets focus
  $("a, input, textarea, button, :focus").bind('focus', function(e) {
    var $focused = $(e.target);
    if (! $focused.parents().hasClass("menu")) {
      $(".sub-menu").hide().attr("aria-hidden", "true");
      $("a.toggle").removeClass("open");
    }
  });

  function bindBrowserIDSignin() {
    $('.browserid-signin').click(function (e) {
      if ( !$(this).hasClass('toggle') ) {
        navigator.id.getVerifiedEmail(function(assertion) {
          if (!assertion) { return; }
          $('input[name="assertion"]').val(assertion.toString());
          $('form.browserid').first().submit();
        });
        return false;
      }
    });
  }

  
  
  (function() {
    
    var $signedOutList = $('ul.signed-out');
    
    if($signedOutList.length) {
      // Hide the signed-out block, add and wire up a BrowserID sign in button,
      // then show the signed-out block again
      $signedOutList.hide();  
      
      // Retrieve the login url
      var url = $signedOutList.attr('data-browserid-header-signin-html');
        
      // Split the URL, find the next value
      var urlSplit = url.split("?"),
          rootUrl = urlSplit.shift(),
          qstring = urlSplit.join("?");
      
      $.get(rootUrl, {
        next: $.parseQuerystring(qstring).next || $.parseQuerystring().next || window.location.pathname
      }, function(content) {
        $signedOutList.html(content).each(function() {
          $('.toggle', $(this)).click(function() {
              $(this).siblings(".sub-menu").slideToggle(150).removeAttr("aria-hidden");
              return false;
          });
        });
        // Binding the signout link!
        bindBrowserIDSignin();
      });
      
      $signedOutList.show();
    }
    
  })();
  

  // Wire up the statically-drawn browserid-signin element on the change
  // email page
  $('#change-email').ready(function(){
      bindBrowserIDSignin();
  });

// });
