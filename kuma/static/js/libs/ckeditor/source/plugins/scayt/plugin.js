'use strict';
CKEDITOR.plugins.add('scayt', {

	//requires : ['menubutton', 'dialog'],
	requires: 'menubutton,dialog',
	lang: 'af,ar,bg,bn,bs,ca,cs,cy,da,de,el,en-au,en-ca,en-gb,en,eo,es,et,eu,fa,fi,fo,fr-ca,fr,gl,gu,he,hi,hr,hu,is,it,ja,ka,km,ko,lt,lv,mk,mn,ms,nb,nl,no,pl,pt-br,pt,ro,ru,sk,sl,sr-latn,sr,sv,th,tr,ug,uk,vi,zh-cn,zh', // %REMOVE_LINE_CORE%
	icons: 'scayt', // %REMOVE_LINE_CORE%
	hidpi: true, // %REMOVE_LINE_CORE%
	tabToOpen : null,
	dialogName: 'scaytDialog',
	init: function(editor) {
		var self = this,
			plugin = CKEDITOR.plugins.scayt;

		this.bindEvents(editor);
		this.parseConfig(editor);
		this.addRule(editor);

		// source mode
		CKEDITOR.dialog.add(this.dialogName, CKEDITOR.getUrl(this.path + 'dialogs/options.js'));
		// end source mode

		this.addMenuItems(editor);
		var config = editor.config,
			lang = editor.lang.scayt,
			env = CKEDITOR.env;

		editor.ui.add('Scayt', CKEDITOR.UI_MENUBUTTON, {
			label : lang.text_title,
			title : ( editor.plugins.wsc ? editor.lang.wsc.title : lang.text_title ),
			// SCAYT doesn't work in IE Compatibility Mode and IE (8 & 9) Quirks Mode
			modes : {wysiwyg: !(env.ie && ( env.version < 8 || env.quirks ) ) },
			toolbar: 'spellchecker,20',
			refresh: function() {
				var buttonState = editor.ui.instances.Scayt.getState();

				// check if scayt is created
				if(editor.scayt) {
					// check if scayt is enabled
					if(plugin.state.scayt[editor.name]) {
						buttonState = CKEDITOR.TRISTATE_ON;
					} else {
						buttonState = CKEDITOR.TRISTATE_OFF;
					}
				}

				editor.fire('scaytButtonState', buttonState);
			},
			onRender: function() {
				var that = this;

				editor.on('scaytButtonState', function(ev) {
					if(typeof ev.data !== undefined) {
						that.setState(ev.data);
					}
				});
			},
			onMenu : function() {
				var scaytInstance = editor.scayt;

				editor.getMenuItem('scaytToggle').label = editor.lang.scayt[(scaytInstance ? plugin.state.scayt[editor.name] : false) ? 'btn_disable' : 'btn_enable'];

				// If UI tab is disabled we shouldn't show menu item
				var menuDefinition = {
					scaytToggle  : CKEDITOR.TRISTATE_OFF,
					scaytOptions : scaytInstance ? CKEDITOR.TRISTATE_OFF : CKEDITOR.TRISTATE_DISABLED,
					scaytLangs   : scaytInstance ? CKEDITOR.TRISTATE_OFF : CKEDITOR.TRISTATE_DISABLED,
					scaytDict    : scaytInstance ? CKEDITOR.TRISTATE_OFF : CKEDITOR.TRISTATE_DISABLED,
					scaytAbout   : scaytInstance ? CKEDITOR.TRISTATE_OFF : CKEDITOR.TRISTATE_DISABLED,
					WSC          : editor.plugins.wsc ? CKEDITOR.TRISTATE_OFF : CKEDITOR.TRISTATE_DISABLED
				};

				if(!editor.config.scayt_uiTabs[0]) {
					delete menuDefinition.scaytOptions;
				}

				if(!editor.config.scayt_uiTabs[1]) {
					delete menuDefinition.scaytLangs;
				}

				if(!editor.config.scayt_uiTabs[2]) {
					delete menuDefinition.scaytDict;
				}

				return menuDefinition;
			}
		});

		// If the 'contextmenu' plugin is loaded, register the listeners.
		if(editor.contextMenu && editor.addMenuItems) {
			editor.contextMenu.addListener(function(element, selection) {
				var scaytInstance = editor.scayt,
					result, selectionNode;

				if(scaytInstance) {
					selectionNode = scaytInstance.getSelectionNode();

					// SCAYT shouldn't build context menu if instance isnot created or word is without misspelling or grammar problem
					if(selectionNode) {
						var items = self.menuGenerator(editor, selectionNode);

						scaytInstance.showBanner('.' + editor.contextMenu._.definition.panel.className.split(' ').join(' .'));
						result = items;
					}
				}

				return result;
			});

			editor.contextMenu._.onHide = CKEDITOR.tools.override(editor.contextMenu._.onHide, function(org) {
				return function() {
					var scaytInstance = editor.scayt;

					if(scaytInstance) {
						scaytInstance.hideBanner();
					}

					return org.apply(this);
				};
			});
		}
	},
	addMenuItems: function(editor) {
		var self = this,
			plugin = CKEDITOR.plugins.scayt,
			graytGroups = ['grayt_description', 'grayt_suggest', 'grayt_control'],
			menuGroup = 'scaytButton';

		editor.addMenuGroup(menuGroup);

		var items_order = editor.config.scayt_contextMenuItemsOrder.split('|');

		for(var pos = 0 ; pos < items_order.length ; pos++) {
			items_order[pos] = 'scayt_' + items_order[pos];
		}
		items_order = graytGroups.concat(items_order);

		if(items_order && items_order.length) {
			for(var pos = 0 ; pos < items_order.length ; pos++) {
				editor.addMenuGroup(items_order[pos], pos - 10);
			}
		}

		editor.addCommand( 'scaytToggle', {
			exec: function(editor) {
				var scaytInstance = editor.scayt;

				plugin.state.scayt[editor.name] = !plugin.state.scayt[editor.name];

				if(plugin.state.scayt[editor.name] === true) {
					if(!scaytInstance) {
						plugin.createScayt(editor);
					}
				} else {
					if(scaytInstance) {
						plugin.destroy(editor);
					}
				}
			}
		} );

		editor.addCommand( 'scaytAbout', {
			exec: function(editor) {
				var scaytInstance = editor.scayt;

				scaytInstance.tabToOpen = 'about';
				editor.lockSelection();
				editor.openDialog(self.dialogName);
			}
		} );

		editor.addCommand( 'scaytOptions', {
			exec: function(editor) {
				var scaytInstance = editor.scayt;

				scaytInstance.tabToOpen = 'options';
				editor.lockSelection();
				editor.openDialog(self.dialogName);
			}
		} );

		editor.addCommand( 'scaytLangs', {
			exec: function(editor) {
				var scaytInstance = editor.scayt;

				scaytInstance.tabToOpen = 'langs';
				editor.lockSelection();
				editor.openDialog(self.dialogName);
			}
		} );

		editor.addCommand( 'scaytDict', {
			exec: function(editor) {
				var scaytInstance = editor.scayt;

				scaytInstance.tabToOpen = 'dictionaries';
				editor.lockSelection();
				editor.openDialog(self.dialogName);
			}
		} );

		var uiMenuItems = {
			scaytToggle: {
				label : editor.lang.scayt.btn_enable,
				group : menuGroup,
				command: 'scaytToggle'
			},
			scaytAbout: {
				label : editor.lang.scayt.btn_about,
				group : menuGroup,
				command: 'scaytAbout'
			},
			scaytOptions: {
				label : editor.lang.scayt.btn_options,
				group : menuGroup,
				command: 'scaytOptions'
			},
			scaytLangs: {
				label : editor.lang.scayt.btn_langs,
				group : menuGroup,
				command: 'scaytLangs'
			},
			scaytDict: {
				label : editor.lang.scayt.btn_dictionaries,
				group : menuGroup,
				command: 'scaytDict'
			}
		};

		if(editor.plugins.wsc) {
			uiMenuItems.WSC = {
				label : editor.lang.wsc.toolbar,
				group : menuGroup,
				onClick: function() {
					var inlineMode = (editor.elementMode == CKEDITOR.ELEMENT_MODE_INLINE),
						plugin = CKEDITOR.plugins.scayt,
						scaytInstance = editor.scayt,
						text = inlineMode ? editor.container.getText() : editor.document.getBody().getText();

					text = text.replace(/\s/g, '');

					if(text) {
						if(scaytInstance && plugin.state.scayt[editor.name] && scaytInstance.setMarkupPaused) {
							scaytInstance.setMarkupPaused(true);
						}

						editor.lockSelection();
						editor.execCommand('checkspell');
					} else {
						alert('Nothing to check!');
					}
				}
			}
		}

		editor.addMenuItems(uiMenuItems);
	},
	bindEvents: function(editor) {
		var self = this,
			plugin = CKEDITOR.plugins.scayt,
			inline_mode = (editor.elementMode == CKEDITOR.ELEMENT_MODE_INLINE);

		var scaytDestroy = function() {
			plugin.destroy(editor);
		};

		var contentDomReady = function() {
			// The event is fired when editable iframe node was reinited so we should restart our service
			if (plugin.state.scayt[editor.name] && !editor.readOnly && !editor.scayt) {
				plugin.createScayt(editor);
			}
		};

		var addMarkupStateHandlers = function() {
			var editable = editor.editable();

			editable.attachListener( editable, 'focus', function( evt ) {
				if( CKEDITOR.plugins.scayt && !editor.scayt ) {
					setTimeout(contentDomReady, 0); // we need small timeout in order to correctly set initial 'focused' option value in SCAYT core
				}

				var pluginStatus = CKEDITOR.plugins.scayt && CKEDITOR.plugins.scayt.state.scayt[editor.name] && editor.scayt,
					selectedElement, ranges, textLength, range;

				if((inline_mode ? true : pluginStatus) && editor._.savedSelection) {
					selectedElement = editor._.savedSelection.getSelectedElement();
					ranges = !selectedElement && editor._.savedSelection.getRanges();

					for(var i = 0; i < ranges.length; i++) {
						range = ranges[i];
						// we need to check type of node value in order to avoid error in IE when accessing 'nodeValue' property
						if(typeof range.startContainer.$.nodeValue === 'string') {
							textLength = range.startContainer.getText().length;
							if(textLength < range.startOffset || textLength < range.endOffset) {
								editor.unlockSelection(false);
							}
						}
					}
				}
			}, this, null, -10 );	// priority "-10" is set to call SCAYT CKEDITOR.editor#unlockSelection before CKEDITOR.editor#unlockSelection call
		};

		var contentDomHandler = function() {
			if(inline_mode) {

				if (!editor.config.scayt_inlineModeImmediateMarkup) {
					editor.on('blur', scaytDestroy);
					editor.on('focus', contentDomReady);

					// We need to check if editor has focus(created) right now.
					// If editor is active - make attempt to create scayt
					if(editor.focusManager.hasFocus) {
						contentDomReady();
					}

				} else {
					contentDomReady();
				}

			} else {
				contentDomReady();
			}

			addMarkupStateHandlers();
		};

		editor.on('contentDom', contentDomHandler);

		editor.on('beforeCommandExec', function(ev) {
			var scaytInstance = editor.scayt,
				selectedLangElement = null,
				forceBookmark = false,
				removeMarkupInsideSelection = true;

			// TODO: after switching in source mode not recreate SCAYT instance, try to just rerun markuping to don't make requests to server
			if(ev.data.name in plugin.options.disablingCommandExec && editor.mode == 'wysiwyg') {
				if(scaytInstance) {
					plugin.destroy(editor);
					editor.fire('scaytButtonState', CKEDITOR.TRISTATE_DISABLED);
				}
			} else if(	ev.data.name === 'bold' || ev.data.name === 'italic' || ev.data.name === 'underline' ||
						ev.data.name === 'strike' || ev.data.name === 'subscript' || ev.data.name === 'superscript' ||
						ev.data.name === 'enter' || ev.data.name === 'cut' || ev.data.name === 'language') {
				if(scaytInstance) {
					if(ev.data.name === 'cut') {
						removeMarkupInsideSelection = false;
						// We need to force bookmark before we remove our markup.
						// Otherwise we will get issues with cutting text via context menu.
						forceBookmark = true;
					}

					// We need to remove all SCAYT markup from 'lang' node before it will be deleted.
					// We need to remove SCAYT markup from selected text before creating 'lang' node as well.
					if(ev.data.name === 'language') {
						selectedLangElement = editor.plugins.language.getCurrentLangElement(editor);
						selectedLangElement = selectedLangElement && selectedLangElement.$;
						// We need to force bookmark before we remove our markup.
						// Otherwise we will get issues with cutting text via language plugin menu.
						forceBookmark = true;
					}

					editor.fire('reloadMarkupScayt', {
						removeOptions: {
							removeInside: removeMarkupInsideSelection,
							forceBookmark: forceBookmark,
							selectionNode: selectedLangElement
						},
						timeout: 0
					});
				}
			}
		});

		editor.on('beforeSetMode', function(ev) {
			var scaytInstance;
			// needed when we use:
			// CKEDITOR.instances.editor_ID.setMode("source")
			// CKEDITOR.instances.editor_ID.setMode("wysiwyg")
			// can't be implemented in editor.on('mode', function(ev) {});
			if (ev.data == 'source') {
				scaytInstance = editor.scayt;
				if(scaytInstance) {
					plugin.destroy(editor);
					editor.fire('scaytButtonState', CKEDITOR.TRISTATE_DISABLED);
				}

				// remove custom data from body, to prevent waste properties showing in IE8
				if(editor.document) { //GitHub #84 : make sure that document exists(e.g. when startup mode set to 'source')
					editor.document.getBody().removeAttribute('_jquid');
				}
			}
		});

		editor.on('afterCommandExec', function(ev) {
			var scaytInstance = editor.scayt;

			if(editor.mode == 'wysiwyg' && (ev.data.name == 'undo' || ev.data.name == 'redo')) {
				if(scaytInstance) {
					setTimeout(function() {
						scaytInstance.fire('startSpellCheck, startGrammarCheck');
					}, 250);
				}
			}
		});

		// handle readonly changes
		editor.on('readOnly', function(ev) {
			var scaytInstance;

			if(ev) {
				scaytInstance = editor.scayt;

				if(ev.editor.readOnly === true) {
					if(scaytInstance) {
						scaytInstance.fire('removeMarkupInDocument', {});
					}
				} else {
					if(scaytInstance) {
						scaytInstance.fire('startSpellCheck, startGrammarCheck');
					} else if(ev.editor.mode == 'wysiwyg' && plugin.state.scayt[ev.editor.name] === true) {
						plugin.createScayt(editor);
						ev.editor.fire('scaytButtonState', CKEDITOR.TRISTATE_ON);
					}
				}
			}
		});

		// we need to destroy SCAYT before CK editor will be completely destroyed
		editor.on('beforeDestroy', scaytDestroy);

		//#9439 after SetData method fires contentDom event and SCAYT create additional instanse
		// This way we should destroy SCAYT on setData event when contenteditable Iframe was re-created
		editor.on('setData', function() {
			scaytDestroy();

			// in inline mode SetData does not fire contentDom event
			if(editor.elementMode == CKEDITOR.ELEMENT_MODE_INLINE || editor.plugins.divarea) {
				contentDomHandler();
			}
		}, this, null, 50);

		editor.on('reloadMarkupScayt', function(ev) {
			var scaytInstance = editor.scayt,
				removeOptions = ev.data && ev.data.removeOptions,
				timeout = ev.data && ev.data.timeout;

			if (scaytInstance) {
				scaytInstance.removeMarkupInSelectionNode(removeOptions);
				if(typeof timeout === 'number') {
					setTimeout(function() {
						scaytInstance.fire('startSpellCheck, startGrammarCheck');
					}, timeout);
				} else {
					scaytInstance.fire('startSpellCheck, startGrammarCheck');
				}
			}
		});

		// Reload spell-checking for current word after insertion completed.
		editor.on('insertElement', function() {
			// IE bug: we need wait here to make sure that focus is returned to editor, and we can store the selection before we proceed with markup
			editor.fire('reloadMarkupScayt', {removeOptions: {forceBookmark: true}});
		}, this, null, 50);

		editor.on('insertHtml', function() {
			editor.fire('reloadMarkupScayt');
		}, this, null, 50);

		editor.on('insertText', function() {
			editor.fire('reloadMarkupScayt');
		}, this, null, 50);

		// The event is listening to open necessary dialog tab
		editor.on('scaytDialogShown', function(ev) {
			var dialog = ev.data,
				scaytInstance = editor.scayt;

			dialog.selectPage(scaytInstance.tabToOpen);
		});

		editor.on('paste', function(ev) {
			var scaytInstance = editor.scayt;

			if(scaytInstance) {
				scaytInstance.removeMarkupInSelectionNode();
			}
		}, null, null, 0);
	},
	parseConfig: function(editor) {
		var plugin = CKEDITOR.plugins.scayt,
			inlineMode = (editor.elementMode == CKEDITOR.ELEMENT_MODE_INLINE);

		// preprocess config for backward compatibility
		plugin.replaceOldOptionsNames(editor.config);

		// Checking editor's config after initialization
		if(typeof editor.config.scayt_autoStartup !== 'boolean') {
			editor.config.scayt_autoStartup = false;
		}
		plugin.state.scayt[editor.name] = editor.config.scayt_autoStartup;

		if(typeof editor.config.grayt_autoStartup !== 'boolean' || inlineMode || editor.plugins.divarea) {
			editor.config.grayt_autoStartup = false;
		}
		if(typeof editor.config.scayt_inlineModeImmediateMarkup !== 'boolean') {
			editor.config.scayt_inlineModeImmediateMarkup = false;
		}
		plugin.state.grayt[editor.name] = editor.config.grayt_autoStartup;

		if(!editor.config.scayt_contextCommands) {
			editor.config.scayt_contextCommands = 'ignore|ignoreall|add';
		}

		if(!editor.config.scayt_contextMenuItemsOrder) {
			editor.config.scayt_contextMenuItemsOrder = 'suggest|moresuggest|control';
		}

		if(!editor.config.scayt_sLang) {
			editor.config.scayt_sLang = 'en_US';
		}

		if(editor.config.scayt_maxSuggestions === undefined || typeof editor.config.scayt_maxSuggestions != 'number' || editor.config.scayt_maxSuggestions < 0) {
			editor.config.scayt_maxSuggestions = 5;
		}

		if(editor.config.scayt_minWordLength === undefined || typeof editor.config.scayt_minWordLength != 'number' || editor.config.scayt_minWordLength < 1) {
			editor.config.scayt_minWordLength = 4;
		}

		if(editor.config.scayt_customDictionaryIds === undefined || typeof editor.config.scayt_customDictionaryIds !== 'string') {
			editor.config.scayt_customDictionaryIds = '';
		}

		if(editor.config.scayt_userDictionaryName === undefined || typeof editor.config.scayt_userDictionaryName !== 'string') {
			editor.config.scayt_userDictionaryName = null;
		}

		if(typeof editor.config.scayt_uiTabs === 'string' && editor.config.scayt_uiTabs.split(',').length === 3) {
			var scayt_uiTabs = [], _tempUITabs = [];
			editor.config.scayt_uiTabs = editor.config.scayt_uiTabs.split(',');

			CKEDITOR.tools.search(editor.config.scayt_uiTabs, function(value) {
				if (Number(value) === 1 || Number(value) === 0) {
					_tempUITabs.push(true);
					scayt_uiTabs.push(Number(value));
				} else {
					_tempUITabs.push(false);
				}
			});

			if (CKEDITOR.tools.search(_tempUITabs, false) === null) {
				editor.config.scayt_uiTabs = scayt_uiTabs;
			} else {
				editor.config.scayt_uiTabs = [1,1,1];
			}

		} else {
			editor.config.scayt_uiTabs = [1,1,1];
		}

		if(typeof editor.config.scayt_serviceProtocol != 'string') {
			editor.config.scayt_serviceProtocol = null;
		}

		if(typeof editor.config.scayt_serviceHost != 'string') {
			editor.config.scayt_serviceHost = null;
		}

		if(typeof editor.config.scayt_servicePort != 'string') {
			editor.config.scayt_servicePort = null;
		}

		if(typeof editor.config.scayt_servicePath != 'string') {
			editor.config.scayt_servicePath = null;
		}

		if(!editor.config.scayt_moreSuggestions) {
			editor.config.scayt_moreSuggestions = 'on';
		}

		if(typeof editor.config.scayt_customerId !== 'string') {
			editor.config.scayt_customerId = '1:WvF0D4-UtPqN1-43nkD4-NKvUm2-daQqk3-LmNiI-z7Ysb4-mwry24-T8YrS3-Q2tpq2';
		}

		if(typeof editor.config.scayt_srcUrl !== 'string') {
			var protocol = document.location.protocol;
			protocol = protocol.search(/https?:/) != -1 ? protocol : 'http:';

			editor.config.scayt_srcUrl = protocol + '//svc.webspellchecker.net/spellcheck31/lf/scayt3/ckscayt/ckscayt.js';
		}

		if(typeof CKEDITOR.config.scayt_handleCheckDirty !== 'boolean') {
			CKEDITOR.config.scayt_handleCheckDirty = true;
		}

		if(typeof CKEDITOR.config.scayt_handleUndoRedo !== 'boolean') {
			CKEDITOR.config.scayt_handleUndoRedo = true;
		}

		if(typeof editor.config.scayt_multiLanguageMode !== 'boolean') {
			editor.config.scayt_multiLanguageMode = false;
		}

		if(typeof editor.config.scayt_multiLanguageStyles !== 'object') {
			editor.config.scayt_multiLanguageStyles = {};
		}

		if( editor.config.scayt_disableOptionsStorage ) {
			var userOptions = CKEDITOR.tools.isArray( editor.config.scayt_disableOptionsStorage ) ? editor.config.scayt_disableOptionsStorage : ( typeof editor.config.scayt_disableOptionsStorage === 'string' ) ? [ editor.config.scayt_disableOptionsStorage ] : undefined,
				availableValue = [ 'all', 'options', 'lang', 'ignore-all-caps-words', 'ignore-domain-names', 'ignore-words-with-mixed-cases', 'ignore-words-with-numbers'],
				valuesOption = ['lang', 'ignore-all-caps-words', 'ignore-domain-names', 'ignore-words-with-mixed-cases', 'ignore-words-with-numbers'],
				search = CKEDITOR.tools.search,
				indexOf = CKEDITOR.tools.indexOf;

			var isValidOption = function( option ) {
				return !!search( availableValue, option );
			};

			var makeOptionsToStorage = function( options ) {
				var retval = [];

				for (var i = 0; i < options.length; i++) {
					var value = options[i],
						isGroupOptionInUserOptions = !!search( options, 'options' );

					if( !isValidOption( value ) || isGroupOptionInUserOptions && !!search( valuesOption, function( val ) { if( val === 'lang' ) { return false; } } ) ) {
						return;
					}

					if( !!search( valuesOption, value ) ) {
						valuesOption.splice( indexOf( valuesOption, value ), 1 );
					}

					if(  value === 'all' || isGroupOptionInUserOptions && !!search( options, 'lang' )) {
						return [];
					}

					if( value === 'options' ) {
						valuesOption = [ 'lang' ];
					}
				}

				retval = retval.concat( valuesOption );

				return retval;
			};

			editor.config.scayt_disableOptionsStorage = makeOptionsToStorage( userOptions );
		}
	},
	addRule: function(editor) {
		var plugin = CKEDITOR.plugins.scayt,
			dataProcessor = editor.dataProcessor,
			htmlFilter = dataProcessor && dataProcessor.htmlFilter,
			pathFilters = editor._.elementsPath && editor._.elementsPath.filters,
			dataFilter = dataProcessor && dataProcessor.dataFilter,
			removeFormatFilter = editor.addRemoveFormatFilter,
			pathFilter = function(element) {
				var scaytInstance = editor.scayt;

				if( scaytInstance && (element.hasAttribute(plugin.options.data_attribute_name) || element.hasAttribute(plugin.options.problem_grammar_data_attribute)) ) {
					return false;
				}
			},
			removeFormatFilterTemplate = function(element) {
				var scaytInstance = editor.scayt,
					result = true;

				if( scaytInstance && (element.hasAttribute(plugin.options.data_attribute_name) || element.hasAttribute(plugin.options.problem_grammar_data_attribute)) ) {
					result = false;
				}

				return result;
			};

		if(pathFilters) {
			pathFilters.push(pathFilter);
		}

		if(dataFilter) {
			var dataFilterRules = {
				elements: {
					span: function(element) {

						var scaytState = element.hasClass(plugin.options.misspelled_word_class) && element.attributes[plugin.options.data_attribute_name],
							graytState = element.hasClass(plugin.options.problem_grammar_class) && element.attributes[plugin.options.problem_grammar_data_attribute];

						if(plugin && (scaytState || graytState)) {
							delete element.name;
						}

						return element;
					}
				}
			};

			dataFilter.addRules(dataFilterRules);
		}

		if (htmlFilter) {
			var htmlFilterRules = {
				elements: {
					span: function(element) {

						var scaytState = element.hasClass(plugin.options.misspelled_word_class) && element.attributes[plugin.options.data_attribute_name],
							graytState = element.hasClass(plugin.options.problem_grammar_class) && element.attributes[plugin.options.problem_grammar_data_attribute];

						if(plugin && (scaytState || graytState)) {
							delete element.name;
						}

						return element;
					}
				}
			};

			htmlFilter.addRules(htmlFilterRules);
		}

		if(removeFormatFilter) {
			removeFormatFilter.call(editor, removeFormatFilterTemplate);
		}
	},
	scaytMenuDefinition: function(editor) {
		var self = this,
			plugin = CKEDITOR.plugins.scayt,
			scayt_instance =  editor.scayt;

		return {
			scayt: {
				scayt_ignore: {
					label:  scayt_instance.getLocal('btn_ignore'),
					group : 'scayt_control',
					order : 1,
					exec: function(editor) {
						var scaytInstance = editor.scayt;
						scaytInstance.ignoreWord();
					}
				},
				scayt_ignoreall: {
					label : scayt_instance.getLocal('btn_ignoreAll'),
					group : 'scayt_control',
					order : 2,
					exec: function(editor) {
						var scaytInstance = editor.scayt;
						scaytInstance.ignoreAllWords();
					}
				},
				scayt_add: {
					label : scayt_instance.getLocal('btn_addWord'),
					group : 'scayt_control',
					order : 3,
					exec : function(editor) {
						var scaytInstance = editor.scayt;

						// @TODO: We need to add set/restore bookmark logic to 'addWordToUserDictionary' method inside dictionarymanager.
						// Timeout is used as tmp fix for IE9, when after hitting 'Add word' menu item, document container was blurred.
						setTimeout(function() {
							scaytInstance.addWordToUserDictionary();
						}, 10);
					}
				},
				scayt_option: {
					label : scayt_instance.getLocal('btn_options'),
					group : 'scayt_control',
					order : 4,
					exec: function(editor) {
						var scaytInstance = editor.scayt;

						scaytInstance.tabToOpen = 'options';
						editor.lockSelection();
						editor.openDialog(self.dialogName);
					},
					verification: function(editor) {
						return (editor.config.scayt_uiTabs[0] == 1) ? true : false;
					}
				},
				scayt_language: {
					label : scayt_instance.getLocal('btn_langs'),
					group : 'scayt_control',
					order : 5,
					exec: function(editor) {
						var scaytInstance = editor.scayt;

						scaytInstance.tabToOpen = 'langs';
						editor.lockSelection();
						editor.openDialog(self.dialogName);
					},
					verification: function(editor) {
						return (editor.config.scayt_uiTabs[1] == 1) ? true : false;
					}
				},
				scayt_dictionary: {
					label : scayt_instance.getLocal('btn_dictionaries'),
					group : 'scayt_control',
					order : 6,
					exec: function(editor) {
						var scaytInstance = editor.scayt;

						scaytInstance.tabToOpen = 'dictionaries';
						editor.lockSelection();
						editor.openDialog(self.dialogName);
					},
					verification: function(editor) {
						return (editor.config.scayt_uiTabs[2] == 1) ? true : false;
					}
				},
				scayt_about: {
					label : scayt_instance.getLocal('btn_about'),
					group : 'scayt_control',
					order : 7,
					exec: function(editor) {
						var scaytInstance = editor.scayt;

						scaytInstance.tabToOpen = 'about';
						editor.lockSelection();
						editor.openDialog(self.dialogName);
					}
				}
			},
			grayt: {
				grayt_problemdescription: {
					label : 'Grammar problem description',
					group : 'grayt_description', // look at addMenuItems method for further info
					order : 1,
					state : CKEDITOR.TRISTATE_DISABLED,
					exec: function(editor) {}
				},
				grayt_ignore: {
					label : scayt_instance.getLocal('btn_ignore'),
					group : 'grayt_control',
					order : 2,
					exec: function(editor) {
						var scaytInstance = editor.scayt;

						scaytInstance.ignorePhrase();
					}
				}
			}
		};
	},
	buildSuggestionMenuItems: function(editor, suggestions, isScaytNode) {
		var self = this,
			itemList = {},
			subItemList = {},
			replaceKeyName = isScaytNode ? 'word' : 'phrase',
			updateEventName = isScaytNode ? 'startGrammarCheck' : 'startSpellCheck',
			plugin = CKEDITOR.plugins.scayt,
			scayt_instance = editor.scayt;

		if(suggestions.length > 0 && suggestions[0] !== 'no_any_suggestions') {

			if(isScaytNode) {
				// build SCAYT suggestions
				for(var i = 0; i < suggestions.length; i++) {

					var commandName = 'scayt_suggest_' + CKEDITOR.plugins.scayt.suggestions[i].replace(' ', '_');

					editor.addCommand(commandName, self.createCommand(CKEDITOR.plugins.scayt.suggestions[i], replaceKeyName, updateEventName));

					if(i < editor.config.scayt_maxSuggestions) {

						// mainSuggestions
						editor.addMenuItem(commandName, {
							label: suggestions[i],
							command: commandName,
							group: 'scayt_suggest',
							order: i + 1
						});

						itemList[commandName] = CKEDITOR.TRISTATE_OFF;

					} else {

						// moreSuggestions
						editor.addMenuItem(commandName, {
							label: suggestions[i],
							command: commandName,
							group: 'scayt_moresuggest',
							order: i + 1
						});

						subItemList[commandName] = CKEDITOR.TRISTATE_OFF;

						if(editor.config.scayt_moreSuggestions === 'on') {

							editor.addMenuItem('scayt_moresuggest', {
								label : scayt_instance.getLocal('btn_moreSuggestions'),
								group : 'scayt_moresuggest',
								order : 10,
								getItems : function() {
									return subItemList;
								}
							});

							itemList['scayt_moresuggest'] = CKEDITOR.TRISTATE_OFF;
						}
					}
				}
			} else {
				// build GRAYT suggestions
				for(var i = 0; i < suggestions.length; i++) {
					var commandName = 'grayt_suggest_' + CKEDITOR.plugins.scayt.suggestions[i].replace(' ', '_');

					editor.addCommand(commandName, self.createCommand(CKEDITOR.plugins.scayt.suggestions[i], replaceKeyName, updateEventName));

					// mainSuggestions
					editor.addMenuItem(commandName, {
						label: suggestions[i],
						command: commandName,
						group: 'grayt_suggest',
						order: i + 1
					});

					itemList[commandName] = CKEDITOR.TRISTATE_OFF;
				}
			}
		} else {
			var noSuggestionsCommand = 'no_scayt_suggest';
			itemList[noSuggestionsCommand] = CKEDITOR.TRISTATE_DISABLED;

			editor.addCommand(noSuggestionsCommand, {
				exec: function() {

				}
			});

			editor.addMenuItem(noSuggestionsCommand, {
				label : scayt_instance.getLocal('btn_noSuggestions') || noSuggestionsCommand,
				command: noSuggestionsCommand,
				group : 'scayt_suggest',
				order : 0
			});
		}

		return itemList;
	},
	menuGenerator: function(editor, selectionNode) {
		var self = this,
			scaytInstance = editor.scayt,
			menuItems = this.scaytMenuDefinition(editor),
			itemList = {},
			allowedOption = editor.config.scayt_contextCommands.split('|'),
			lang = selectionNode.getAttribute(scaytInstance.getLangAttribute()) || scaytInstance.getLang(),
			word, grammarPhrase, isScaytNode, isGrammarNode, problemDescriptionText;


		isScaytNode = scaytInstance.isScaytNode(selectionNode);
		isGrammarNode = scaytInstance.isGraytNode(selectionNode);

		if(isScaytNode) {
			// we clicked scayt misspelling
			// get suggestions
			menuItems = menuItems.scayt;

			word = selectionNode.getAttribute(scaytInstance.getScaytNodeAttributeName());

			scaytInstance.fire('getSuggestionsList', {
				lang: lang,
				word: word
			});

			itemList = this.buildSuggestionMenuItems(editor, CKEDITOR.plugins.scayt.suggestions, isScaytNode);
		} else if(isGrammarNode) {
			// we clicked grammar problem
			// get suggestions
			menuItems = menuItems.grayt;
			grammarPhrase = selectionNode.getAttribute(scaytInstance.getGraytNodeAttributeName());

			// setup grammar problem description
			problemDescriptionText = scaytInstance.getProblemDescriptionText(grammarPhrase, lang);
			if(menuItems.grayt_problemdescription && problemDescriptionText) {
				menuItems.grayt_problemdescription.label = problemDescriptionText;
			}

			scaytInstance.fire('getGrammarSuggestionsList', {
				lang: lang,
				phrase: grammarPhrase
			});

			itemList = this.buildSuggestionMenuItems(editor, CKEDITOR.plugins.scayt.suggestions, isScaytNode);
		}

		if(isScaytNode && editor.config.scayt_contextCommands == 'off') {
			return itemList;
		}

		for(var key in menuItems) {
			if(isScaytNode && CKEDITOR.tools.indexOf(allowedOption, key.replace('scayt_', '')) == -1 && editor.config.scayt_contextCommands != 'all') {
				continue;
			}

			if(typeof menuItems[key].state != 'undefined') {
				itemList[key] = menuItems[key].state;
			} else {
				itemList[key] = CKEDITOR.TRISTATE_OFF;
			}

			// delete item from context menu if its state isn't verified as allowed
			if(typeof menuItems[key].verification === 'function' && !menuItems[key].verification(editor)) {
				// itemList[key] = (menuItems[key].verification(editor)) ? CKEDITOR.TRISTATE_OFF : CKEDITOR.TRISTATE_DISABLED;
				delete itemList[key];
			}

			editor.addCommand(key, {
				exec: menuItems[key].exec
			});

			editor.addMenuItem(key, {
				label : editor.lang.scayt[menuItems[key].label] || menuItems[key].label,
				command: key,
				group : menuItems[key].group,
				order : menuItems[key].order
			});
		}

		return itemList;
	},
	createCommand: function(suggestion, replaceKeyName, updateEventName) {
		return {
			exec: function(editor) {
				var scaytInstance = editor.scayt,
					eventObject = {};

				eventObject[replaceKeyName] = suggestion;
				scaytInstance.replaceSelectionNode(eventObject);

				// we need to remove grammar markup from selection node if we just performed replace action for misspelling
				if(updateEventName === 'startGrammarCheck') {
					scaytInstance.removeMarkupInSelectionNode({grammarOnly: true});
				}
				// for grayt problem replacement we need to fire 'startSpellCheck'
				// for scayt misspelling replacement we need to fire 'startGrammarCheck'
				scaytInstance.fire(updateEventName);
			}
		};
	}
});

