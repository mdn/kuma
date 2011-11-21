/*
 * MindTouch Deki - enterprise collaboration and integration platform
 * Copyright (C) 2006-2009 MindTouch, Inc.
 * www.mindtouch.com  oss@mindtouch.com
 *
 * For community documentation and downloads visit www.opengarden.org;
 * please review the licensing section.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
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
 * @file Definition List plugin.
 */

(function()
{
	var listNodeNames = { dl : 1 };

	var whitespaces = CKEDITOR.dom.walker.whitespaces(),
		bookmarks = CKEDITOR.dom.walker.bookmark(),
		nonEmpty = function( node ){ return !( whitespaces( node ) || bookmarks( node ) ); };

	/*
	 * Convert a DOM list tree into a data structure that is easier to
	 * manipulate. This operation should be non-intrusive in the sense that it
	 * does not change the DOM tree, with the exception that it may add some
	 * markers to the list item nodes when database is specified.
	 */
	function defListToArray( listNode, database, baseArray, baseIndentLevel, grandparentNode )
	{
		if ( !listNodeNames[ listNode.getName() ] )
			return [];

		if ( !baseIndentLevel )
			baseIndentLevel = 0;
		if ( !baseArray )
			baseArray = [];

		// Iterate over all list items to get their contents and look for inner lists.
		for ( var i = 0, count = listNode.getChildCount() ; i < count ; i++ )
		{
			var listItem = listNode.getChild( i );

			// It may be a text node or some funny stuff.
			if ( !listItem.is || !listItem.is( 'dt', 'dd' ) )
				continue;

			var itemObj = { 'parent' : listNode, indent : baseIndentLevel, contents : [], dx : listItem.getName() };
			if ( !grandparentNode )
			{
				itemObj.grandparent = listNode.getParent();
				if ( itemObj.grandparent && itemObj.grandparent.is && itemObj.grandparent.is( 'dt', 'dd' ) )
					itemObj.grandparent = itemObj.grandparent.getParent();
			}
			else
				itemObj.grandparent = grandparentNode;

			if ( database )
				CKEDITOR.dom.element.setMarker( database, listItem, 'listarray_index', baseArray.length );
			baseArray.push( itemObj );

			for ( var j = 0, itemChildCount = listItem.getChildCount(), child; j < itemChildCount ; j++ )
			{
				child = listItem.getChild( j );
				if ( child.type == CKEDITOR.NODE_ELEMENT && listNodeNames[ child.getName() ] )
					// Note the recursion here, it pushes inner list items with
					// +1 indentation in the correct order.
					defListToArray( child, database, baseArray, baseIndentLevel + 1, itemObj.grandparent );
				else
					itemObj.contents.push( child );
			}
		}
		return baseArray;
	}

	// Convert our internal representation of a list back to a DOM forest.
	function arrayToDefList( listArray, database, baseIndex, paragraphMode, dir )
	{
		if ( !baseIndex )
			baseIndex = 0;
		if ( !listArray || listArray.length < baseIndex + 1 )
			return null;
		var doc = listArray[ baseIndex ].parent.getDocument(),
			retval = new CKEDITOR.dom.documentFragment( doc ),
			rootNode = null,
			currentIndex = baseIndex,
			indentLevel = Math.max( listArray[ baseIndex ].indent, 0 ),
			currentListItem = null,
			paragraphName = ( paragraphMode == CKEDITOR.ENTER_P ? 'p' : 'div' );
		while ( 1 )
		{
			var item = listArray[ currentIndex ];
			if ( item.indent == indentLevel )
			{
				if ( !rootNode || listArray[ currentIndex ].parent.getName() != rootNode.getName() )
				{
					rootNode = listArray[ currentIndex ].parent.clone( 0, 1 );
					dir && rootNode.setAttribute( 'dir', dir );
					retval.append( rootNode );
				}
				currentListItem = rootNode.append( doc.createElement( item.dx ) );
				for ( var i = 0 ; i < item.contents.length ; i++ )
					currentListItem.append( item.contents[i].clone( 1, 1 ) );
				currentIndex++;
			}
			else if ( item.indent == Math.max( indentLevel, 0 ) + 1 )
			{
				var listData = arrayToDefList( listArray, null, currentIndex, paragraphMode );
				currentListItem.append( listData.listNode );
				currentIndex = listData.nextIndex;
			}
			else if ( item.indent == -1 && !baseIndex && item.grandparent )
			{
				currentListItem;
				if ( listNodeNames[ item.grandparent.getName() ] )
					currentListItem = doc.createElement( item.dx );
				else
				{
					// Create completely new blocks here.
					if ( dir || item.element.hasAttributes() ||
						( paragraphMode != CKEDITOR.ENTER_BR && item.grandparent.getName() != 'td' ) )
					{
						currentListItem = doc.createElement( paragraphName );
						item.element.copyAttributes( currentListItem, { type:1, value:1 } );
						dir && currentListItem.setAttribute( 'dir', dir );

						// There might be a case where there are no attributes in the element after all
						// (i.e. when "type" or "value" are the only attributes set). In this case, if enterMode = BR,
						// the current item should be a fragment.
						if ( !dir && paragraphMode == CKEDITOR.ENTER_BR && !currentListItem.hasAttributes() )
							currentListItem = new CKEDITOR.dom.documentFragment( doc );
					}
					else
						currentListItem = new CKEDITOR.dom.documentFragment( doc );
				}

				for ( i = 0 ; i < item.contents.length ; i++ )
					currentListItem.append( item.contents[i].clone( 1, 1 ) );

				if ( currentListItem.type == CKEDITOR.NODE_DOCUMENT_FRAGMENT
					 && currentIndex != listArray.length - 1 )
				{
					var last = currentListItem.getLast();
					if ( last && last.type == CKEDITOR.NODE_ELEMENT
							&& last.getAttribute( 'type' ) == '_moz' )
					{
						last.remove();
					}

					if ( !( last = currentListItem.getLast( nonEmpty )
						&& last.type == CKEDITOR.NODE_ELEMENT
						&& last.getName() in CKEDITOR.dtd.$block ) )
					{
						currentListItem.append( doc.createElement( 'br' ) );
					}
				}

				if ( currentListItem.type == CKEDITOR.NODE_ELEMENT &&
						currentListItem.getName() == paragraphName &&
						currentListItem.$.firstChild )
				{
					currentListItem.trim();
					var firstChild = currentListItem.getFirst();
					if ( firstChild.type == CKEDITOR.NODE_ELEMENT && firstChild.isBlockBoundary() )
					{
						var tmp = new CKEDITOR.dom.documentFragment( doc );
						currentListItem.moveChildren( tmp );
						currentListItem = tmp;
					}
				}

				var currentListItemName = currentListItem.$.nodeName.toLowerCase();
				if ( !CKEDITOR.env.ie && ( currentListItemName == 'div' || currentListItemName == 'p' ) )
					currentListItem.appendBogus();
				retval.append( currentListItem );
				rootNode = null;
				currentIndex++;
			}
			else
				return null;

			if ( listArray.length <= currentIndex || Math.max( listArray[ currentIndex ].indent, 0 ) < indentLevel )
				break;
		}

		// Clear marker attributes for the new list tree made of cloned nodes, if any.
		if ( database )
		{
			var currentNode = retval.getFirst();
			while ( currentNode )
			{
				if ( currentNode.type == CKEDITOR.NODE_ELEMENT )
					CKEDITOR.dom.element.clearMarkers( database, currentNode );
				currentNode = currentNode.getNextSourceNode();
			}
		}

		return { listNode : retval, nextIndex : currentIndex };
	}

	function setState( editor, state )
	{
		editor.getCommand( this.name ).setState( state );
	}

	function onSelectionChange( evt )
	{
		var path = evt.data.path,
			blockLimit = path.blockLimit,
			elements = path.elements,
			element;

		// Grouping should only happen under blockLimit.(#3940).
		for ( var i = 0 ; i < elements.length && ( element = elements[ i ] )
			  && !element.equals( blockLimit ); i++ )
		{
			if ( elements[i].getName() == this.type )
			{
				return setState.call( this, evt.editor,
						this.type == elements[i].getName() ? CKEDITOR.TRISTATE_ON : CKEDITOR.TRISTATE_OFF );
			}
		}

		return setState.call( this, evt.editor, CKEDITOR.TRISTATE_OFF );
	}

	function changeListType( editor, groupObj, database, listsCreated )
	{
		var listArray = CKEDITOR.plugins.list.listToArray( groupObj.root, database ),
			selectedListItems = [];

		for ( var i = 0 ; i < groupObj.contents.length ; i++ )
		{
			var itemNode = groupObj.contents[i];
			itemNode.renameNode( this.type );
		}
	}

	var headerTagRegex = /^h[1-6]$/;

	function createList( editor, groupObj, listsCreated )
	{
		var contents = groupObj.contents,
			doc = groupObj.root.getDocument(),
			listContents = [];

		// It is possible to have the contents returned by DomRangeIterator to be the same as the root.
		// e.g. when we're running into table cells.
		// In such a case, enclose the childNodes of contents[0] into a <div>.
		if ( contents.length == 1 && contents[0].equals( groupObj.root ) )
		{
			var divBlock = doc.createElement( 'div' );
			contents[0].moveChildren && contents[0].moveChildren( divBlock );
			contents[0].append( divBlock );
			contents[0] = divBlock;
		}

		// Calculate the common parent node of all content blocks.
		var commonParent = groupObj.contents[0].getParent();
		for ( var i = 0 ; i < contents.length ; i++ )
			commonParent = commonParent.getCommonAncestor( contents[i].getParent() );

		var useComputedState = editor.config.useComputedState,
			listDir, explicitDirection;

		useComputedState = useComputedState === undefined || useComputedState;

		// We want to insert things that are in the same tree level only, so calculate the contents again
		// by expanding the selected blocks to the same tree level.
		for ( i = 0 ; i < contents.length ; i++ )
		{
			var contentNode = contents[i],
				parentNode;
			while ( ( parentNode = contentNode.getParent() ) )
			{
				if ( parentNode.equals( commonParent ) )
				{
					listContents.push( contentNode );

					// Determine the lists's direction.
					if ( !explicitDirection && contentNode.getDirection() )
						explicitDirection = 1;

					var itemDir = contentNode.getDirection( useComputedState );

					if ( listDir !== null )
					{
						// If at least one LI have a different direction than current listDir, we can't have listDir.
						if ( listDir && listDir != itemDir )
							listDir = null;
						else
							listDir = itemDir;
					}

					break;
				}
				contentNode = parentNode;
			}
		}

		if ( listContents.length < 1 )
			return;

		// Insert the list to the DOM tree.
		var insertAnchor = listContents[ listContents.length - 1 ].getNext(),
			listNode = doc.createElement( 'dl' );

		listsCreated.push( listNode );

		var contentBlock, listItem;

		while ( listContents.length )
		{
			contentBlock = listContents.shift();
			listItem = doc.createElement( this.type == 'dl' ? 'dt' : this.type );

			// Preserve preformat block and heading structure when converting to list item. (#5335) (#5271)
			if ( contentBlock.is( 'pre' ) || headerTagRegex.test( contentBlock.getName() ) )
				contentBlock.appendTo( listItem );
			else
			{
				// Remove DIR attribute if it was merged into list root.
				if ( listDir && contentBlock.getDirection() )
				{
					contentBlock.removeStyle( 'direction' );
					contentBlock.removeAttribute( 'dir' );
				}

				contentBlock.copyAttributes( listItem );
				contentBlock.moveChildren( listItem );
				contentBlock.remove();
			}

			listItem.appendTo( listNode );
		}

		// Apply list root dir only if it has been explicitly declared.
		if ( listDir && explicitDirection )
			listNode.setAttribute( 'dir', listDir );

		if ( insertAnchor )
			listNode.insertBefore( insertAnchor );
		else
			listNode.appendTo( commonParent );
	}

	function removeList( editor, groupObj, database )
	{
		// This is very much like the change list type operation.
		// Except that we're changing the selected items' indent to -1 in the list array.
		var listArray = defListToArray( groupObj.root, database ),
			selectedListItems = [];

		if ( listNodeNames[ this.type ] )
		{
			for ( var j = 0 ; j < listArray.length ; j++ )
			{
				listArray[j].indent = -1;
			}
		}
		else
		{
			for ( var i = 0 ; i < groupObj.contents.length ; i++ )
			{
				var itemNode = groupObj.contents[i];
				itemNode = itemNode.getAscendant( this.type, true );
				if ( !itemNode || itemNode.getCustomData( 'list_item_processed' ) )
					continue;
				selectedListItems.push( itemNode );
				CKEDITOR.dom.element.setMarker( database, itemNode, 'list_item_processed', true );
			}

			var lastListIndex = null;
			for ( i = 0 ; i < selectedListItems.length ; i++ )
			{
				var listIndex = selectedListItems[i].getCustomData( 'listarray_index' );
				listArray[listIndex].indent = -1;
				lastListIndex = listIndex;
			}

			// After cutting parts of the list out with indent=-1, we still have to maintain the array list
			// model's nextItem.indent <= currentItem.indent + 1 invariant. Otherwise the array model of the
			// list cannot be converted back to a real DOM list.
			for ( i = lastListIndex + 1 ; i < listArray.length ; i++ )
			{
				if ( listArray[i].indent > listArray[i-1].indent + 1 )
				{
					var indentOffset = listArray[i-1].indent + 1 - listArray[i].indent;
					var oldIndent = listArray[i].indent;
					while ( listArray[i] && listArray[i].indent >= oldIndent )
					{
						listArray[i].indent += indentOffset;
						i++;
					}
					i--;
				}
			}
		}

		var newList = arrayToDefList( listArray, database, null, editor.config.enterMode,
			groupObj.root.getAttribute( 'dir' ) );

		// Compensate <br> before/after the list node if the surrounds are non-blocks.(#3836)
		var docFragment = newList.listNode, boundaryNode, siblingNode;
		function compensateBrs( isStart )
		{
			if ( ( boundaryNode = docFragment[ isStart ? 'getFirst' : 'getLast' ]() )
				 && !( boundaryNode.is && boundaryNode.isBlockBoundary() )
				 && ( siblingNode = groupObj.root[ isStart ? 'getPrevious' : 'getNext' ]
				      ( CKEDITOR.dom.walker.whitespaces( true ) ) )
				 && !( siblingNode.is && siblingNode.isBlockBoundary( { br : 1 } ) ) )
				editor.document.createElement( 'br' )[ isStart ? 'insertBefore' : 'insertAfter' ]( boundaryNode );
		}
		compensateBrs( true );
		compensateBrs();

		docFragment.replace( groupObj.root );
	}

	function defListCommand( name, type )
	{
		this.name = name;
		this.type = type;
	}

	defListCommand.prototype = {
		exec : function( editor )
		{
			editor.focus();

			var doc = editor.document,
				selection = editor.getSelection(),
				ranges = selection && selection.getRanges( true );

			// There should be at least one selected range.
			if ( !ranges || ranges.length < 1 )
				return;

			// Midas lists rule #1 says we can create a list even in an empty document.
			// But DOM iterator wouldn't run if the document is really empty.
			// So create a paragraph if the document is empty and we're going to create a list.
			if ( this.state == CKEDITOR.TRISTATE_OFF )
			{
				var body = doc.getBody();
				body.trim();
				if ( !body.getFirst() )
				{
					var paragraph = doc.createElement( editor.config.enterMode == CKEDITOR.ENTER_P ? 'p' :
							( editor.config.enterMode == CKEDITOR.ENTER_DIV ? 'div' : 'br' ) );
					paragraph.appendTo( body );
					ranges = new CKEDITOR.dom.rangeList( [ new CKEDITOR.dom.range( doc ) ] );
					// IE exception on inserting anything when anchor inside <br>.
					if ( paragraph.is( 'br' ) )
					{
						ranges[ 0 ].setStartBefore( paragraph );
						ranges[ 0 ].setEndAfter( paragraph );
					}
					else
						ranges[ 0 ].selectNodeContents( paragraph );
					selection.selectRanges( ranges );
				}
				// Maybe a single range there enclosing the whole list,
				// turn on the list state manually(#4129).
				else
				{
					var range = ranges.length == 1 && ranges[ 0 ],
						enclosedNode = range && range.getEnclosedNode();
					if ( enclosedNode && enclosedNode.is
						&& this.type == enclosedNode.getName() )
							setState.call( this, editor, CKEDITOR.TRISTATE_ON );
				}
			}

			var bookmarks = selection.createBookmarks( true );

			// Group the blocks up because there are many cases where multiple lists have to be created,
			// or multiple lists have to be cancelled.
			var listGroups = [],
				database = {},
				rangeIterator = ranges.createIterator(),
				index = 0;

			while ( ( range = rangeIterator.getNextRange() ) && ++index )
			{
				var boundaryNodes = range.getBoundaryNodes(),
					startNode = boundaryNodes.startNode,
					endNode = boundaryNodes.endNode;

				if ( startNode.type == CKEDITOR.NODE_ELEMENT && startNode.getName() == 'td' )
					range.setStartAt( boundaryNodes.startNode, CKEDITOR.POSITION_AFTER_START );

				if ( endNode.type == CKEDITOR.NODE_ELEMENT && endNode.getName() == 'td' )
					range.setEndAt( boundaryNodes.endNode, CKEDITOR.POSITION_BEFORE_END );

				var iterator = range.createIterator(),
					block;

				iterator.forceBrBreak = ( this.state == CKEDITOR.TRISTATE_OFF );

				while ( ( block = iterator.getNextParagraph() ) )
				{
					// Avoid duplicate blocks get processed across ranges.
					if( block.getCustomData( 'list_block' ) )
						continue;
					else
						CKEDITOR.dom.element.setMarker( database, block, 'list_block', 1 );

					var path = new CKEDITOR.dom.elementPath( block ),
						pathElements = path.elements,
						pathElementsCount = pathElements.length,
						listNode = null,
						processedFlag = 0,
						blockLimit = path.blockLimit,
						element;

					// First, try to group by a list ancestor.
					for ( var i = pathElementsCount - 1; i >= 0 && ( element = pathElements[ i ] ); i-- )
					{
						if ( listNodeNames[ element.getName() ]
							 && blockLimit.contains( element ) )     // Don't leak outside block limit (#3940).
						{
							// If we've encountered a list inside a block limit
							// The last group object of the block limit element should
							// no longer be valid. Since paragraphs after the list
							// should belong to a different group of paragraphs before
							// the list. (Bug #1309)
							blockLimit.removeCustomData( 'list_group_object_' + index );

							var groupObj = element.getCustomData( 'list_group_object' );
							if ( groupObj )
								groupObj.contents.push( block );
							else
							{
								groupObj = { root : element, contents : [ block ] };
								listGroups.push( groupObj );
								CKEDITOR.dom.element.setMarker( database, element, 'list_group_object', groupObj );
							}
							processedFlag = 1;
							break;
						}
					}

					if ( processedFlag )
						continue;

					// No list ancestor? Group by block limit, but don't mix contents from different ranges.
					var root = blockLimit;
					if ( root.getCustomData( 'list_group_object_' + index ) )
						root.getCustomData( 'list_group_object_' + index ).contents.push( block );
					else
					{
						groupObj = { root : root, contents : [ block ] };
						CKEDITOR.dom.element.setMarker( database, root, 'list_group_object_' + index, groupObj );
						listGroups.push( groupObj );
					}
				}
			}

			// Now we have two kinds of list groups, groups rooted at a list, and groups rooted at a block limit element.
			// We either have to build lists or remove lists, for removing a list does not makes sense when we are looking
			// at the group that's not rooted at lists. So we have three cases to handle.
			var listsCreated = [];
			while ( listGroups.length > 0 )
			{
				groupObj = listGroups.shift();
				if ( this.state == CKEDITOR.TRISTATE_OFF )
				{
					if ( listNodeNames[ groupObj.root.getName() ] )
						changeListType.call( this, editor, groupObj, database, listsCreated );
					else
						createList.call( this, editor, groupObj, listsCreated );
				}
				else if ( this.state == CKEDITOR.TRISTATE_ON && listNodeNames[ groupObj.root.getName() ] )
					removeList.call( this, editor, groupObj, database );
			}

			// For all new lists created, merge adjacent, same type lists.
			for ( i = 0 ; i < listsCreated.length ; i++ )
			{
				listNode = listsCreated[i];
				var mergeSibling, listCommand = this;
				( mergeSibling = function( rtl ){

					var sibling = listNode[ rtl ?
						'getPrevious' : 'getNext' ]( CKEDITOR.dom.walker.whitespaces( true ) );
					if ( sibling && sibling.getName &&
						 sibling.getName() == listCommand.type )
					{
						sibling.remove();
						// Move children order by merge direction.(#3820)
						sibling.moveChildren( listNode, rtl );
					}
				} )();
				mergeSibling( 1 );
			}

			// Clean up, restore selection and update toolbar button states.
			CKEDITOR.dom.element.clearAllMarkers( database );
			selection.selectBookmarks( bookmarks );
			editor.focus();
		}
	};

	CKEDITOR.plugins.add( 'definitionlist',
	{
		requires : [ 'domiterator', 'list' ],

		lang : [ 'en', 'cs', 'de', 'en-au', 'es', 'et', 'fr-ca', 'fr', 'he', 'hu', 'it', 'ja', 'ko', 'nl', 'pt-br', 'ru', 'sv' ],

		init : function( editor )
		{
			// Register commands.
			var definitionListCommand = new defListCommand( 'definitionlist', 'dl' ),
				definitionTermCommand = new defListCommand( 'definitionterm', 'dt' ),
				definitionDescCommand = new defListCommand( 'definitiondesc', 'dd' );

			editor.addCommand( 'definitionlist', definitionListCommand );
			editor.addCommand( 'definitionterm', definitionTermCommand );
			editor.addCommand( 'definitiondesc', definitionDescCommand );

			// Register the toolbar button.
			editor.ui.addButton( 'DefinitionList',
				{
					label : editor.lang.definitionList,
					command : 'definitionlist',
					icon : this.path + 'images/dl.gif'
				} );
			editor.ui.addButton( 'DefinitionTerm',
				{
					label : editor.lang.definitionTerm,
					command : 'definitionterm',
					icon : this.path + 'images/dt.gif'
				} );
			editor.ui.addButton( 'DefinitionDescription',
				{
					label : editor.lang.definitionDesc,
					command : 'definitiondesc',
					icon : this.path + 'images/dd.gif'
				} );

			// Register the state changing handlers.
			editor.on( 'selectionChange', CKEDITOR.tools.bind( onSelectionChange, definitionListCommand ) );
			editor.on( 'selectionChange', CKEDITOR.tools.bind( onSelectionChange, definitionTermCommand ) );
			editor.on( 'selectionChange', CKEDITOR.tools.bind( onSelectionChange, definitionDescCommand ) );
		}
	} );
})();
