/*
 * tags.js
 * Scripts to support tagging.
 */

(function($){

    // Initialize tagging features.
    function init() {
        initVocab();
        initTagAdding();  // first because it visibly dims the Add button
        initAutoComplete();
        initTagRemoval();
    }

    // Parse the tag vocab out of the embedded JSON and store it on an attr on
    // the .tags block surrounding each set of add and remove forms.
    function initVocab() {
        $("div.tags[data-tag-vocab-json]").each(
            function(index) {
                var $tagContainer = $(this);
                var parsedVocab = $.parseJSON($tagContainer.attr("data-tag-vocab-json"));
                $tagContainer[0].tagVocab = parsedVocab;
            }
        );
    }

    // Attach an autocomplete widget to each input.autocomplete-tags. Get
    // completion data from the data-tag-vocab attr on the nearest div.tags
    // object outside the input.
    function initAutoComplete() {
        // Return a function() that sets the enabledness of the Add button appropriately.
        function makeButtonTender($addForm) {
            var $adder = $addForm.find("input.adder"),
                $input = $addForm.find("input[name=tag-name]"),
                vocab = $addForm.closest("div.tags")[0].tagVocab,
                $tagList = formToTagList($addForm);

            // Like inArray but for strings only and case-insensitive.
            // TODO: Think about sorting and using binary search.
            function inArrayCaseInsensitive(str, ary) {
                var matcher = new RegExp("^" + escapeRegex(str) + "$", "i");
                for (var i = 0; i < ary.length; i++)
                    if (matcher.test(ary[i]))
                        return i;
                return -1;
            }

            // Enable Add button if the entered tag is in the vocabulary. Else, disable it.
            function tendAddButton() {
                // TODO: Optimization: use the calculation already done for the
                // autocomplete menu to limit the search space.
                var tagName = $.trim($input.val()),
                    inVocab = inArrayCaseInsensitive(tagName, vocab) != -1;
                $adder.attr("disabled", !inVocab || tagIsOnscreen(tagName, $tagList));
            }

            return tendAddButton;
        }


        // Case-insensitive array filter
        // Ripped off from jquery.ui.autocomplete.js. Why can't I get at these
        // via, e.g., $.ui.autocomplete.filter?

        function escapeRegex( value ) {
            return value.replace( /([\^\$\(\)\[\]\{\}\*\.\+\?\|\\])/gi, "\\$1" );
        }

        function filter(array, term) {
            var matcher = new RegExp( escapeRegex(term), "i" );
            return $.grep( array, function(value) {
                return matcher.test( value.label || value.value || value );
            });
        }


        // Return an autocomplete vocab source callback that produces the
        // full vocab minus the already applied tags.
        //
        // $tags -- a .tags element containing a vocab in its tagVocab attr
        function makeVocabCallback($tags) {
            var vocab = $tags[0].tagVocab,
                $tagList = $tags.find("ul.tag-list");

            function vocabCallback(request, response) {
                var appliedTags = getAppliedTags($tagList),
                    vocabMinusApplied = $.grep(vocab,
                        function(e, i) {
                            return $.inArray(e, appliedTags) == -1;
                        }
                    );
                response(filter(vocabMinusApplied, request.term));
            }

            return vocabCallback;
        }

        $("input.autocomplete-tags").each(
            function(index) {
                var $input = $(this);
                $input.autocomplete({
                    source: makeVocabCallback($input.closest("div.tags")),
                    delay: 0,
                    minLength: 1  // Adjust with size of vocab.
                                  // Starting small for discoverability.
                });

                tender = makeButtonTender($input.closest("form"));
                // keyup isn't triggered by pasting into the field. FWIW,
                // Google Suggest also punts on this.
                $input.keyup(tender);
                $input.bind("autocompletechange", tender);
            }
        );
    }

    function initTagRemoval() {
        // Attach an async tag-removal function to each clickable "x":
        $(".tag").each(
            function(index) {
                attachRemoverHandlerTo($(this));
            }
        );

        // Prevent the form from submitting so our AJAX handler is always called:
        $("form.remove-tag-form").submit(function() { return false; });
    }

    // Attach onclick removal handlers to every .remove element in $tag.
    function attachRemoverHandlerTo($tag) {
        $tag.find(".remover").click(
            function() {
                var $remover = $(this),
                    $tag = $remover.closest(".tag"),
                    tagName = $tag.find(".tag-name").text();
                $tag.addClass("removing");  // Dim for immediate feedback.
                $.ajax({
                    type: 'POST',
                    url: $remover.closest("form.remove-tag-form").attr("data-action-async"),
                    data: {name: tagName},
                    success: function makeTagDisappear() {
                           $tag.remove();
                           // TODO: Update Add button state in case a tag is
                           // removed whose name is presently in the Add field.
                        },
                    error: function makeTagReappear() {
                           $tag.removeClass("removing");
                        }
                });
            }
        );
    }

    function initTagAdding() {
        // Dim all Add buttons. We'll undim them upon valid input.
        $("form.add-tag-form input.adder:enabled").attr("disabled", true);

        // Attach an async submit handler to all form.add-tag-form.
        $("form.add-tag-form").each(
            function initOneForm(index) {
                var $form = $(this);
                $form.submit(
                    function() {
                        var $input = $form.find("input[name=tag-name]"),
                            tagName = $input.val();

                        function makeTagShowUp(data) {
                            var $tagList = formToTagList($form),
                                canonicalName = data.canonicalName;

                            if (!(tagIsOnscreen(canonicalName, $tagList))) {
                                var $tag = $("<li class='tag'><a class='tag-name' href='#'></a><input type='submit' value='&#x2716;' class='remover' /></li> ");
                                $tag.find(".tag-name").text(canonicalName);
                                $tag.find("input").attr("name", "remove-tag-" + canonicalName);
                                $tagList.append($tag);
                                attachRemoverHandlerTo($tag);
                            }
                        }

                        $.post($form.attr("data-action-async"),
                               {'tag-name': tagName},
                               makeTagShowUp
                        );
                        // TODO: Give immediate feedback [bug 576681], and add
                        // error callback.
                        $input.val("");
                        $form.find("input.adder").attr("disabled", true);
                        return false;
                    }
                );
            }
        );
    }

    // Given the tag-adding form, return the tag list in the corresponding
    // tag-removing form.
    function formToTagList($addForm) {
        return $addForm.closest("div.tags").find("ul.tag-list");
    }

    // Return the tags already applied to an object.
    // Specifically, given a .tag-list, return an array of tag names in it.
    function getAppliedTags($tagList) {
        var tagNames = [];
        $tagList.find(".tag .tag-name").each(
            function(i, e) {
                tagNames.push(e.text);
            }
        );
        return tagNames;
    }

    // Return whether the tag of the given name is in the visible list.
    function tagIsOnscreen(tagName, $tagList) {
        return $.inArray(tagName, getAppliedTags($tagList)) != -1;
    }

    $(document).ready(init);

}(jQuery));
