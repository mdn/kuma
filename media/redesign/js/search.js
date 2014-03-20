(function($) {
  'use strict';
  /*
    Set up the "from search" buttons if user came from search
  */
  var fromSearchNav = $('.from-search-navigate');
  if(fromSearchNav.length) {
    var fromSearchList = $('.from-search-toc');
    var ga = window._gaq || [];
    fromSearchNav.mozMenu({
      submenu: fromSearchList,
      brickOnClick: true,
      onOpen: function(){
        ga.push(['_trackEvent',
                 'Search doc navigator',
                 'Open on hover']);
      },
      onClose: function(){
        ga.push(['_trackEvent',
                 'Search doc navigator',
                 'Close on blur']);
      }
    });
    fromSearchList.find('ol').mozKeyboardNav();
  }

  function mozSearchStorage(options) {
    var prefix = 'mdn.search';
    var keys = ['key', 'data'];

    var getKey = function(name) {
      return prefix + '.' + name;
    }

    return {
      flush: function() {
        var self = this;
        $.each(keys, function(index, key) {
          self.removeItem(key);
        });
      },
      serialize: function(value) {
        return JSON.stringify(value);
      },
      deserialize: function(value) {
        if (typeof value != 'string') {
          return undefined;
        }
        try {
          return JSON.parse(value);
        } catch(e) {
          return value || undefined;
        }
      },
      getItem: function(key) {
        return this.deserialize(sessionStorage.getItem(getKey(key)));
      },
      setItem: function(key, value) {
        return sessionStorage.setItem(getKey(key), this.serialize(value));
      },
      removeItem: function(key) {
        return sessionStorage.removeItem(getKey(key));
      }
    };
  }
  var storage = mozSearchStorage();

  if($('body').hasClass('search-navigator-flush')) {
    storage.flush();
  }

  $.fn.mozSearchResults = function(url, ga) {
    var next_doc;
    var prev_doc;
    var data;
    var url = url;
    var key = storage.getItem('key');

    var populate = function(data) {
      // setting the main search input with the storey query
      if (data !== null && typeof data.query != 'undefined') {
        $('#main-q').val(data.query);
      }

      // first walk the loaded documents
      $.each(data.documents, function(index, doc) {
        var link = $('<a>', {
          text: doc.title,
          href: doc.url,
          on: {
            click: function() {
              ga.push(['_trackEvent',
                       'Search doc navigator',
                       'Click',
                       $(this).attr('href'),
                       doc.id]);
            }
          }
        });

        if (doc.slug === $('body').data('slug')) {
          link.addClass('current');
          // see if we can find the next page in the loaded documents
          next_doc = data.documents[index+1];
          if (typeof next_doc != 'undefined') {
            // and set the href of the next page anchor, make it visible, too
            $('.from-search-next').each(function() {
              $(this).attr('href', next_doc.url)
                     .on('click', function() {
                        ga.push(['_trackEvent',
                                 'Search doc navigator',
                                 'Click next',
                                 next_doc.url,
                                 next_doc.id]);
                     })
                     .parent()
                     .show();
            });
          }
          // do the same for the previous page link
          prev_doc = data.documents[index-1];
          if (typeof prev_doc != 'undefined') {
            $('.from-search-previous').each(function() {
              $(this).attr('href', prev_doc.url)
                     .on('click', function() {
                        ga.push(['_trackEvent',
                                 'Search doc navigator',
                                 'Click previous',
                                 prev_doc.url,
                                 prev_doc.id]);
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

    if (url === '') {
      if (key === null) {
        return this;
      } else {
        url = key;
      }
    } else {
      storage.setItem('key', url);
    }

    data = storage.getItem('data');
    if (typeof data == 'undefined') {
      $.ajax({
        url: url,
        dataType: 'json',
        success: function(data) {
          storage.setItem('data', data);
          populate(data);
        },
        error: function(xhr, status, err) {
          console.error(url, status, err.toString());
        }
      });
    } else {
      populate(data);
    }
    return this;
  };

  $('.search-results-topics').on('change', 'input', function(event) {
    $('#search-form').submit();
    $(this).parents('fieldset').attr('disabled', 'disabled');
  });

})(jQuery);