CKEDITOR.plugins.scayt = {
	state: {
		scayt: {},
		grayt: {}
	},
	suggestions: [],
	loadingHelper: {
		loadOrder: []
	},
	isLoading: false,
	options: {
		disablingCommandExec: {
			source: true,
			newpage: true,
			templates: true
		},
		data_attribute_name: 'data-scayt-word',
		misspelled_word_class: 'scayt-misspell-word',
		problem_grammar_data_attribute: 'data-grayt-phrase',
		problem_grammar_class: 'gramm-problem'
	},
	backCompatibilityMap: {
		'scayt_service_protocol': 'scayt_serviceProtocol',
		'scayt_service_host'  : 'scayt_serviceHost',
		'scayt_service_port'  : 'scayt_servicePort',
		'scayt_service_path'  : 'scayt_servicePath',
		'scayt_customerid'    : 'scayt_customerId'
	},
	replaceOldOptionsNames: function(config) {
		for(var key in config) {
			if(key in this.backCompatibilityMap) {
				config[this.backCompatibilityMap[key]] = config[key];
				delete config[key];
			}
		}
	},
	createScayt : function(editor) {
		var self = this,
			plugin = CKEDITOR.plugins.scayt;

		this.loadScaytLibrary(editor, function(_editor) {
			var container = _editor.editable().$.nodeName == 'BODY' ? _editor.document.getWindow().$.frameElement : _editor.editable().$,
				scaytInstanceOptions = {
					lang 				: _editor.config.scayt_sLang,
					container 			: _editor.editable().$.nodeName == 'BODY' ? _editor.document.getWindow().$.frameElement : _editor.editable().$,
					customDictionary 	: _editor.config.scayt_customDictionaryIds,
					userDictionaryName 	: _editor.config.scayt_userDictionaryName,
					localization 		: _editor.langCode,
					customer_id 		: _editor.config.scayt_customerId,
					debug 				: _editor.config.scayt_debug,
					data_attribute_name : self.options.data_attribute_name,
					misspelled_word_class: self.options.misspelled_word_class,
					problem_grammar_data_attribute: self.options.problem_grammar_data_attribute,
					problem_grammar_class: self.options.problem_grammar_class,
					'options-to-restore':  _editor.config.scayt_disableOptionsStorage,
					focused 			: _editor.editable().hasFocus, // #30260 we need to set focused=true if CKEditor is focused before SCAYT initialization
					ignoreElementsRegex : _editor.config.scayt_elementsToIgnore,
					minWordLength 		: _editor.config.scayt_minWordLength,
					multiLanguageMode 	: _editor.config.scayt_multiLanguageMode,
					multiLanguageStyles	: _editor.config.scayt_multiLanguageStyles,
					graytAutoStartup	: plugin.state.grayt[_editor.name]
				},
				contcontainerID;

			if(_editor.config.scayt_serviceProtocol) {
				scaytInstanceOptions['service_protocol'] = _editor.config.scayt_serviceProtocol;
			}

			if(_editor.config.scayt_serviceHost) {
				scaytInstanceOptions['service_host'] = _editor.config.scayt_serviceHost;
			}

			if(_editor.config.scayt_servicePort) {
				scaytInstanceOptions['service_port'] = _editor.config.scayt_servicePort;
			}

			if(_editor.config.scayt_servicePath) {
				scaytInstanceOptions['service_path'] = _editor.config.scayt_servicePath;
			}

			// Fix bug with getting wrong uid after re-creating SCAYT instance.
			// And as result - restoring options for wrong instance
			if(!container.id && _editor.element.getAttribute('id')) {
				container.id = _editor.element.getAttribute('id');
			}

			var scaytInstance = new SCAYT.CKSCAYT(scaytInstanceOptions, function() {
					// success callback
				}, function() {
					// error callback
				}),
				wordsPrefix = 'word_';

			scaytInstance.subscribe('suggestionListSend', function(data) {
				// TODO: 1. Maybe store suggestions for specific editor
				// TODO: 2. Fix issue with suggestion duplicates on on server
				//CKEDITOR.plugins.scayt.suggestions = data.suggestionList;
				var _wordsCollection = {},
					_suggestionList =[];

				for (var i = 0; i < data.suggestionList.length; i++) {
					if (!_wordsCollection[wordsPrefix + data.suggestionList[i]]) {
						_wordsCollection[wordsPrefix + data.suggestionList[i]] = data.suggestionList[i];
						_suggestionList.push(data.suggestionList[i]);
					}
				}

				CKEDITOR.plugins.scayt.suggestions = _suggestionList;
			});

			// if selection has changed programmatically by SCAYT we need to react appropriately
			scaytInstance.subscribe('selectionIsChanged', function(data) {
				var selection = _editor.getSelection();

				if(selection.isLocked) {
					_editor.lockSelection();
				}
			});

			scaytInstance.subscribe('graytStateChanged', function(data) {
				plugin.state.grayt[_editor.name] = data.state;
			});

			_editor.scayt = scaytInstance;

			_editor.fire('scaytButtonState', _editor.readOnly ? CKEDITOR.TRISTATE_DISABLED : CKEDITOR.TRISTATE_ON);
		});
	},
	destroy: function(editor) {
		if(editor.scayt) {
			editor.scayt.destroy();
		}

		delete editor.scayt;
		editor.fire('scaytButtonState', CKEDITOR.TRISTATE_OFF);
	},
	loadScaytLibrary: function(editor, callback) {
		var self = this,
			date,
			timestamp,
			scaytUrl;

		// no need to process load requests from same editor as it can cause bugs with
		// loading ckscayt app due to subsequent calls of some events
		// need to be before 'if' statement, because of timing issue in CKEDITOR.scriptLoader
		// when callback executing is delayed for a few milliseconds, and scayt can be created twise
		// on one instance
		if(this.loadingHelper[editor.name]) return;

		if(typeof window.SCAYT === 'undefined' || typeof window.SCAYT.CKSCAYT !== 'function') {

			// add onLoad callbacks for editors while SCAYT is loading
			this.loadingHelper[editor.name] = callback;
			this.loadingHelper.loadOrder.push(editor.name);

			//creating unique timestamp for SCAYT URL
			date = new Date();
			timestamp = date.getTime();
			scaytUrl = editor.config.scayt_srcUrl;

			//if there already implemented timstamp for scayr_srcURL use it, if not use our timestamp
			scaytUrl = scaytUrl + (scaytUrl.indexOf('?') >= 0 ? '' : '?' + timestamp);

			if (!this.loadingHelper.ckscaytLoading) {
				CKEDITOR.scriptLoader.load(scaytUrl, function(success) {
					var editorName;

					CKEDITOR.fireOnce('scaytReady');

					for(var i = 0; i < self.loadingHelper.loadOrder.length; i++) {
						editorName = self.loadingHelper.loadOrder[i];

						if(typeof self.loadingHelper[editorName] === 'function') {
							self.loadingHelper[editorName](CKEDITOR.instances[editorName]);
						}

						delete self.loadingHelper[editorName];
					}
					self.loadingHelper.loadOrder = [];
				});
				this.loadingHelper.ckscaytLoading = true;
			}


		} else if(window.SCAYT && typeof window.SCAYT.CKSCAYT === 'function') {
			CKEDITOR.fireOnce('scaytReady');

			if(!editor.scayt) {
				if(typeof callback === 'function') {
					callback(editor);
				}
			}
		}
	}
};

