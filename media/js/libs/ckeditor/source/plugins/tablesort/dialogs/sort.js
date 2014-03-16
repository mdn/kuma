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

(function()
{
	function tablesortDialog( editor, command )
	{
		var fillSortByList = function( table )
		{
			var cols = table.$.rows[0].cells.length, i, num;
			
			this.clear();
			
			for ( i = 0 ; i < cols ; i++ )
			{
				num = i + 1;
				this.add( editor.lang.tablesort.column + ' ' + num, i );
			}
		};
		
		var sortBySelect = function( id, disabled )
		{
			return {
				type : 'select',
				id : 'selSortBy' + id,
				'default' : '',
				label : '',
				items : [],
				setup : function( selectedTable )
				{
					fillSortByList.call( this, selectedTable );
					if ( disabled )
						this.disable();
				}
			};
		};
		
		var sortTypeSelect = function( id, disabled )
		{
			return {
				type : 'select',
				id : 'selSortType' + id,
				'default' : '',
				label : '',
				items :
				[
					[ editor.lang.tablesort.alphanumeric, 'alphanumeric' ],
					[ editor.lang.tablesort.numeric, 'numeric' ],
					[ editor.lang.tablesort.date, 'date' ]
				],
				setup : function( selectedTable )
				{
					if ( disabled )
						this.disable();
				}
			};
		};
		
		var sortOrderRadio = function( id, disabled )
		{
			return {
				type : 'radio',
				id : 'rdbOrder' + id,
				'default' : 'asc',
				items :
				[
				 	[ editor.lang.tablesort.asc, 'asc' ],
				 	[ editor.lang.tablesort.desc, 'desc' ]
				],
				setup : function( selectedTable )
				{
					if ( disabled )
						for ( var i = 0 ; i < this._.children.length ; i++ )
						{
							this._.children[i].disable();
						}
				}
			};
		};
		
		var onChangeChk = function()
		{
			var disabled = !this.getValue(),
				dialog = this.getDialog(),
				command = disabled ? 'disable' : 'enable',
				id = this.id.substring(this.id.length - 1);
			
			dialog.getContentElement( 'sort', 'selSortBy' + id )[command]();
			dialog.getContentElement( 'sort', 'selSortType' + id )[command]();
			
			var radio = dialog.getContentElement( 'sort', 'rdbOrder' + id ),
				i;
			for ( i = 0 ; i < radio._.children.length ; i++ )
			{
				radio._.children[i][command]();
			}
		};
		
		var sortTable = function( table )
		{
			if ( !table )
				return;
			
			this.table = table;
		};

		sortTable.prototype =
		{
			sort : function( part, cols )
			{
				var sort = function( row1, row2 )
				{
					var result, col, i;
					
					for ( i = 0 ; i < cols.length ; i++ )
					{
						col = cols[i];
						
						switch ( col.type )
						{
							case 'numeric' :
								result = sortTable.sort.numeric( row1[col.column], row2[col.column] );
								break;
							case 'date' :
								result = sortTable.sort.date( row1[col.column], row2[col.column] );
								break;
							case 'alphanumeric' :
							default :
								result = sortTable.sort.alpha( row1[col.column], row2[col.column] );
								break;
						}
						
						if ( col.order == 'desc' )
							result *= -1;
						
						if ( result == 0 )
							continue;
						else
							break;
					}
					
					return result;
				};
			
				var parts = [], i;
				
				switch ( part )
				{
					case 'thead' :
						parts.push( this.table.$.tHead );
						break;
					case 'tfoot' :
						parts.push( this.table.$.tFoot );
						break;
					case 'tbody' :
					default :
						parts = this.table.$.tBodies;
						break;
				}
				
				for ( i = 0 ; i < parts.length ; i++ )
				{
					var rows = [], j;
					
					for ( j = 0 ; j < parts[i].rows.length ; j++ )
					{
						var cells = [], k;
						
						for ( k = 0 ; k < parts[i].rows[j].cells.length ; k++ )
						{
							cells.push( this.getInnerText( parts[i].rows[j].cells[k] ) );
						}
						
						cells.push( parts[i].rows[j] );
						rows.push( cells );
					}
					
					rows.sort( sort );
					
					for ( j = 0 ; j < rows.length ; j++ )
					{
						parts[i].appendChild( rows[j][rows[j].length - 1] );
					}
				}
			},
			
			/**
			 * gets the text we want to use for sorting for a cell.
			 * strips leading and trailing whitespace.
			 * this is *not* a generic getInnerText function; it's special to sorttable.
			 * for example, you can override the cell text with a customkey attribute.
			 * it also gets .value for <input> fields.
			 */
			getInnerText : function( node )
			{
				var hasInputs = ( typeof node.getElementsByTagName == 'function' )
						&& node.getElementsByTagName( 'input' ).length;
			
				if ( typeof node.textContent != 'undefined' && !hasInputs )
				{
					return node.textContent.replace( /^\s+|\s+$/g, '' );
				}
				else if ( typeof node.innerText != 'undefined' && !hasInputs )
				{
					return node.innerText.replace( /^\s+|\s+$/g, '' );
				}
				else if ( typeof node.text != 'undefined' && !hasInputs )
				{
					return node.text.replace( /^\s+|\s+$/g, '' );
				}
				else
				{
					switch ( node.nodeType )
					{
						case 3 :
							if ( node.nodeName.toLowerCase() == 'input' )
							{
								return node.value.replace( /^\s+|\s+$/g, '' );
							}
							// break;
						case 4 :
							return node.nodeValue.replace( /^\s+|\s+$/g, '' );
							break;
						case 1 :
						case 11 :
							var innerText = '';
							for ( var i = 0 ; i < node.childNodes.length ; i++ )
							{
								innerText += this.getInnerText( node.childNodes[i] );
							}
							return innerText.replace( /^\s+|\s+$/g, '' );
							break;
						default :
							return '';
					}
				}
			}	
		};

		/**
		 * sort functions each sort function takes two parameters, a and b you are
		 * comparing a[0] and b[0]
		 */
		sortTable.sort =
		{
			numeric : function( a, b )
			{
				var aa = parseFloat( a.replace( /[^0-9.-]/g, '' ) );
				
				if ( isNaN( aa ) )
					aa = 0;
				
				var bb = parseFloat( b.replace( /[^0-9.-]/g, '' ) );
				
				if ( isNaN( bb ) )
					bb = 0;
				
				return aa - bb;
			},
			
			alpha : function( a, b )
			{
				if ( a == b )
					return 0;
				
				if ( a < b )
					return -1;
				
				return 1;
			},
			
			date : function( a, b )
			{
				var dateA = new Date( a ),
					dateB = new Date( b );
				
				var nDateA = dateA.getTime(),
					nDateB = dateB.getTime();
				
				if ( isNaN( nDateA ) || isNaN( nDateB ) || nDateA == nDateB )
					return 0;
				
				return nDateA - nDateB;
			}
		};

		return {
			title : editor.lang.tablesort.title,
			minWidth : 430,
			minHeight : CKEDITOR.env.ie ? 180 : 150,
			onShow : function()
			{
				// Detect if there's a selected table.
				var selection = editor.getSelection(),
					ranges = selection.getRanges(),
					selectedTable = null;

				if ( ( selectedTable = editor.getSelection().getSelectedElement() ) )
				{
					if ( selectedTable.getName() != 'table' )
						selectedTable = null;
				}
				else if ( ranges.length > 0 )
				{
					var rangeRoot = ranges[0].getCommonAncestor( true );
					selectedTable = rangeRoot.getAscendant( 'table', true );
				}

				// Save a reference to the selected table
				this._.selectedElement = selectedTable;

				if ( selectedTable )
				{
					this.setupContent( selectedTable );
				}
			},
			onOk : function()
			{
				var table = this._.selectedElement;

				this.commitContent( table );
				
				var col, cols = [], i, chkKey;
				
				for ( i = 0 ; i < 3 ; i++ )
				{
					chkKey = this.getContentElement( 'sort', 'chkKey' + i );

					if ( chkKey && !chkKey.getValue() )
						continue;

					col = {};
				
					col.column = this.getContentElement( 'sort', 'selSortBy' + i ).getValue();
					col.type = this.getContentElement( 'sort', 'selSortType' + i ).getValue();
					col.order = this.getContentElement( 'sort', 'rdbOrder' + i ).getValue();
				
					cols.push(col);
				}
				
				var oSortTable = new sortTable( table );
				oSortTable.sort( this.getContentElement( 'sort', 'selSort' ).getValue(), cols );
				
				return true;
			},
			contents : [
				{
					id : 'sort',
					label : editor.lang.tablesort.title,
					elements :
					[
						{
							type : 'hbox',
							widths : [ '5%', '25%', '30%', '40%' ],
							styles : [ 'vertical-align:top' ],
							children :
							[
								{
									type : 'vbox',
									padding : '5px',
									children :
									[
										{
											type : 'html',
											html : '&nbsp;'
										},
										{
											type : 'html',
											html : '&nbsp;'
										},
										{
											type : 'checkbox',
											id : 'chkKey1',
											isChanged : false,
											label : '',
											onChange : onChangeChk
										},
										{
											type : 'checkbox',
											id : 'chkKey2',
											isChanged : false,
											label : '',
											onChange : onChangeChk
										}
									]
								},
								{
									type : 'vbox',
									padding : '5px',
									children :
									[
										{
											type : 'html',
											html : editor.lang.tablesort.by
										},
										sortBySelect( 0 ),
										sortBySelect( 1, true ),
										sortBySelect( 2, true )
									]
								},
								{
									type : 'vbox',
									padding : '5px',
									children :
									[
										{
											type : 'html',
											html : editor.lang.tablesort.type
										},
										sortTypeSelect( 0 ),
										sortTypeSelect( 1, true ),
										sortTypeSelect( 2, true )
									]
								},
								{
									type : 'vbox',
									padding : '5px',
									children :
									[
										{
											type : 'html',
											html : editor.lang.tablesort.order
										},
										sortOrderRadio( 0 ),
										sortOrderRadio( 1, true ),
										sortOrderRadio( 2, true )
									]
								}
							]
						},
						{
							type : 'select',
							id : 'selSort',
							'default' : 'tbody',
							label : '',
							items :
							[
								[ editor.lang.tablesort.head, 'thead' ],
								[ editor.lang.tablesort.body, 'tbody' ],
								[ editor.lang.tablesort.foot, 'tfoot' ]
							]
						}
					]
				}
			]
		};
	}

	CKEDITOR.dialog.add( 'tablesort', function( editor )
		{
			return tablesortDialog( editor, 'table' );
		} );
})();