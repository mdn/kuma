/*
 * Taken from Django's contrib/admin/media/js folder, thanks Django!
 * Copyright Django and licensed under BSD, please see django/LICENSE for
 * license details.
 * Modified slightly to handle fallback to full title if slug is empty.
 * Also modified to only trigger onchange.
 * Also modified to catch illegal slug characters
 */
(function($) {
    $.fn.prepopulate = function(dependencies, maxLength) {
        /*
            Depends on urlify.js
            Populates a selected field with the values of the dependent fields,
            URLifies and shortens the string.
            dependencies - selected jQuery object of dependent fields
            maxLength - maximum length of the URLify'd string
        */
        return this.each(function() {
            var $field = $(this);

            $field.data("_changed", false);
            $field.change(function() {
                $field.data("_changed", true);
            });

            var populate = function () {
                // Bail if the fields value has changed
                if ($field.data("_changed") == true) return;

                var values = [], field_val, field_val_raw;
                dependencies.each(function() {
                    if ($(this).val().length > 0) {
                        values.push($(this).val());
                    }
                });

                s = values.join(" ");
                
                // Remove anything from the slug that could cause big problems
                s = s.replace(/[\?\&\#\*\$\/ +?]/g, "_");

                // "$" is used for verb delimiter in URLs
                s = s.replace(/\$/g, ""); 

                // Don't allow "_____" mess
                s = s.replace(/\_+/g, "_");

                // trim to first num_chars chars
                s = s.substring(0, maxLength);

                $field.val(s);
            };
            
            dependencies.keyup(populate).change(populate).focus(populate);
        });
    };
})(jQuery);
