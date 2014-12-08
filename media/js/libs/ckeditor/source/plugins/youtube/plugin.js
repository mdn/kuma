/*
* Youtube Embed Plugin
*
* @author Jonnas Fonini <contato@fonini.net>
* @version 0.1
* https://github.com/fonini/ckeditor-youtube-plugin
*/

'use strict';

( function() {

	CKEDITOR.plugins.add( 'youtube',
	{
		icons: 'youtube-moono', // %REMOVE_LINE_CORE%
		
		init: function( editor )
		{
			// Backport language
			editor.lang.youtube = {
				button : gettext('Embed YouTube Video'),
				title : gettext('Embed Youtube Video'),
				txtEmbed : gettext('Paste Embed Code Here'),
				txtUrl : gettext('Paste Youtube Video URL'),
				txtWidth : gettext('Width'),
				txtHeight : gettext('Height'),
				noCode : gettext('You must input an embed code or URL'),
				invalidEmbed : gettext('The embed code you\'ve entered doesn\'t appear to be valid'),
				invalidUrl : gettext('The URL you\'ve entered doesn\'t appear to be valid'),
				or : gettext('or')
			};

			editor.addCommand( 'youtube', new CKEDITOR.dialogCommand( 'youtube' ) );

			editor.ui.addButton( 'youtube',
			{
				icon: 'youtube-moono',
				label: editor.lang.youtube.button,
				command: 'youtube',
				toolbar: 'insert'
			});

			CKEDITOR.dialog.add( 'youtube', function ( instance )
			{
				return {
					title : editor.lang.youtube.title,
					minWidth : 550,
					minHeight : 200,
					contents :
						[{
							id : 'youtubePlugin',
							expand : true,
							elements :
								[{
									id : 'txtEmbed',
									type : 'textarea',
									label : editor.lang.youtube.txtEmbed,
									autofocus : 'autofocus',
									onChange : function ( api ){
										if ( this.getValue().length > 0 ){
											this.getDialog().getContentElement( 'youtubePlugin', 'txtUrl' ).disable();
										}
										else{
											this.getDialog().getContentElement( 'youtubePlugin', 'txtUrl' ).enable();
										}
									},
									validate : function() {
										if ( this.isEnabled() ){
											if ( !this.getValue() )
											{
												alert( editor.lang.youtube.noCode );
												return false;
											}
											else if (!(/https?\:\/\//.test(this.getValue()))) {
												alert( editor.lang.youtube.invalidEmbed );
												return false;
											}
										}
									}
								},
								{
									type : 'html',
									html : editor.lang.youtube.or + '<hr>'
								},
								{
									type : 'hbox',
									widths : [ '70%', '15%', '15%' ],
									children :
									[
										{
											id : 'txtUrl',
											type : 'text',
											label : editor.lang.youtube.txtUrl,
											onChange : function ( api ){
												if ( this.getValue().length > 0 ){
													this.getDialog().getContentElement( 'youtubePlugin', 'txtEmbed' ).disable();
												}
												else {
													this.getDialog().getContentElement( 'youtubePlugin', 'txtEmbed' ).enable();
												}
											},
											validate : function() {
												if ( this.isEnabled() ){
													if ( !this.getValue() )
													{
														alert( editor.lang.youtube.noCode );
														return false;
													}
													else if (!(/https?\:\/\//.test(this.getValue()))) {
														alert( editor.lang.youtube.invalidUrl );
														return false;
													}
												}
											}
										},
										{
											type : 'text',
											id : 'txtWidth',
											width : '60px',
											label : editor.lang.youtube.txtWidth,
											'default' : '640'
										},
										{
											type : 'text',
											id : 'txtHeight',
											width : '60px',
											label : editor.lang.youtube.txtHeight,
											'default' : '360'
										}
									]
								}
							]
						}
					],
					onOk: function() {
						var content = '';

						if ( this.getContentElement( 'youtubePlugin', 'txtEmbed' ).isEnabled() )
						{
							content = this.getValueOf( 'youtubePlugin', 'txtEmbed' ).replace('http:', 'https:');
						}
						else {
							var url = this.getValueOf( 'youtubePlugin', 'txtUrl' );
							var width = this.getValueOf( 'youtubePlugin', 'txtWidth' );
							var height = this.getValueOf( 'youtubePlugin', 'txtHeight' );
							var urlSplit = url.split('?');
							var video = urlSplit.length && urlSplit[1] ? jQuery.parseQuerystring(urlSplit[1]).v : '';
							if(video) {
								url = 'https://www.youtube.com/embed/' + video + '/?feature=player_detailpage';
								content = '<iframe width="' + width + '" height="' + height + '" src="' + url + '" frameborder="0" allowfullscreen></iframe>';
 							}
						}

						var instance = this.getParentEditor();
						instance.insertHtml( content );

						this.getContentElement( 'youtubePlugin', 'txtEmbed' ).enable();
						this.getContentElement( 'youtubePlugin', 'txtUrl' ).enable();
					}
				};
			});
		}
	});
})();
