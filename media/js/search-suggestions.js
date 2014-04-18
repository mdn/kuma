$(document).ready(function(){
    'use strict';
    var filtersData = window.mdn.searchFilters;

    var $search = $('.search-wrapper');
    var $searchFilters = $search.find('.filters');
    var $searchInput = $search.find('input');
    var $searchForm = $search.find('form');
    var $suggestions = $('form.search .suggestions');
    var BASE_SEARCH_URL = $('form.search').attr('action');

    var previousValue = $searchInput.val();

    var fnSuggestions = {
      'prepareInput':function(){
          $searchInput.attr('size', '15');
      },
      'parse':function(s){
          var matches = s.match(/^(#\S+)\s+|\s(#\S+)\s+/);
          return matches ? matches[1] || matches[2] : matches;
      },
      'open': function(){
        $suggestions.attr('data-hidden', 'false');
        $suggestions.slideDown();
      },
      'close': function(){
        $suggestions.attr('data-hidden', 'true');
        $suggestions.slideUp();
      },
      'populate': function(){
        if($suggestions.attr('data-hidden') == 'false')
        {
            var fs = $searchInput.val().match(/#(\S+)/) || [];
            this.recoverTopics(fs[1] || '');
            $('.search').mozKeyboardNav();
        }
      },
      'addFilter':function(f){ // f is a topic with the # ('#javascript', '#advanced')
        var filter = $('<span></span>')
            .addClass('topic button')
            .attr('data-topic', f.slice('#'.length))
            .text(f)
            .appendTo($searchFilters);

        $('<button></button>')
            .addClass('close')
            .attr('type', 'button')
            .html('<i aria-hidden="true" class="icon-remove"></i>')
            .on('click', function(){
                $(filter).remove();
            })
            .appendTo(filter);
      },
      'parseAndAddFilters': function(){
          var toParse = $searchInput.val();
          var filter = true;
          var filters = [];
          var self = this;
          while(filter){
              filter = self.parse(toParse);
              if(filter){
                  filters.push(filter);
                  toParse = toParse.replace(filter, '').trim();
              }
          }

          if(filters.length >= 1){
              filters.forEach(function(entry){
                self.addFilter(entry)
              });
              self.close();
          }

          $searchInput.val(toParse);
          $searchInput.attr('size', $searchInput.val().length < 15 ? 15 : $searchInput.val().length);
      },
      'removeAccents': function(srt) {
          var map={'À':'A','Á':'A','Â':'A','Ã':'A','Ä':'A','Å':'A','Æ':'AE','Ç':'C','È':'E','É':'E','Ê':'E','Ë':'E','Ì':'I','Í':'I','Î':'I','Ï':'I','Ð':'D','Ñ':'N','Ò':'O','Ó':'O','Ô':'O','Õ':'O','Ö':'O','Ø':'O','Ù':'U','Ú':'U','Û':'U','Ü':'U','Ý':'Y','ß':'s','à':'a','á':'a','â':'a','ã':'a','ä':'a','å':'a','æ':'ae','ç':'c','è':'e','é':'e','ê':'e','ë':'e','ì':'i','í':'i','î':'i','ï':'i','ñ':'n','ò':'o','ó':'o','ô':'o','õ':'o','ö':'o','ø':'o','ù':'u','ú':'u','û':'u','ü':'u','ý':'y','ÿ':'y','Ā':'A','ā':'a','Ă':'A','ă':'a','Ą':'A','ą':'a','Ć':'C','ć':'c','Ĉ':'C','ĉ':'c','Ċ':'C','ċ':'c','Č':'C','č':'c','Ď':'D','ď':'d','Đ':'D','đ':'d','Ē':'E','ē':'e','Ĕ':'E','ĕ':'e','Ė':'E','ė':'e','Ę':'E','ę':'e','Ě':'E','ě':'e','Ĝ':'G','ĝ':'g','Ğ':'G','ğ':'g','Ġ':'G','ġ':'g','Ģ':'G','ģ':'g','Ĥ':'H','ĥ':'h','Ħ':'H','ħ':'h','Ĩ':'I','ĩ':'i','Ī':'I','ī':'i','Ĭ':'I','ĭ':'i','Į':'I','į':'i','İ':'I','ı':'i','Ĳ':'IJ','ĳ':'ij','Ĵ':'J','ĵ':'j','Ķ':'K','ķ':'k','Ĺ':'L','ĺ':'l','Ļ':'L','ļ':'l','Ľ':'L','ľ':'l','Ŀ':'L','ŀ':'l','Ł':'L','ł':'l','Ń':'N','ń':'n','Ņ':'N','ņ':'n','Ň':'N','ň':'n','ŉ':'n','Ō':'O','ō':'o','Ŏ':'O','ŏ':'o','Ő':'O','ő':'o','Œ':'OE','œ':'oe','Ŕ':'R','ŕ':'r','Ŗ':'R','ŗ':'r','Ř':'R','ř':'r','Ś':'S','ś':'s','Ŝ':'S','ŝ':'s','Ş':'S','ş':'s','Š':'S','š':'s','Ţ':'T','ţ':'t','Ť':'T','ť':'t','Ŧ':'T','ŧ':'t','Ũ':'U','ũ':'u','Ū':'U','ū':'u','Ŭ':'U','ŭ':'u','Ů':'U','ů':'u','Ű':'U','ű':'u','Ų':'U','ų':'u','Ŵ':'W','ŵ':'w','Ŷ':'Y','ŷ':'y','Ÿ':'Y','Ź':'Z','ź':'z','Ż':'Z','ż':'z','Ž':'Z','ž':'z','ſ':'s','ƒ':'f','Ơ':'O','ơ':'o','Ư':'U','ư':'u','Ǎ':'A','ǎ':'a','Ǐ':'I','ǐ':'i','Ǒ':'O','ǒ':'o','Ǔ':'U','ǔ':'u','Ǖ':'U','ǖ':'u','Ǘ':'U','ǘ':'u','Ǚ':'U','ǚ':'u','Ǜ':'U','ǜ':'u','Ǻ':'A','ǻ':'a','Ǽ':'AE','ǽ':'ae','Ǿ':'O','ǿ':'o'};
          var valueResult='';
          for (var i=0;i<srt.length;i++) {
              var c=srt.charAt(i);
              valueResult+=map[c]||c;
          }
          return valueResult;
      },
      'recoverTopics': function(f){
          // clean suggestion div
          $suggestions.empty();
          var self = this;
          $.each(filtersData, function(index, group){
              var title = $('<strong>').text(group.name);
              var ul = document.createElement("UL");
              var show = false;
              $.each(group.filters, function(index, filter){
                  var slugNorm = filter.slug.toLowerCase();
                  var nameNorm = self.removeAccents(filter.name.toLowerCase());
                  if (!f || slugNorm.indexOf(self.removeAccents(f.toLowerCase())) != -1 || nameNorm.indexOf(self.removeAccents(f.toLowerCase())) != -1) {
                      var $li = $('<li></li>')
                                  .attr('data-slug', filter.slug)
                                  .addClass('sug');
                      var $a = $('<a></a>')
                                  .attr('class', 'search-ss')
                                  .attr('href', '#')
                                  .html(filter.name + ' <span>#' + filter.slug + '</span>')
                                  .appendTo($li)
                                  .on('click', function(e){
                                      e.preventDefault();
                                      self.addFilter('#'+filter.slug);
                                      $searchInput.val($searchInput.val().replace('#'+f,""));
                                      previousValue = $searchInput.val();
                                      $searchInput.attr('size', $searchInput.val().length < 15 ? 15 : $searchInput.val().length);
                                      $suggestions.attr('data-hidden', 'true');
                                      $suggestions.hide();
                                      $searchInput.focus();
                                  });
                      $(ul).append($li);
                      show = true;
                  }
              });
              if(show){
                  $suggestions.append(title);
                  $suggestions.append(ul);
              }
          });
      }
    };

    $search.on('click', function(){
        $searchInput.focus();
    });

    // Open Q : other events than input?
    $searchInput.on('input', function(e){

        $searchInput.attr('size', $searchInput.val().length < 15 ? 15 : $searchInput.val().length);
        fnSuggestions.parseAndAddFilters();

        // find out if there is a difference of exactly one # between input.value and previousValue
        // Current algorithm is very simple. Must be improved in the future
        // Currently consider only the last character
        if($searchInput.val().length - previousValue.length === 1 &&
           $searchInput.val()[$searchInput.val().length -1] === '#')
        {
            fnSuggestions.open();
        }

        if(previousValue.length - $searchInput.val().length === 1 &&
           previousValue[previousValue.length -1] === '#')
        {
            fnSuggestions.close();
        }

        fnSuggestions.populate();

        previousValue = $searchInput.val();
    });

    $('.show-topics').on('click', function(e){
        e.preventDefault();
        if($suggestions.attr('data-hidden') == 'false') {
          fnSuggestions.close();
        }else{
          fnSuggestions.open();
          fnSuggestions.populate();
        }
    })

    $('form.search').on('submit', function(e){
        e.preventDefault();

        var topics = $.makeArray($('form.search .topic')).map(function(e){
            return encodeURIComponent($(e).attr('data-topic'));
        });
        var topicsString = topics
            .map(function(t){ return 'topic='+t; })
            .join('&');

        var q = encodeURIComponent($searchInput.val());

        var searchURL = BASE_SEARCH_URL + '?' +
            'q=' + q +
            '&' + topicsString;

        console.log('search URL', searchURL);
        location.href = searchURL;
    });

    fnSuggestions.prepareInput();
    // Show first time notification in the first visit
    if (typeof localStorage['first-visit'] === 'undefined') {
        var $closeButton = $('<button></button>')
            .addClass('close')
            .attr('type', 'button')
            .html('<i aria-hidden="true" class="icon-remove"></i>')
            .on('click', function(){
                $firstTimePop.remove();
            })
        var $firstTimePop = $('<div></div>')
            .addClass('notificaton-first-time')
            .append($search.data('ft-text'))
            .append($closeButton);

        $search.after($firstTimePop);
        localStorage['first-visit'] = 'nope';
    }
});