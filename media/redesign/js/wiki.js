(function(win, doc, $) {
  'use strict';

  /*
    Togglers within articles (i.e.)
  */
  $('.toggleable').mozTogglers();

  /*
    Toggle for quick links show/hide
  */
  (function() {
    // Set up the quick links for the toggler
    var $quickLinks = $('#quick-links');
    setupTogglers($quickLinks.find('> ul > li, > ol > li'));
    $quickLinks.find('.toggleable').mozTogglers();

    var $columnContainer = $('#wiki-column-container');
    var $quickLinksControl = $('#wiki-controls .quick-links');

    var child = $('#wiki-left').get(0);
    if(child) {
      var parent = child.parentNode;
    }

    // Quick Link toggles
    $('#quick-links-toggle, #show-quick-links').on('click', function(e) {
      e.preventDefault();
      $(child).toggleClass('column-closed');
      $columnContainer.toggleClass('wiki-left-closed');
      $quickLinksControl.toggleClass('hidden');

      if($(child).hasClass('column-closed')) {
        parent.removeChild(child);
      }
      else {
        parent.appendChild(child);
      }
    });
  })();

  /*
    Set up the zone subnav accordion
  */
  $('.subnav').each(function() {
    var $subnav = $(this);
    var $subnavList = $subnav.find(' > ol');
    var minHeightFn = $('.zone-landing-header-preview-base').length ? setMinHeight : noop;

    if(!$subnavList.length) return; // Exit if the subnav isn't set up properly

    // Set the list items as togglers where needed
    setupTogglers($subnavList.find('li'));

    // Make them toggleable!
    $subnavList.find('.toggleable').mozTogglers({
      slideCallback: minHeightFn
    });

    // Try to find the current page in the list, if found, open it
    // Need to keep track of the elements we've found so they aren't found twice
    var used = [];
    var $selected = $subnavList.find('a[href$="' + doc.location.pathname + '"]');
    $selected.each(function() {
      var self = this;
      var $togglers = $(this).parents('.toggleable').find('.toggler');

      $togglers.each(function() {
        if($.contains($(this).parent('li').get(0), self) && used.indexOf(this) === -1) {
          $(this).trigger('mdn:click');
          used.push(this);
        }
      });
    }).parent().addClass('current');

    // Mark this is an accordion so the togglers open/close properly
    $subnavList.addClass('accordion');

    function noop(){}
    function setMinHeight() {
      if($('.zone-landing-header-preview-base').css('position') == 'absolute') {
        $('.wiki-main-content').css('min-height', $subnav.height());
      }
    }

    minHeightFn();
  });

  /*
    Subscribe / unsubscribe to an article
  */
  $('.page-watch a').on('click', function(e) {
    e.preventDefault();
    $(this).closest('form').submit();
  });

  // Utility method for the togglers
  function setupTogglers($elements) {
    $elements.each(function() {
      var $li = $(this);
      var $sublist = $li.find('> ul, > ol');

      if($sublist.length) {
        $li.addClass('toggleable closed');
        $li.find('> a').addClass('toggler').prepend('<i aria-hidden="true" class="icon-caret-up"></i>');
        $sublist.addClass('toggle-container');
      }
    });
  }

  /* Syntax highlighting scripts */
  $('article pre').length && (function() {
    var mediaPath = win.mdn.mediaPath;
    $('<link />').attr({
      type: 'text/css',
      rel: 'stylesheet',
      href: mediaPath + 'css/syntax-prism-min.css'
    }).appendTo(doc.head);

    var syntaxScript = doc.createElement('script');
    syntaxScript.setAttribute('data-manual', '');
    syntaxScript.async = 'true';
    syntaxScript.src = mediaPath + 'js/syntax-prism-min.js';
    doc.body.appendChild(syntaxScript);
  })();


  /*
    Set up the scrolling TOC effect
  */
  (function() {
    var $toc = $('#toc');
    if($toc.length) {
      var tocOffset = $toc.offset().top;
      var $toggler = $toc.find('> .toggler');
      var fixedClass = 'fixed';
      var $wikiRight = $('#wiki-right');

      var scrollFn = debounce(function(e) {
        // Set forth the pinned or static positioning of the table of contents
        var scroll = win.scrollY;
        var maxHeight = win.innerHeight - parseInt($toc.css('padding-top'), 10) - parseInt($toc.css('padding-bottom'), 10);

        if(scroll > tocOffset && $toggler.css('pointer-events') == 'none') {
          $toc.css({
            width: $toc.css('width'),
            maxHeight: maxHeight
          });

          if(!$toc.hasClass(fixedClass)){
            $toc.addClass(fixedClass);
          }
        }
        else {
          $toc.css({
            width: 'auto',
            maxHeight: 'none'
          });
          $toc.removeClass(fixedClass);
        }

        // Should the TOC be one-column (auto-closed) or sidebar'd
        if(!e || e.type == 'resize') {
          if($toggler.css('pointer-events') == 'auto'  || $toggler.find('i').css('display') != 'none') { /* icon check is for old IEs that don't support pointer-events */
            if(!$toc.attr('data-closed')) {
              $toggler.trigger('mdn:click');
            }
          }
          else if($toc.attr('data-closed')) { // Changes width, should be opened (i.e. mobile to desktop width)
            $toggler.trigger('mdn:click');
          }
        }
      }, 10);

      // Set it forth!
      scrollFn();
      $(win).on('scroll', scrollFn);
    }
  })();

  /*
    Compat table table setup
  */
  $('.htab').each(function(index) {
      var $htab = $(this);
      var $items = $htab.find('>ul>li');

      $htab.append($('div[id=compat-desktop]')[index]);
      $htab.append($('div[id=compat-mobile]')[index]);

      $items.find('a').on('click mdn:click', function(e) {
          var $this = $(this);
          if(e) {
            e.preventDefault();
            e.stopPropagation();
          }
          $items.removeClass('selected');
          $this.parent().addClass('selected');
          $htab.find('>div').hide().eq($items.index($this.parent())).show();
      }).eq(0).trigger('mdn:click');
  });

  /*
  Adds a context menu to edit page or view history
  if right-click on a link it will edit/view history on the links href.
  */
  $('body[contextmenu=edit-history-menu]').mozContextMenu(function(target, $contextMenu) {
      var $menuitems = $contextMenu.find('menuitem');
      $menuitems.removeAttr('disabled');

      // if target is an anchor other than MDN
      if(target.hostname && target.hostname !== location.hostname) {
        $menuitems.attr('disabled', true);
      }

      $contextMenu.on('click', function(e) {
        location.href = (target.href || location.href) + $(e.target).data('action');
      });
  });

  /*
    Stack overflow search form, used for dev program

    ex: http://stackoverflow.com/search?q=[firefox]+or+[firefox-os]+or+[html5-apps]+foobar
  */
  $('.stack-form').html('<form action="http://stackoverflow.com/search"><i class="stack-icon" aria-hidden="true"></i><label for="stack-search" class="offscreen">' + gettext('Search Stack Overflow') + '</label><input id="stack-search" placeholder="' + gettext('Search Stack Overflow') + '" /><button type="submit" class="offscreen">Submit Search</button></form>').find('form').on('submit', function(e) {
    e.preventDefault();

    var value = $(this).find('#stack-search').val();

    if(value != '') {
      win.location = 'http://stackoverflow.com/search?q=[firefox]+or+[firefox-os]+or+[html5-apps]+' + value;
    }
  });

  /*
    jQuery extensions used within the wiki.
  */
  $.extend({
    // Currently used within CKEDitor YouTube plugin
    parseQuerystring: function(str){
      var nvpair = {};
      var qs = (str || window.location.search).replace('?', '');
      var pairs = qs.split('&');

      $.each(pairs, function(i, v){
        var pair = v.split('=');
        nvpair[pair[0]] = pair[1];
      });

      return nvpair;
    },
    // Used within the wiki new/move pages
    slugifyString: function(str, allowSlash) {
      var regex = new RegExp('[\?\&\"\'\#\*\$' + (allowSlash ? '' : '\/') + ' +?]', 'g');
      // Remove anything from the slug that could cause big problems
      return str.replace(regex, '_')
        // "$" is used for verb delimiter in URLs
        .replace(/\$/g, '')
        // Don't allow "_____" mess
        .replace(/\_+/g, '_');
    }
  });


  function debounce(func, wait, immediate) {
    var timeout;
    return function() {
      var context = this, args = arguments;
      var later = function() {
        timeout = null;
        if (!immediate) func.apply(context, args);
      };
      var callNow = immediate && !timeout;
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
      if (callNow) func.apply(context, args);
    };
  }

})(window, document, jQuery);
