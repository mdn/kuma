(function() {
	
	// List of languages we'll allow syntax highlighting for
	var supportedBrushes = [
		{ name: "Bash", brush: "bash" },
		{ name: "C/C++", brush: "cpp" },
		{ name: "CSS", brush: "css" },
		{ name: "HTML", brush: "html" },
		{ name: "Java", brush: "java" },
		{ name: "JavaScript", brush: "js" },
		{ name: "JSON", brush: "json" },
		{ name: "PHP", brush: "php" },
		{ name: "Python", brush: "python" },
		{ name: "SQL", brush: "sql" },
		{ name: "XML", brush: "xml" }
	];
	
	// Create the meat of the SyntaxHighlighter
	CKEDITOR.plugins.add("mdn-syntaxhighlighter", {
		// Need the selection plugin to handle the PRE element and its text
		requires: ["selection", "combobutton"],
		init: function(editor) {

			// Add the button to the syntax highlighter
			var title = gettext("Syntax Highlighter");
			editor.ui.addComboButton("mdn-syntaxhighlighter", {
				className: "cke_syntaxhighlighter",
				label: title,
				title: title,
				iconOffset: 1,
				icon: editor.skinPath + "icons.png",
				panel: {
					multiSelect: false,
					css : editor.skin.editor.css.concat(editor.config.contentsCss),
					attributes: { "aria-label" : gettext("Syntax Highlighter") }
				},
				// Upon initialization, build the combo and populate with languages
				init: function() {
					this.add("none", gettext("No Highlight"), "none");
					
					// Add languages to the box
					for(var x = 0; x < supportedBrushes.length; x++) {
						this.add(supportedBrushes[x].brush, supportedBrushes[x].name, supportedBrushes[x].brush);
					}
					
					// Commit list with all items added
					this.commit();
				},
				onClick: function(value) {
					// Set the selected class, focus on the editor
					var klass = value && value != "none" ? "brush: " + value : "",
						selection = editor.getSelection();

					// If there's a selection, and it's not a PRE, attempt to force?
					if(CKEDITOR.env.ie || (selection && selection.getStartElement().$.tagName != "PRE")) {;
						editor.execCommand("mdn-buttons-pre");
						selection = editor.getSelection();
					}
					
					if(selection) {
						selection.getStartElement().$.className = klass;
					}
					else if(this.lastPre) { // Internet Explorer forces us to use this instead
						try {
							this.lastPre.className = klass;
						}
						catch(e){}
					}
					
					// Focus back on the editor:
					editor.focus();
				},
				
				onRender: function() {
					// When the selection changes, update my state so only PRE elements can be chosen
					var self = this;
					editor.on("selectionChange", function(event) {
						var state = CKEDITOR.TRISTATE_DISABLED,
							element = event.data.path.block.$;
							
						if(element.tagName == "PRE") {
							state = CKEDITOR.TRISTATE_OFF;
							self.setValue(getBrushFromClassName(element));
							if(CKEDITOR.env.ie) self.lastPre = element; // IE-Specific
						}
						
						//self.setState(state);
					});
				},
				onOpen: function() {
					
					// If IE, focus back on the editor, because the selection is incorrect otherwise :(
					if(CKEDITOR.env.ie) editor.focus();
					
					var selection = editor.getSelection();
					
					// If no selection, close out
					if(!selection) {
						this._.panel.hide();
						this.onClose();
						return;
					}
					
					// Unmark any preselected value
					this.showAll();
					this.unmarkAll();
					
					// Mark the existing or "none" item
					var toShow = getBrushFromClassName(selection.getStartElement().$);
					this.mark(toShow);
					this._.list.focus(toShow);
				}
			});
		}
	});
	
	// Parses out the brush from a CSS className
	function getBrushFromClassName(pre) {
		var className = pre.className,
			brush = "none",
			brushMatch, split;
			
		if(className) {
			brushMatch = className.match(/brush\:(.*?);?$/);
			if(brushMatch != null) {
				split = brushMatch[1].split(";");
				brush = split[0].replace(/^\s+|\s+$/g, "");
			}
		}

		return brush;
	}
	
})();