CKEDITOR.on('dialogDefinition', function(dialogDefinitionEvent) {
	var dialogName = dialogDefinitionEvent.data.name,
		dialogDefinition = dialogDefinitionEvent.data.definition,
		dialog = dialogDefinition.dialog;

	if (dialogName === 'scaytDialog') {
		dialog.on('cancel', function(cancelEvent) {
			return false;
		}, this, null, -1);
	}

	if (dialogName === 'link') {
		dialog.on('ok', function(okEvent) {
			var editor = okEvent.sender && okEvent.sender.getParentEditor();

			if(editor) {
				setTimeout(function() {
					editor.fire('reloadMarkupScayt', {
						removeOptions: {
							removeInside: true,
							forceBookmark: true
						},
						timeout: 0
					});
				}, 0);
			}
		});
	}
});

CKEDITOR.on('scaytReady', function() {

	// Override editor.checkDirty method avoid CK checkDirty functionality to fix SCAYT issues with incorrect checkDirty behavior.
	if(CKEDITOR.config.scayt_handleCheckDirty === true) {
		var editorCheckDirty = CKEDITOR.editor.prototype;

		editorCheckDirty.checkDirty = CKEDITOR.tools.override(editorCheckDirty.checkDirty, function(org) {

			return function() {
				var retval = null,
					pluginStatus = CKEDITOR.plugins.scayt && CKEDITOR.plugins.scayt.state.scayt[this.name] && this.scayt,
					scaytInstance = this.scayt;

				if(!pluginStatus) {
					retval = org.call(this);
				} else {
					retval = (this.status == 'ready');

					if (retval) {
						var currentData = scaytInstance.removeMarkupFromString(this.getSnapshot()),
							prevData = scaytInstance.removeMarkupFromString(this._.previousValue);

						retval = (retval && (prevData !== currentData))
					}
				}

				return retval;
			};
		});

		editorCheckDirty.resetDirty = CKEDITOR.tools.override(editorCheckDirty.resetDirty, function(org) {
			return function() {
				var pluginStatus = CKEDITOR.plugins.scayt && CKEDITOR.plugins.scayt.state.scayt[this.name] && this.scayt,
					scaytInstance = this.scayt;//CKEDITOR.plugins.scayt.getScayt(this);

				if(!pluginStatus) {
					org.call(this);
				} else {
					this._.previousValue = scaytInstance.removeMarkupFromString(this.getSnapshot());
				}
			};
		});
	}

	if (CKEDITOR.config.scayt_handleUndoRedo === true) {
		var undoImagePrototype = CKEDITOR.plugins.undo.Image.prototype;

		// add backword compatibility for CKEDITOR 4.2. method equals was repleced on other method
		var equalsContentMethodName = (typeof undoImagePrototype.equalsContent == "function") ? 'equalsContent' : 'equals';

		undoImagePrototype[equalsContentMethodName] = CKEDITOR.tools.override(undoImagePrototype[equalsContentMethodName], function(org) {
			return function(otherImage) {
				var pluginState = CKEDITOR.plugins.scayt && CKEDITOR.plugins.scayt.state.scayt[otherImage.editor.name] && otherImage.editor.scayt,
					scaytInstance = otherImage.editor.scayt,
					thisContents = this.contents,
					otherContents = otherImage.contents,
					retval = null;

				// Making the comparison based on content without SCAYT word markers.
				if(pluginState) {
					this.contents = scaytInstance.removeMarkupFromString(thisContents) || '';
					otherImage.contents = scaytInstance.removeMarkupFromString(otherContents) || '';
				}

				var retval = org.apply(this, arguments);

				this.contents = thisContents;
				otherImage.contents = otherContents;

				return retval;
			};
		});
	}
});

