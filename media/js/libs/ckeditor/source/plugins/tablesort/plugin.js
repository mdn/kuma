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

CKEDITOR.plugins.add( 'tablesort',
{
	lang : 'en', // %REMOVE_LINE_CORE%

	init : function( editor )
	{
		var lang = editor.lang.tablesort;

		editor.addCommand( 'tablesort', new CKEDITOR.dialogCommand( 'tablesort' ) );

		CKEDITOR.dialog.add( 'tablesort', this.path + 'dialogs/sort.js' );

		// If the "menu" plugin is loaded, register the menu items.
		if ( editor.addMenuItems )
		{
			editor.addMenuItems(
				{
					tablesort :
					{
						label : lang.menu,
						command : 'tablesort',
						group : 'table',
						order : 2
					}
				} );
		}

		// If the "contextmenu" plugin is loaded, register the listeners.
		if ( editor.contextMenu )
		{
			editor.contextMenu.addListener( function( element, selection )
				{
					if ( !element || element.isReadOnly() )
						return null;

					var isTable	= element.is( 'table' ) || element.hasAscendant( 'table' );

					if ( isTable )
					{
						return {
							tablesort : CKEDITOR.TRISTATE_OFF
						};
					}

					return null;
				} );
		}
	}
} );