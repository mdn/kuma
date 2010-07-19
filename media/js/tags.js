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
                $tagContainer.data("tagVocab", parsedVocab);
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
                canCreateTags = $addForm.attr("data-can-create-tags") !== undefined,
                $input = $addForm.find("input[name=tag-name]"),
                vocab = $addForm.closest("div.tags").data("tagVocab"),
                $tagList = formToTagList($addForm);

            // Enable Add button if the entered tag is in the vocabulary. Else,
            // disable it. If the user has the can_add_tag permission, let him
            // add whatever he wants, as long as it has some non-whitespace in
            // it.
            function tendAddButton() {
                // TODO: Optimization: use the calculation already done for the
                // autocomplete menu to limit the search space.
                var tagName = $.trim($input.val()),
                    inVocab = inArrayCaseInsensitive(tagName, vocab) != -1,
                    isOnscreen = tagIsOnscreen(tagName, $tagList);
                $adder.attr("disabled", !tagName.length || isOnscreen ||
                                        (!canCreateTags && !inVocab));
            }

            return tendAddButton;
        }

        // Return an autocomplete vocab source callback that produces the
        // full vocab minus the already applied tags.
        //
        // $tags -- a .tags element containing a vocab in its tagVocab attr
        function makeVocabCallback($tags) {
            var vocab = $tags.data("tagVocab"),
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
                })
                // Work around jQuery UI bug http://dev.jqueryui.com/ticket/5275:
                .data("autocomplete")._renderItem = function(ul, item) {
                        var a = $("<a></a>").text(item.label);
                        return $("<li></li>")
                            .data("item.autocomplete", item)
                            .append(a)
                            .appendTo(ul);
                    };

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
                $tag.addClass("in-progress");  // Dim for immediate feedback.
                $.ajax({
                    type: "POST",
                    url: $remover.closest("form.remove-tag-form").attr("data-action-async"),
                    data: {name: tagName},
                    success: function makeTagDisappear() {
                           $tag.remove();
                           // TODO: Update Add button state in case a tag is
                           // removed whose name is presently in the Add field.
                        },
                    error: function makeTagReappear() {
                           $tag.removeClass("in-progress");
                        }
                });
                return false;
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
                            tagName = $input.val(),
                            $tag = putTagOnscreen(tagName);

                        // Add a ghostly tag to the onscreen list and return the tag element.
                        // If the tag was already onscreen, do nothing and return null.
                        function putTagOnscreen(tagName) {
                            var $tagList = formToTagList($form);

                            if (!(tagIsOnscreen(tagName, $tagList))) {
                                var $tag = $("<li class='tag in-progress'><a class='tag-name' href='#'></a><input type='submit' value='&#x2716;' class='remover' /></li> ");
                                $tag.find(".tag-name").text(tagName);
                                $tag.find("input").attr("name", "remove-tag-" + tagName);
                                $tagList.append($tag);
                                return $tag;
                            }
                        }
                        
                        $.ajax({
                            type: "POST",
                            url: $form.attr("data-action-async"),
                            data: {"tag-name": tagName},
                            success: function solidifyTag(data) {
                                         // Make an onscreen tag non-ghostly,
                                         // canonicalize its name,
                                         // activate its remover button, and
                                         // add it to the local vocab.
                                         var vocab = $form.closest("div.tags").data("tagVocab"),
                                             canonicalName = data.canonicalName;
                                         if (inArrayCaseInsensitive(canonicalName, vocab) == -1)
                                             vocab.push(canonicalName);
                                         $tag.find(".tag-name").text(canonicalName);
                                         $tag.removeClass("in-progress");
                                         attachRemoverHandlerTo($tag);
                                     },
                            error: function disintegrateTag(data) {
                                       $tag.remove();
                                   }
                        });
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


    // Like inArray but for strings only and case-insensitive.
    // TODO: Think about sorting and using binary search.
    function inArrayCaseInsensitive(str, ary) {
        var matcher = new RegExp("^" + escapeRegex(str) + "$", "i");
        for (var i = 0; i < ary.length; i++)
            if (matcher.test(ary[i]))
                return i;
        return -1;
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
    // The in-the-process-of-being-added-or-removed state is considered onscreen.
    function tagIsOnscreen(tagName, $tagList) {
        return inArrayCaseInsensitive(tagName, getAppliedTags($tagList)) != -1;
    }

    $(document).ready(init);

}(jQuery));
