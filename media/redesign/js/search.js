
(function($) {
  // remove query paramters from the given URL. it probably sucks
  var remove_qs = function(url) {
    if (url.indexOf('?') !== -1) {
      return url.split('?')[0];
    } else {
      return url;
    }
  };

  var ga = function () {
    if (window._gaq && typeof window._gaq.push === 'function') {
      return window._gaq;
    } else {
      return [];
    }
  };

  var parentSelector = '.search-pane';
  $(parentSelector + ' .close').on('click', function(e) {
    e.preventDefault();
    $('#search-results-close-container').addClass('closed');
  });

  /*
    Set up the "from search" buttons if user came from search
  */
  var fromSearchNav = $('.from-search-navigate');
  if(fromSearchNav.length) {
    var fromSearchList = $('.from-search-toc');
    fromSearchNav.mozMenu({
      submenu: fromSearchList,
      brickOnClick: true,
      onOpen: function(){
        ga().push(['_trackEvent',
                 'Search doc navigator',
                 'Open on hover']);
      },
      onClose: function(){
        ga().push(['_trackEvent',
                 'Search doc navigator',
                 'Close on blur']);
      }
    });
    fromSearchList.find('ol').mozKeyboardNav();
  }

  var more = $('.search-results-more');
  more.find('.view-all').on('click', function(e) {
    e.preventDefault();
    var hiddenClass = 'closed';
    var parent = $(this).closest(parentSelector);
    parent.find('.' + hiddenClass).removeClass(hiddenClass);
    parent.find('.pager').removeClass('hidden');
    more.removeClass('with-view-all');
  });

  // a small wrapper around store.js to be able to set an expiration
  var searchStore = {
    set: function(key, val, exp) {
      store.set(key, {
        val:val,
        exp:exp * 1000,
        time:new Date().getTime()
      });
    },
    get: function(key) {
      var payload = store.get(key);
      if (!payload) {
        return null;
      }
      if (searchStore.expired(payload)) {
        return null;
      }
      return payload.val;
    },
    expired: function(payload) {
      return new Date().getTime() - payload.time > payload.exp;
    },
    cleanup: function() {
      store.forEach(function(key, payload) {
        if (payload && searchStore.expired(payload)) {
          store.remove(key);
        }
      });
    }
  };
  var prefix = 'mdn.search.';
  var state = history.state;
  var timeout = 86400;  // in seconds
  var clean_window_location = remove_qs(window.location.href);
  var current_docid = $('body').data('docid');

  // Function to store search result documents in local storage
  $.fn.mozSearchStore = function(key) {
    var documents = [];
    if (key === '') {
      return this;
    }

    // removing stale entries (stored docs that have expired, see timeout above)
    searchStore.cleanup();

    if (store.enabled) {
      return this.each(function() {
        // first look for docs and put them in an array
        var link = $(this),
        href = link.attr("href"),
        title = link.text(),
        docid = link.data("docid"),
        slug = link.data("slug"),
        query = $('#search-q').val();
        documents.push({
          title: title,
          docid: docid,
          slug: slug,
          url: href,
          query: query
        });
      }).promise().done(function() {
        // then create a payload to be stored and then store it with a timeout
        var payload = {
          documents: documents,
          next_page: null,
          previous_page: null
        };
        searchStore.set(prefix + key, payload, timeout);
      });
    }
  };

  $.fn.mozSearchResults = function(key) {
    var next_doc,
        prev_doc,
        payload = searchStore.get(prefix + key);

    if (key === '') {
      return this;
    }

    // removing stale entries again
    searchStore.cleanup();

    if (payload === null) {
      // if no payload was found and there is a ref in the URL, remove it
      if (window.location.search.indexOf("search=") !== -1) {
        history.replaceState(state, window.document.title, clean_window_location);
        // record the removal of a stale ?search= parameter URL
        ga().push(['_trackEvent',
                 'Search doc navigator',
                 'Remove stale parameters on load',
                 '',
                 current_docid]);
      }
    } else {
      // first walk the loaded documents
      $.each(payload.documents, function(index, doc) {
        var ref = '?search=' + key;
        var link = $('<a>', {
          text: doc.title,
          href: doc.url + ref,
          on: {
            click: function() {
              ga().push(['_trackEvent',
                       'Search doc navigator',
                       'Click',
                       remove_qs($(this).attr('href')),
                       doc.docid]);
            }
          }
        });

        if (doc.slug === $('body').data('slug')) {
          // setting the main search input with the storey query
          if (typeof doc.query != 'undefined') {
            $('#main-q').val(doc.query);
          }
          link.addClass('current');
          // appending the current search ref to the URL to make it copy/paste-able
          history.replaceState(state, window.document.title, doc.url + ref);
          // see if we can find the next page in the loaded documents
          next_doc = payload.documents[index+1];
          if (typeof next_doc != 'undefined') {
            // and set the href of the next page anchor, make it visible, too
            $('.from-search-next').each(function() {
              $(this).attr('href', next_doc.url + ref)
                     .click(function() {
                        ga().push(['_trackEvent',
                                 'Search doc navigator',
                                 'Click next',
                                 next_doc.url,
                                 next_doc.docid]);
                     })
                     .parent()
                     .show();
            });
          }
          // do the same for the previous page link
          prev_doc = payload.documents[index-1];
          if (typeof prev_doc != 'undefined') {
            $('.from-search-previous').each(function() {
              $(this).attr('href', prev_doc.url + ref)
                     .click(function() {
                        ga().push(['_trackEvent',
                                 'Search doc navigator',
                                 'Click previous',
                                 prev_doc.url,
                                 prev_doc.docid]);
                     })
                     .parent()
                     .addClass('from-search-spacer') // also add a spacer
                     .show();
            });
          }
        }
        var list_item = $('<li></li>').append(link);
        $('.from-search-toc ol').append(list_item);
      });
    }
    // return **this**
    return this;
  };
})(jQuery);
