//
// User detail and edit view enhancements
//
(function ($) {
    'use strict';

    $(document).ready(function(){

        // word count
        $('.wordcount').each(function(i, el){

            var $el = $(el);
            var placeholder = $el.find('.counter');
            var limit = parseInt(placeholder.text(), 10);
            var currcount = 0;
            var field = $el.children('textarea');

            function updateWordCount() {
                var words = $.trim(field.val()).split(' ');
                var color = placeholder.parent().css('color');
                var invalidColor = '#900';
                var length;

                if(words[0] === ''){ words.length = 0; }
                currcount = limit - words.length;
                placeholder.text(currcount);

                length = words.length;

                if(length >= limit && color !== invalidColor) {
                    placeholder.parent().css('color', invalidColor);
                }
                else if(words.length < limit && color === invalidColor) {
                    placeholder.parent().css('color', '');
                }
            }

            updateWordCount();
            field.keypress(updateWordCount);
        });

        // Update "Other users", preventing "blank" submissions
        $('#users input').mozPlaceholder();
    });
})(jQuery);
