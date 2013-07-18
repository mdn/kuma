//
// Profile view and edit enhancements
//
(function () {

	var DEBOUNCE_DELAY = 25;

	// Translate multiple rapid calls to a function into a single call after a
	// short delay. Also serves to allow UI updates to complete due to yielding
	// the event loop.
	//
	// This seems to paper over some odd timing bugs where checkboxes aren't
	// detected, and certain events aren't caught.
	function debounce(orig_fn, delay) {
		delay = delay || DEBOUNCE_DELAY;
		return function () {
			var fn = arguments.callee;
			if (fn.debounce) { return; }
			fn.debounce = true;
			window.setTimeout(function () {
				orig_fn();
				fn.debounce = false;
			}, delay);
		};
	}

	// Rebuild the list of expertise tags and checkboxes.
	var rebuildExpertiseTaglist = debounce(function () {
		var taglist = $("#tags-expertise"),
			interests = $("#id_interests"),
			i_tags = interests.val().split(",");

		// Completely rebuild the list of expertise tags. Seems wasteful, but
		// the number of elements should be relatively tiny vs the code to do
		// it more surgically.
		taglist.empty();
		$.each(i_tags, function (idx, tag) {
			tag = $.trim(tag);
			if (INTEREST_SUGGESTIONS.indexOf(tag) == -1) return;

			taglist.append('<li class="tag-expert">' +
				'<label for="expert-' + idx + '">' +
				'<input type="checkbox" name="expert-' + idx + '" ' +
					'id="expert-'+idx+'" value="' + tag + '"> ' + tag +
				'</label></li>');
		});

		// Do this mutual update, so any checkboxes that have disappeared
		// also get removed from the field.
		updateTaglistFromField();
		updateFieldFromTaglist();
	});

	// Update the checked tags in expertise tag list from the text field
	var updateTaglistFromField = debounce(function () {
		var taglist = $("#tags-expertise"),
			expertise = $("#id_expertise"),
			eTags = expertise.val().split(",");

		$("#tags-expertise .tag-expert input[type=checkbox]").removeAttr("checked");
		$.each(eTags, function(idx, tag) {
			tag = $.trim(tag);
			$('#tags-expertise .tag-expert input[value="' + tag + '"]').attr("checked", "checked");
		});
	});

	// Update the expertise text field from checked boxes in tag list
	var updateFieldFromTaglist = debounce(function () {
		var tags = $("#tags-expertise .tag-expert input[type=checkbox]:checked")
			.map(function () { return $(this).val(); })
			.get().join(",");
		$("#id_expertise").val(tags);
	});

	$(document).ready(function(){

		// Convert interests text field into a tag-it widget
		$("#id_interests").hide()
			.after("<ul id='tagit-interests'></ul>")
			.change(rebuildExpertiseTaglist);
		$("#tagit-interests").tagit({
			availableTags: INTEREST_SUGGESTIONS,
			singleField: true,
			singleFieldNode: $("#id_interests"),
			onTagAdded: rebuildExpertiseTaglist,
			onTagRemoved: rebuildExpertiseTaglist,
			onTagClicked: rebuildExpertiseTaglist
		});

		// Convert the expertise text field into tag list with checkboxes sync'd to
		// interests
		$("#id_expertise").hide().after("<ul id='tags-expertise' class='taglist'></ul>");
		$("#tags-expertise").click(updateFieldFromTaglist);
		rebuildExpertiseTaglist();

		// word count
		$(".wordcount").each(function(i, el){

			var $el = $(el),
				placeholder = $el.find(".counter"),
				limit = parseInt(placeholder.text(), 10),
				currcount = 0,
				field = $el.children("textarea");

			function updateWordCount() {
				var words = $.trim(field.val()).split(" "),
					color = placeholder.parent().css("color"),
					length;

				if(words[0] == ""){ words.length = 0; }
				currcount = limit - words.length;
				placeholder.text(currcount);

				length = words.length;

				if(length >= limit && color != "#900" ) {
					placeholder.parent().css("color", "#900");
				}
				else if(words.length < limit && color == "#900") {
					placeholder.parent().css("color", "");
				}
			}
			
			updateWordCount();
			field.keypress(updateWordCount);
		});

		// Update "Other Profiles", preventing "blank" submissions
		$("#elsewhere input").mozPlaceholder();

	});
})();