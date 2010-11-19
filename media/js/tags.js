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
            function() {
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
                $input = $addForm.find("input.autocomplete-tags"),
                $tagsDiv = $input.closest("div.tags"),
                canCreateTags = $tagsDiv.attr("data-can-create-tags") !== undefined,
                vocab = $tagsDiv.data("tagVocab"),
                $tagList = inputToTagList($input);

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
            function() {
                var $input = $(this),
                    tender = makeButtonTender($input.closest("form"));

                $input.autocomplete({
                    source: makeVocabCallback($input.closest("div.tags")),
                    delay: 0,
                    minLength: 1,  // Adjust with size of vocab.
                                   // Starting small for discoverability.
                    close: tender
                });
                
                // keyup isn't triggered by pasting into the field. FWIW,
                // Google Suggest also punts on this.
                $input.keyup(tender);
                $input.bind("autocompletechange", tender);
            }
        );
    }

    function initTagRemoval() {
        // Attach a tag-removal function to each clickable "x":
        $("div.tags").each(
            function() {
                var $div = $(this),
                    async = !$div.hasClass("tag-deferred");
                $div.find(".tag").each(
                    function() {
                        attachRemoverHandlerTo($(this), async);
                    }
                );
            }
        );

        // Prevent the form, if it exists, from submitting so our AJAX handler
        // is always called:
        $("form.remove-tag-form").submit(function() { return false; });
    }

    // Attach onclick removal handlers to every .remove element in $tag.
    function attachRemoverHandlerTo($tag, async) {
        $tag.find(".remover").click(
            function() {
                var $remover = $(this),
                    $tag = $remover.closest(".tag"),
                    tagName = $tag.find(".tag-name").text();

                function makeTagDisappear() {
                   $tag.remove();
                   // TODO: Update Add button state in case a tag is
                   // removed whose name is presently in the Add field.
                }

                if (async) {
                    $tag.addClass("in-progress");  // Dim for immediate feedback.
                    $.ajax({
                        type: "POST",
                        url: $remover.closest("form.remove-tag-form").attr("data-action-async"),
                        data: {name: tagName},
                        success: makeTagDisappear,
                        error: function makeTagReappear() {
                               $tag.removeClass("in-progress");
                            }
                    });
                } else
                    makeTagDisappear();
                return false;
            }
        );
    }

    // $container is either a form or a div.tags.
    function addTag($container, async) {
        var $input = $container.find("input.autocomplete-tags"),
            tagName = $input.val(),
            vocab = $input.closest("div.tags").data("tagVocab"),
            tagIndex = inArrayCaseInsensitive(tagName, vocab),
            $tag;

        // Add a (ghostly, if async) tag to the onscreen
        // list and return the tag element. If the tag was
        // already onscreen, do nothing and return null.
        function putTagOnscreen(tagName) {
            var $tagList = inputToTagList($input);
            if (!(tagIsOnscreen(tagName, $tagList))) {
                var $li = $("<li class='tag'><span class='tag-name' /><input type='submit' value='&#x2716;' class='remover' /></li> ");
                if (async)
                    $li.addClass("in-progress");
                else {
                    // Add hidden input to persist form state, and make the removal X work.
                    var $hidden = $("<input type='hidden' />");
                    $hidden.attr("value", tagName);
                    $hidden.attr("name", $input.attr("name"));
                    $li.prepend($hidden);
                    attachRemoverHandlerTo($li, false);
                }
                $li.find(".tag-name").text(tagName);
                $li.find("input.remover").attr("name", "remove-tag-" + tagName);
                $tagList.append($li);
                return $li;
            }
        }

        if (tagIndex == -1) {
            if (async)  // If we're operating wholly client side until Submit is clicked, it would be weird to pretend you've added to the server-side vocab.
                vocab.push(tagName);
        } else  // Canonicalize case.
            tagName = vocab[tagIndex];  // Canonicalize case.

        $tag = putTagOnscreen(tagName);

        if ($tag && async) {
            $.ajax({
                type: "POST",
                url: $container.attr("data-action-async"),
                data: {"tag-name": tagName},
                success: function solidifyTag(data) {
                             // Make an onscreen tag non-ghostly,
                             // canonicalize its name,
                             // activate its remover button, and
                             // add it to the local vocab.
                             var url = data.tagUrl,
                                 tagNameSpan = $tag.find(".tag-name");
                             tagNameSpan.replaceWith($("<a class='tag-name' />")
                                .attr("href", url)
                                .text(tagNameSpan.text()));
                             $tag.removeClass("in-progress");
                             attachRemoverHandlerTo($tag, true);
                         },
                error: function disintegrateTag(data) {
                           $tag.remove();
                       }
            });
        }

        // Clear the input field.
        $input.val("");
        $container.find("input.adder").attr("disabled", true);
        return false;
    }

    function initTagAdding() {
        // Dim all Add buttons. We'll undim them upon valid input.
        $("div.tags input.adder:enabled").attr("disabled", true);

        // Attach an async submit handler to all form.add-tag-immediately.
        $("form.add-tag-immediately").each(
            function initOneForm() {
                var $form = $(this);
                $form.submit(
                    function() {
                        return addTag($form, true);
                    }
                );
            }
        );

        // Attach a tag-appearing handler to all div.tag-deferred.
        $("div.tag-deferred").each(
            function initOneDiv() {
                var $div = $(this);
                $div.find("input.adder").click(
                    function() {
                        return addTag($div, false);
                    }
                );
            }
        );
    }

    // Given the tag-adding form, return the tag list in the corresponding
    // tag-removing form.
    function inputToTagList($input) {
        return $input.closest("div.tags").find("ul.tag-list");
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
    // (Tags in the process of being added or removed are considered applied.)
    function getAppliedTags($tagList) {
        var tagNames = [];
        $tagList.find(".tag .tag-name").each(
            function(i, e) {
                tagNames.push($(e).text());
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
