(function($) {
  var parentSelector = '.search-pane';
    $(parentSelector + ' .close').on('click', function(e) {
      e.preventDefault();
      $('#search-results-close-container').addClass('closed');
    });

    var $more = $('.search-results-more');
    $more.find('.view-all').on('click', function(e) {
      e.preventDefault();
      var hiddenClass = 'closed';
      var $parent = $(this).closest(parentSelector);
      $parent.find('.' + hiddenClass).removeClass(hiddenClass);
      $parent.find('.pager').removeClass('hidden');
      $more.removeClass('with-view-all');
    });

  $('#search-filter').change(function() {
    var search_input = $('#search-q');
    var search_value = search_input.val();
    $(this).find('option:selected').each(function() {
      var selected_value = $(this).val();
      if (search_value.search(selected_value) == -1) {
        search_input.val(search_value + ' #' + selected_value);
      }
    });
  })
  function equal(a, b) {
      if (a === b) return true;
      if (a === undefined || b === undefined) return false;
      if (a === null || b === null) return false;
      // Check whether 'a' or 'b' is a string (primitive or object).
      // The concatenation of an empty string (+'') converts its argument to a string's primitive.
      if (a.constructor === String) return a+'' === b+''; // a+'' - in case 'a' is a String object
      if (b.constructor === String) return b+'' === a+''; // b+'' - in case 'b' is a String object
      return false;
  }

  $('#search-q').select2({
    tags: search_filters, // a global object
    width: 'element',
    multiple: true,
    separator: ' ',
    dropdownAutoWidth: true,
    openOnEnter: false,
    selectOnBlur: false,
    minimumInputLength: 1,  // that'll use the formatInputTooShort below
    createSearchChoice: function(term, data) {
      if ($(data).filter(function() {return this.text.localeCompare(term) === 0}).length === 0) {
        return {id:term, text:term};
      }
    },
    initSelection: function (element, callback) {
      // this correctly splits the inputs values and gets the labels
      // of the selected items from the global search filter list
      var data = [];
      $(element.val().split(' ')).each(function () {
          var obj = { id: this, text: this };
          $(search_filters).each(function() {
            if (equal(this.id, obj.id)) { obj = this; return false; } });
          data.push(obj);
        });
      callback(data);
    },
    formatInputTooShort: function (input, min) {
      return "Please start typing to enter a query or select a search filter";
    },
    formatSelectionCssClass: function(data, container) {
      var class_name = undefined;
      $(search_filters).each(function() {
        if (equal(this.id, data.id)) {
          // this give the selected a different css class
          class_name = 'filter';
          return false;
        }
      });
      return class_name;
    }
  });

})(jQuery);