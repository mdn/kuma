/*
* YouTube Embed Plugin
*
* @author Jonnas Fonini <contato@fonini.net>
* @version 0.1
* https://github.com/fonini/ckeditor-youtube-plugin
*
* REVISED BY MDN CONTENT TEAM:
*   This plugin now inserts a KumaScript macro into the page instead of
*   directly inserting an <iframe> element.
*/

'use strict';

( function() {

	CKEDITOR.plugins.add( 'mdn-youtube',
	{
		icons: 'youtube-moono', // %REMOVE_LINE_CORE%

		init: function( editor )
		{
			// Backport language
			editor.lang['mdn-youtube'] = {
				button : gettext('Embed YouTube Video'),
				title : gettext('Locate a YouTube Video'),
				txtEmbed : gettext('Paste Embed Code Here'),
				txtUrl : gettext('Paste YouTube Video URL'),
				txtAspect : gettext('Aspect ratio'),
				noCode : gettext('You must input an embed code or URL'),
				invalidEmbed : gettext('The embed code you\'ve entered doesn\'t appear to be valid'),
				invalidUrl : gettext('The URL you\'ve entered doesn\'t appear to be valid'),
				or : gettext('or'),
				defaultStr : gettext("Default")
			};

			editor.addCommand( 'mdn-youtube', new CKEDITOR.dialogCommand( 'mdn-youtube' ) );

			editor.ui.addButton( 'mdn-youtube',
			{
				icon: 'youtube-moono',
				label: editor.lang['mdn-youtube'].button,
				command: 'mdn-youtube',
				toolbar: 'insert'
			});

			CKEDITOR.dialog.add( 'mdn-youtube', function ( instance )
			{
				return {
					title : editor.lang['mdn-youtube'].title,
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
									label : editor.lang['mdn-youtube'].txtEmbed,
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
												alert( editor.lang['mdn-youtube'].noCode );
												return false;
											}
											else if (!(/https?\:\/\//.test(this.getValue()))) {
												alert( editor.lang['mdn-youtube'].invalidEmbed );
												return false;
											}
										}
									}
								},
								{
									type : 'html',
									html : editor.lang['mdn-youtube'].or + '<hr>'
								},
								{
									type : 'hbox',
									widths : [ '70%', '30%' ],
									children :
									[
										{
											id : 'txtUrl',
											type : 'text',
											label : editor.lang['mdn-youtube'].txtUrl,
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
														alert( editor.lang['mdn-youtube'].noCode );
														return false;
													}
													else if (!(/https?\:\/\//.test(this.getValue()))) {
														alert( editor.lang['mdn-youtube'].invalidUrl );
														return false;
													}
												}
											}
										},
										{
											type : 'select',
											id : 'txtAspect',
											label : editor.lang['mdn-youtube'].txtAspect,
											items : [ ['Default'], ['4:3'], ['16:9'] ],
											'default' : 'Default'
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
							var aspect = this.getValueOf( 'youtubePlugin', 'txtAspect' );
							var aspectArg = (aspect == '4:3') ? ', "4:3"' : '';
							var urlSplit = url.split('?');
							var video = urlSplit.length && urlSplit[1] ? jQuery.parseQuerystring(urlSplit[1]).v : '';
							if (video) {
							    content = '{{EmbedYouTube("' + video + '"' + aspectArg + ')}}';
								//url = 'https://www.youtube.com/embed/' + video + '/?feature=player_detailpage';
								//content = '<iframe width="' + width + '" height="' + height + '" src="' + url + '" frameborder="0" allowfullscreen></iframe>';
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
