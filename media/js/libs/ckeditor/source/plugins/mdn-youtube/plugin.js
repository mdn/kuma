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
				txtUrl : gettext('Paste YouTube Video URL'),
				txtAspect : gettext('Aspect ratio'),
				noCode : gettext('You must input a valid YouTube video URL.'),
				invalidUrl : gettext('The URL you\'ve entered doesn\'t appear to be valid'),
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
					width: 500,
					height: 120,
					resizable: CKEDITOR.DIALOG_RESIZE_NONE,
					contents :
						[{
							id : 'youtubePlugin',
							expand : true,
							elements :
								[{
									type : 'hbox',
									widths : [ '70%', '30%' ],
									children :
									[
										{
											id : 'txtUrl',
											type : 'text',
											label : editor.lang['mdn-youtube'].txtUrl,
											validate : function() {
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

                        var url = this.getValueOf( 'youtubePlugin', 'txtUrl' );
                        var aspect = this.getValueOf( 'youtubePlugin', 'txtAspect' );
                        var aspectArg = (aspect == '4:3') ? ', "4:3"' : '';
                        var urlSplit = url.split('?');
                        var video = urlSplit.length && urlSplit[1] ? jQuery.parseQuerystring(urlSplit[1]).v : '';
                        if (video) {
                            content = '{{EmbedYouTube("' + video + '"' + aspectArg + ')}}';
                        }

						var instance = this.getParentEditor();
						instance.insertHtml( content );
					}
				};
			});
		}
	});
})();