/**
 * The parameter turns on/off SCAYT on the autostartup. If 'true', turns on SCAYT automatically after loading the editor.
 *
 *		config.scayt_autoStartup = true;
 *
 * @cfg {Boolean} [scayt_autoStartup=false]
 * @member CKEDITOR.config
 */

/**
 * The parameter turns on/off Grammar As You Type (GRAYT) on the SCAYT startup. If 'true', turns on GRAYT automatically after SCAYT started.
 *
 *		config.grayt_autoStartup = true;
 *
 * @cfg {Boolean} [grayt_autoStartup=false]
 * @member CKEDITOR.config
 */

/**
 * The parameter turns on/off SCAYT initiation when Inline CKEditor is not focused. SCAYT markup is taken place (SCAYT instance is not destroyed)
 * in both Inline CKEditor's states, focused and unfocused.
 *
 *		 config.scayt_inlineModeImmediateMarkup = true;
 *
 * @cfg {Boolean} [scayt_inlineModeImmediateMarkup=false]
 * @member CKEDITOR.config
 */


/**
 * The parameter defines the number of SCAYT suggestions to show in the main context menu.
 * Possible values are:
 *
 * * `0` (zero) &ndash; No suggestions are shown in the main context menu. All
 *     entries will be listed in the "More Suggestions" sub-menu.
 * * Positive number &ndash; The maximum number of suggestions to show in the context
 *     menu. Other entries will be shown in the "More Suggestions" sub-menu.
 * * Negative number &ndash; 5 suggestions are shown in the main context menu. All other
 *     entries will be listed in the "More Suggestions" sub-menu.
 *
 * Examples:
 *
 *		// Display only three suggestions in the main context menu.
 *		config.scayt_maxSuggestions = 3;
 *
 *		// Do not show the suggestions directly.
 *		config.scayt_maxSuggestions = 0;
 *
 * @cfg {Number} [scayt_maxSuggestions=5]
 * @member CKEDITOR.config
 */

