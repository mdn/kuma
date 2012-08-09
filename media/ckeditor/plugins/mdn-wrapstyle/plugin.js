/*
 * MindTouch Core - open source enterprise collaborative networking
 * Copyright(c) 2006-2010 MindTouch Inc.
 * www.mindtouch.com oss@mindtouch.com
 *
 * For community documentation and downloads visit www.opengarden.org;
 * please review the licensing section.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 *(at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 * http://www.gnu.org/copyleft/gpl.html
 */

/**
 * Support of wrap styles
 * @see #MT-9346
 * @link {http://developer.mindtouch.com/User:dev/Specs/Wrapping_block_styles_for_the_editor}
 * @fileOverview The "wrapstyle" plugin. It wraps the selected block level elements with a 'div' element with specified style.
 */

(function() {
	// Definition of elements at which div operation should stopped.
	var divLimitDefinition = (function() {
		// Customzie from specialize blockLimit elements
		var definition = CKEDITOR.tools.extend({}, CKEDITOR.dtd.$blockLimit);

		// Exclude 'div' itself.
		delete definition.div;

		// Exclude 'td' and 'th'
		delete definition.td;
		delete definition.th;
		
		return definition;
	})();

	// DTD of 'div' element
	var dtd = CKEDITOR.dtd.div;

	/**
	 * Add to collection with DUP examination.
	 * @param {Object} collection
	 * @param {Object} element
	 * @param {Object} database
	 */
	function addSafely(collection, element, database) {
		// 1. IE doesn't support customData on text nodes;
		// 2. Text nodes never get chance to appear twice;
		if(!element.is || !element.getCustomData('block_processed')) {
			element.is && CKEDITOR.dom.element.setMarker(database, element, 'block_processed', true);
			collection.push(element);
		}
	}

	/**
	 * Get the first div limit element on the element's path.
	 * @param {Object} element
	 */
	function getDivLimitElement(element) {
		var pathElements = new CKEDITOR.dom.elementPath(element).elements,
			divLimit;
		for(var i = 0; i < pathElements.length; i++) {
			if(pathElements[i].getName() in divLimitDefinition) {
				divLimit = pathElements[i];
				break;
			}
		}
		return divLimit;
	}

	/**
	 * Divide a set of nodes to different groups by their path's blocklimit element.
	 * Note: the specified nodes should be in source order naturally, which mean they are supposed to produce a by following class:
	 *  * CKEDITOR.dom.range.Iterator
	 *  * CKEDITOR.dom.domWalker
	 *  @return {Array []} the grouped nodes
	 */
	function groupByDivLimit(nodes) {
		var groups = [],
			lastDivLimit = null,
			path, block;
		for(var i = 0; i < nodes.length; i++) {
			block = nodes[i];
			var limit = getDivLimitElement(block);
			if(!limit.equals(lastDivLimit)) {
				lastDivLimit = limit;
				groups.push([]);
			}
			groups[groups.length - 1].push(block);
		}
		return groups;
	}

	/**
	 * Wrapping 'div' element around appropriate blocks among the selected ranges.
	 * @param {Object} editor
	 */
	function createDiv(editor) {
		// new adding containers OR detected pre-existed containers.
		var containers = [],
		// node markers store.
			database = {},
		// All block level elements which contained by the ranges.
			containedBlocks = [], block,
		// Get all ranges from the selection.
			selection = editor.document.getSelection(),
			ranges = selection.getRanges(),
			bookmarks = selection.createBookmarks(),
			i, iterator;

		// collect all included elements from dom-iterator
		for(i = 0; i < ranges.length; i++) {
			iterator = ranges[i].createIterator();
			while((block = iterator.getNextParagraph())) {
				// include contents of blockLimit elements.
				if(block.getName() in divLimitDefinition) {
					var j, childNodes = block.getChildren();
					for(j = 0; j < childNodes.count(); j++)
						addSafely(containedBlocks, childNodes.getItem(j) , database);
				}
				else {
					// Bypass dtd disallowed elements.
					while(!dtd[block.getName()] && block.getName() != 'body')
						block = block.getParent();
					addSafely(containedBlocks, block, database);
				}
			}
		}

		CKEDITOR.dom.element.clearAllMarkers(database);

		var blockGroups = groupByDivLimit(containedBlocks),
			ancestor, divElement;

		for(i = 0; i < blockGroups.length; i++) {
			var currentNode = blockGroups[i][0];

			// Calculate the common parent node of all contained elements.
			ancestor = currentNode.getParent();
			for(j = 1; j < blockGroups[i].length; j++)
				ancestor = ancestor.getCommonAncestor(blockGroups[i][j]);

			divElement = new CKEDITOR.dom.element('div', editor.document);

			// Normalize the blocks in each group to a common parent.
			for(j = 0; j < blockGroups[i].length; j++) {
				currentNode = blockGroups[i][j];

				while(!currentNode.getParent().equals(ancestor))
					currentNode = currentNode.getParent();

				// This could introduce some duplicated elements in array.
				blockGroups[i][j] = currentNode;
			}

			// Wrapped blocks counting
			for(j = 0; j < blockGroups[i].length; j++) {
				currentNode = blockGroups[i][j];

				// Avoid DUP elements introduced by grouping.
				if(!(currentNode.getCustomData && currentNode.getCustomData('block_processed')))
				{
					currentNode.is && CKEDITOR.dom.element.setMarker(database, currentNode, 'block_processed', true);

					// Establish new container, wrapping all elements in this group.
					if(!j)
						divElement.insertBefore(currentNode);

					divElement.append(currentNode);
				}
			}

			CKEDITOR.dom.element.clearAllMarkers(database);
			containers.push(divElement);
		}

		selection.selectBookmarks(bookmarks);
		return containers;
	}

	var wrapStyles = [];

	CKEDITOR.plugins.add('mdn-wrapstyle', {
		requires: ['styles'],

		beforeInit: function(editor) {/*
			var sortStyleDefinitions = function(definitionA, definitionB) {
				return definitionA.wrap === true ? -1 :
					definitionB.wrap === true ? 1 : 0;
			}

			editor.getStylesSet(function(stylesDefinitions) {
				for(var i = 0, count = stylesDefinitions.length; i < count; i++) {
					var styleDefinition = stylesDefinitions[i],
						style, className;

					// add the common class name for all wrap styles
					if(styleDefinition.wrap && styleDefinition.wrap === true && styleDefinition.attributes) {
						className = styleDefinition.attributes['class'] || '';

						if(className.length) {
							className += ' ';
						}

						className +=(editor.config.style_wrap_class || 'style-wrap');

						styleDefinition.attributes['class'] = className;

						style = new CKEDITOR.style(styleDefinition);
						wrapStyles.push(style);
					}
				}

				// move wrap styles up
				stylesDefinitions.sort(sortStyleDefinitions);
			});
			*/

			// extend style class
			var styleProto = CKEDITOR.style.prototype,
				applyStyle = styleProto.apply,
				removeStyle = styleProto.remove,
				checkRemovable = styleProto.checkElementRemovable;
			

			CKEDITOR.tools.extend(styleProto, {
					apply: function(document) {
						if(this._.definition.wrap && this._.definition.wrap === true) {
							editor.execCommand('wrapstyle', this);
						}
						else {
							applyStyle.apply(this, arguments);
						}
					},

					remove: function(document) {
						if(this._.definition.wrap && this._.definition.wrap === true) {
							editor.execCommand('wrapstyle', this);
						}
						else {
							removeStyle.apply(this, arguments);
						}
					},

					checkElementRemovable: function(element, fullMatch) {
						if(this._.definition.wrap && this._.definition.wrap === true) {
							element = element && element.getAscendant(this.element, true);
						}
						if(element) {
							return checkRemovable.apply(this, [element, fullMatch]);
						}
					}
				}, true);
		},

		init: function(editor) {
			editor.addCommand('wrapstyle', {
					exec : function(editor, style) {
						var selection = editor.getSelection(),
							bookmarks = selection && selection.createBookmarks(),
							ranges = selection && selection.getRanges(),
							rangeIterator = ranges && ranges.createIterator(),
							range,
							iterator,
							div,
							removeDiv = true,
							toRemove = [];

						while((range = rangeIterator.getNextRange())) { // Only one =
							iterator = range.createIterator();
							iterator.enforceRealBlocks = true;

							var block;
							while((block = iterator.getNextParagraph())) { // Only one =
								div = block.getAscendant(style.element, true);

								if(div && style.checkElementRemovable(div)) {
									var prev = toRemove.pop(),
										commonAncestor = prev && prev.getCommonAncestor(div);

									if(commonAncestor && style.checkElementRemovable(commonAncestor)) {
										toRemove.push(commonAncestor)
									}
									else {
										prev && toRemove.push(prev);
										toRemove.push(div);
									}
								}
								else if(toRemove.length == 0) {
									removeDiv = false;
								}
							}
						}

						if(removeDiv) {
							for(var i = 0, count = toRemove.length; i < count; i++) {
								toRemove[i].remove(true);
							}
						}
						else {
							var divs = createDiv(editor);

							for(var i = 0, count = divs.length; i < count; i++) {
								div = divs[i];
								style.applyToObject(div);
							}
						}

						bookmarks && selection.selectBookmarks(bookmarks);
					}
				});
		},

		afterInit: function(editor) {
			// Don't remove formatting from wrap divs
			editor.addRemoveFormatFilter && editor.addRemoveFormatFilter(function(element) {
					for(var i = 0, count = wrapStyles.length; i < count; i++) {
						var style = wrapStyles[i];

						if(element.is(style.element) && style.checkElementRemovable(element)) {
							return false;
						}
					}

					return true;
				});
		}
	});
})();

/**
 * The common class for wrap blocks.
 * @name CKEDITOR.config.style_wrap_class
 * @type String
 * @default 'style-wrap'
 */