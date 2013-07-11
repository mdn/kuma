CKEDITOR.plugins.add('mdn-keystrokes', {
	
	// Requires CKEditor's keystrokes
	requires: ['keystrokes', 'mdn-buttons'],
	
	// Initialize
	init: function(editor) {
		
		var keys = mdn.ckeditor.keys;

		editor.on('key', function(event) {
			event.stop();

			switch(event.data.keyCode) {
				
				/* Heading Tags */
				
				// Control - 2
				case keys.control2:
					editor.execCommand('mdn-buttons-h2');
					break;
					
				// Control - 3
				case keys.control3:
					editor.execCommand('mdn-buttons-h3');
					break;
					
				// Control - 4
				case keys.control4:
					editor.execCommand('mdn-buttons-h4');
					break;
					
				// Control - 5
				case keys.control5:
					editor.execCommand('mdn-buttons-h5');
					break;
					
				// Control - 6
				case keys.control6:
					editor.execCommand('mdn-buttons-h6');
					break;
					
				/* Link Dialog */
				case keys.controlK:
					editor.execCommand('link');
					break;
					
				/* Source Toggle */
				case keys.controlShiftO:
					editor.execCommand('source');
					break;
				
				// TAB:  Increases indent level if in indent mode, otherwise inserts two spaces as a tab.  Inside tables, this jumps to the next cell, or inserts a new row if there is no next cell.  If the cursor is currently in the page title or in a header, the cursor jumps to the next paragraph.
				case keys.shiftTab:
					tab(event, true);
					break;
				
				case keys.tab:
					tab(event);
					break;

				/* <code> Toggle */
				case keys.controlO:
					editor.execCommand('mdn-buttons-code');
					break;

				/* <pre> Toggle */
				case keys.controlP:
					event.cancel();
					editor.execCommand('mdn-buttons-pre');
					break;

				/* Save buttons */
				case keys.controlShiftS:
					editor.execCommand('mdn-buttons-save-exit');
					break;
				case keys.controlS:
					editor.execCommand('mdn-buttons-save');
					break;

				/* Toggle formats */
				case keys.controlShiftL:
					toggleBlock(event);
					break;

				/* Don't allow back/foward in WYSIWYG mode */
				case keys.back:
				case keys.forward:
					if(editor.mode != "source") {
						event.stop();
						event.cancel();
					}
			}
		});

		/* Toggle current block */
		function toggleBlock(event) {
			// The trick within this block is to exec the command 
			// that is currently selected to get back to "plain" state

			var editor = event.editor,
				on = CKEDITOR.TRISTATE_ON,
				bullettedlist = 'bulletedlist',
				numberedlist = 'numberedlist',
				commandName = numberedlist,
				count = 0,
				getState = function(c) {
					return editor.getCommand(c).state;
				},
				path,
				length,
				elements,
				name;

			if(getState(bullettedlist) != on) {
				commandName = bullettedlist
				if(getState(numberedlist) == on) {
					path = new CKEDITOR.dom.elementPath(editor.getSelection().getStartElement());
					commandName = numberedlist;
					elements = path.elements;
					length = elements.length;
					for(var x = 0 ; x < length; x++) {
						if(elements[x].is('ul', 'ol')) {
							count++;
						}
					}
					if(count > 1) {
						commandName = bullettedlist;
					}
				}
			}

			if (getState(commandName) != CKEDITOR.TRISTATE_DISABLED) {
				editor.execCommand(commandName);
				return true;
			}

			return false;
		}		

		/* Handles tab key presses */
		function tab(event, hasShift) {

			var editor = event.editor,
				keyCode = event.keyCode,
				selection = editor.getSelection(),
				range = selection && selection.getRanges(true)[0],
				tabSpaces = editor.config.tabSpaces,
				tabText = '',
				isList = false,
				cells = function(bad) {
					return function(node) {
						return bad ^ (node && node.is('td', 'th'));
					};
				},
				rows = function(bad) {
					return function(node) {
						return bad ^ (node && node.getName() == 'tr');
					};
				},
				nextCell,
				row,
				parent,
				element;

			if (!range) {
				return false;
			}

			element = range.startContainer;

			while(tabSpaces--) {
				tabText += ' ';
			}

			while(element) {
				if(element.type == CKEDITOR.NODE_ELEMENT) {
					if(element.is('tr', 'tbody', 'table')) {
						return true;
					}
					else if(element.is('dt') || (element.is('dd') && hasShift)) {
						var mark = selection.createBookmarks();
						element.renameNode(element.getName() == 'dt' ? 'dd' : 'dt');
						selection.selectBookmarks(mark);
						return true;
					}
					else if(!hasShift && element.is('pre')) {
						editor.fire('saveSnapshot');
						var tabNode = new CKEDITOR.dom.text(tabText, editor.document);
						range.deleteContents();
						range.insertNode(tabNode);
						range.setStartAt(tabNode, CKEDITOR.POSITION_BEFORE_END);
						range.collapse(true);
						range.select();

						editor.fire('saveSnapshot');

						return true;
					}
					else if(element.is('li')) {
						isList = true;
					}
					else if(element.is('td', 'th')) {
						if(isList) {
							if(range.checkStartOfBlock()) {
								break;
							}
						}

						// Find the next cell 
						nextCell = hasShift ? element.getPrevious(cells) : element.getNext(cells);

						if(nextCell == null) {
							parent = element.getParent();
							row = hasShift ? parent.getPrevious(rows) : parent.getNext(rows);
							if (row) {
								nextCell = hasShift ? row.getLast(cells) : row.getFirst(cells);
							}
							else {
								// We're still null
								if(hasShift) {
									break;
								}

								// Save snapshot
								editor.fire('saveSnapshot');

								(function() {
									var table = element.getAscendant('table').$,
										cells = parent.$.cells,
										rows = table.rows,
										newRow = new CKEDITOR.dom.element(table.insertRow(-1), editor.document),
										x, count, newCell;

									for (x = 0, count = cells.length; x < count; x++ ) {
										newCell = newRow.append(new CKEDITOR.dom.element(cells[x], editor.document).clone(false, false));
										if(!CKEDITOR.env.ie) {
											newCell.appendBogus()
										}
										if(!x) {
											nextCell = newCell;
										}
									}
									editor.fire('saveSnapshot');
								})();
							}
						}

						if(nextCell) {
							range.moveToElementEditStart(nextCell);
							range.select();
							return true;
						}
					}
				}

				element = element.getParent();
			}

			if (!hasShift) {
				var startNode = range.getCommonAncestor(true, true),
					nextNode;

				if(startNode && startNode.is('h1', 'h2', 'h3', 'h4', 'h5', 'h6')) {
					nextNode = startNode.getNextSourceNode(false, CKEDITOR.NODE_ELEMENT);

					if (!nextNode) {
						nextNode = new CKEDITOR.dom.element(editor.config.enterMode == CKEDITOR.ENTER_DIV ? 'div' : 'p', editor.document);
						nextNode.insertAfter(startNode);
					}

					range.moveToElementEditStart(nextNode);
					range.select();
					return true;
				}

				if (tabText.length && !range.checkStartOfBlock()) {
					editor.insertHtml(tabText);
					return true;
				}
			}
			
			editor.execCommand(hasShift ? 'outdent' : 'indent');
			return true;
		}
		
	}
	
});