/**
 * The parameter defines minimum length of the words that will be collected from editor's text for spell checking.
 * Possible value is any positive number.
 *
 * Examples:
 *
 *		// Set minimum length of the words that will be collected from text.
 *		config.scayt_minWordLength = 5;
 *
 * @cfg {Number} [scayt_minWordLength=4]
 * @member CKEDITOR.config
 */

/**
 * The parameter sets the customer ID for SCAYT. Used for hosted users only. Required for migration from free
 * to trial or paid versions.
 *
 *		// Load SCAYT using my customer ID.
 *		config.scayt_customerId  = 'your-encrypted-customer-id';
 *
 * @cfg {String} [scayt_customerId='1:WvF0D4-UtPqN1-43nkD4-NKvUm2-daQqk3-LmNiI-z7Ysb4-mwry24-T8YrS3-Q2tpq2']
 * @member CKEDITOR.config
 */

/**
 * The parameter enables/disables the "More Suggestions" sub-menu in the context menu.
 * Possible values are `'on'` and `'off'`.
 *
 *		// Disables the "More Suggestions" sub-menu.
 *		config.scayt_moreSuggestions = 'off';
 *
 * @cfg {String} [scayt_moreSuggestions='on']
 * @member CKEDITOR.config
 */

/**
 * The parameter customizes the display of SCAYT context menu commands ("Add Word", "Ignore",
 * "Ignore All", "Options", "Languages", "Dictionaries" and "About").
 * This must be a string with one or more of the following
 * words separated by a pipe character (`'|'`):
 *
 * * `off` &ndash; disables all options.
 * * `all` &ndash; enables all options.
 * * `ignore` &ndash; enables the "Ignore" option.
 * * `ignoreall` &ndash; enables the "Ignore All" option.
 * * `add` &ndash; enables the "Add Word" option.
 * * `option` &ndash; enables "Options" menu item.
 * * `language` &ndash; enables "Languages" menu item.
 * * `dictionary` &ndash; enables "Dictionaries" menu item.
 * * `about` &ndash; enables "About" menu item.
 *
 * Note, that availability of 'Options', 'Languages' and 'Dictionaries' items
 * depends on scayt_uiTabs option also.
 * Example:
 *
 *		// Show only "Add Word" and "Ignore All" in the context menu.
 *		config.scayt_contextCommands = 'add|ignoreall';
 *
 * @cfg {String} [scayt_contextCommands='ignore|ignoreall|add']
 * @member CKEDITOR.config
 */

/**
 * The parameter sets the default spell checking language for SCAYT. Possible values are:
 * `'en_US'`, `'en_GB'`, `'pt_BR'`, `'da_DK'`,
 * `'nl_NL'`, `'en_CA'`, `'fi_FI'`, `'fr_FR'`,
 * `'fr_CA'`, `'de_DE'`, `'el_GR'`, `'it_IT'`,
 * `'nb_NO'`, `'pt_PT'`, `'es_ES'`, `'sv_SE'`.
 *
 *		// Sets SCAYT to German.
 *		config.scayt_sLang = 'de_DE';
 *
 * @cfg {String} [scayt_sLang='en_US']
 * @member CKEDITOR.config
 */

/**
 * The parameter customizes the SCAYT dialog and SCAYT toolbar menu to show particular tabs/items.
 * This setting must contain a `1` (enabled) or `0`
 * (disabled) value for each of the following entries, in this precise order,
 * separated by a comma (`','`): `'Options'`, `'Languages'`, and `'Dictionary'`.
 *
 *		// Hides the "Languages" tab.
 *		config.scayt_uiTabs = '1,0,1';
 *
 * @cfg {String} [scayt_uiTabs='1,1,1']
 * @member CKEDITOR.config
 */

/**
 * The parameter allows to specify protocol for WSC service (ssrv.cgi) full path.
 *
 *		// Defines protocol for WSC service (ssrv.cgi) full path.
 *		config.scayt_serviceProtocol = 'https';
 *
 * @cfg {String} [scayt_serviceProtocol='http']
 * @member CKEDITOR.config
 */

/**
 * The parameter allows to specify host for WSC service (ssrv.cgi) full path.
 *
 *		// Defines host for WSC service (ssrv.cgi) full path.
 *		config.scayt_serviceHost = 'my-host';
 *
 * @cfg {String} [scayt_serviceHost='svc.webspellchecker.net']
 * @member CKEDITOR.config
 */

/**
 * The parameter allows to specify port for WSC service (ssrv.cgi) full path.
 *
 *		// Defines port for WSC service (ssrv.cgi) full path.
 *		config.scayt_servicePort = '2330';
 *
 * @cfg {String} [scayt_servicePort='80']
 * @member CKEDITOR.config
 */

/**
 * The parameter allows to specify path for WSC service (ssrv.cgi) full path.
 *
 *		// Defines host for WSC service (ssrv.cgi) full path.
 *		config.scayt_servicePath = 'my-path/ssrv.cgi';
 *
 * @cfg {String} [scayt_servicePath='spellcheck31/script/ssrv.cgi']
 * @member CKEDITOR.config
 */

/**
 * The parameter sets the URL to SCAYT core. Required to switch to the licensed version of SCAYT application.
 *
 * Further details available at [http://wiki.webspellchecker.net/doku.php?id=migration:hosredfreetolicensedck](http://wiki.webspellchecker.net/doku.php?id=migration:hosredfreetolicensedck)
 *
 *		config.scayt_srcUrl = "http://my-host/spellcheck/lf/scayt/scayt.js";
 *
 * @cfg {String} [scayt_srcUrl='//svc.webspellchecker.net/spellcheck31/lf/scayt3/ckscayt/ckscayt.js']
 * @member CKEDITOR.config
 */

/**
 * The parameter links SCAYT to custom dictionaries. This is a string containing dictionary IDs
 * separated by commas (`','`). Available only for the licensed version.
 *
 * Further details at [http://wiki.webspellchecker.net/doku.php?id=installationandconfiguration:customdictionaries:licensed](http://wiki.webspellchecker.net/doku.php?id=installationandconfiguration:customdictionaries:licensed)
 *
 *		config.scayt_customDictionaryIds = '3021,3456,3478';
 *
 * @cfg {String} [scayt_customDictionaryIds='']
 * @member CKEDITOR.config
 */

/**
 * The parameter activates a User Dictionary in SCAYT. The user
 * dictionary name must be used. Available only for the licensed version.
 *
 *		config.scayt_userDictionaryName = 'MyDictionary';
 *
 * @cfg {String} [scayt_userDictionaryName='']
 * @member CKEDITOR.config
 */

/**
 * The parameter defines the order SCAYT context menu items by groups.
 * This must be a string with one or more of the following
 * words separated by a pipe character (`'|'`):
 *
 * * `suggest` &ndash; main suggestion word list,
 * * `moresuggest` &ndash; more suggestions word list,
 * * `control` &ndash; SCAYT commands, such as "Ignore" and "Add Word".
 *
 * Example:
 *
 *		config.scayt_contextMenuItemsOrder = 'moresuggest|control|suggest';
 *
 * @cfg {String} [scayt_contextMenuItemsOrder='suggest|moresuggest|control']
 * @member CKEDITOR.config
 */

/**
 * If set to `true` &ndash; overrides checkDirty functionality of CK
 * to fix SCAYT issues with incorrect checkDirty behavior. If set to `false`,
 * provides better performance on big preloaded text.
 *
 *		config.scayt_handleCheckDirty = 'false';
 *
 * @cfg {String} [scayt_handleCheckDirty='true']
 * @member CKEDITOR.config
 */

/**
 * If set to `true` &ndash; overrides undo\redo functionality of CK
 * to fix SCAYT issues with incorrect undo\redo behavior. If set to `false`,
 * provides better performance on undo\redo text.
 *
 *		config.scayt_handleUndoRedo = 'false';
 *
 * @cfg {String} [scayt_handleUndoRedo='true']
 * @member CKEDITOR.config
 */

/**
 * Disabling of SCAYT Options storing during several sessions. Options storing will be turned off after page refresh.
 *
 * * `'options'` - disables all SCAYT Ignore options
 * * `'ignore-all-caps-words'` - disables 'Ignore All-Caps Words' option
 * * `'ignore-domain-names'` - disables 'Ignore Domain Names' option
 * * `'ignore-words-with-mixed-cases'` - disables 'Ignore Words with Mixed Case' option
 * * `'ignore-words-with-numbers'` - disables 'Ignore Words with Numbers' option
 * * `'lang'` - disables SCAYT spell check language storing
 * * `'all'` - disables all SCAYT options storing
 *
 * Example:
 *
 *		// One options disabling.
 *		config.scayt_disableOptionsStorage = 'all';
 *
 *		// Several options disabling.
 *  	config.scayt_disableOptionsStorage = ['lang', 'ignore-domain-names', 'ignore-words-with-numbers'];
 *
 *
 * @cfg {String|Array} [scayt_disableOptionsStorage = '']
 * @member CKEDITOR.config
 */

 /**
 * Specifies the names of tags that will be skipped while spell checking. This is a string containing tag names
 * separated by commas (`','`). Please note that `'style'` tag would be added to specified tags list.
 *
 *		config.scayt_elementsToIgnore = 'del,pre';
 *
 * @cfg {String} [scayt_elementsToIgnore='style']
 * @member CKEDITOR.config
 */

 /**
 * The parameter turns on/off multi language support in SCAYT. If 'true', turns on SCAYT multi language support after loading the editor.
 *
 *		config.scayt_multiLanguageMode = true;
 *
 * @cfg {Boolean} [scayt_multiLanguageMode=false]
 * @member CKEDITOR.config
 */

 /**
 * Defines additional styles for misspellings for specified languages. Styles will be applied only if 'scayt_multiLanguageMode' parameter is set to 'true'
 * and 'language' plugin included and loaded into editor.  All misspellings still will be underlined with red waveline by default.
 *
 * Example:
 *
 *		// Display misspellings in French language with green color and underlined with red waveline
 *		config.scayt_multiLanguageStyles = {
 *			'fr': 'color: green'
 *		};
 *
 *		// Display misspellings in Italian language with green color and underlined with red waveline and German misspellings with red color only
 *		config.scayt_multiLanguageStyles = {
 *			'it': 'color: green',
 *			'de': 'background-image: none; color: red'
 *		};
 *
 * @cfg {Object} [scayt_multiLanguageStyles = {}]
 * @member CKEDITOR.config
 */