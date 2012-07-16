// See: http://blog.lystor.org.ua/2010/11/ckeditor-plugin-and-toolbar-button-for.html

// the plugin automatically creates button commands for these tags
CKEDITOR.config.mdnButtons_tags = ['pre', 'code', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'];

(function(){
    
    // make a generic command object that wraps text in <tag>
    var tagCommand = function(tag) {
        var command = {
            exec: function(editor, data){

                alert("Exec'ing: " + tag);

                var format = {
                    element: tag
                };
                var style = new CKEDITOR.style(format);
                style.apply(editor.document);
            }
        };
        return command;
    };
    
    CKEDITOR.plugins.add('mdn-buttons', {
        init: function(editor) {

            var tags = CKEDITOR.config.mdnButtons_tags;
            var pluginName = 'mdn-buttons';
            var $saveButton = $('#btn-save');
            var $saveContinueButton = $('#btn-save-and-edit')
            
            // addCommand and addButton for each tag in the list
            for (var i = 0, j = tags.length; i < j; i++) {
                var tag = tags[i];
                var commandName = pluginName + '-' + tag;
                var command = tagCommand(tag);
                editor.addCommand(commandName, command);
                editor.ui.addButton(tag+'Button', {
                    label: tag,
                    command: commandName,
                    className: 'mdn-buttons-button ' + tag,
                });
            }
            
            // Configure "Save and Exit"
            editor.addCommand(pluginName + '-save-exit', {
                exec: function (editor, data) {
                    if(!$saveButton.length) {
                        $saveButton = $('.edited-section-ui.current .btn-save');
                    }
                    
                    editor.updateElement();
                    $saveButton.click();
                }
            });
            editor.ui.addButton('mdnSaveExit', {
                label: gettext('Save and Exit'),
                className: 'cke_button_save_exit',
                command: pluginName + '-save-exit'
            });
            
            // Add "Save and Continue", if that button is present
            if($saveContinueButton.length) {
                editor.addCommand(pluginName + '-save', {
                    exec: function (editor, data) {
                        var saveCallback = $saveContinueButton.data('save_cb') || function () { 
                            $saveContinueButton.click(); 
                        };
                        
                        editor.updateElement();
                        saveCallback();
                    }
                });
                editor.ui.addButton('mdnSave', {
                    label: $saveContinueButton.text(),
                    className: 'cke_button_save',
                    command: pluginName + '-save'
                });
            }

            // Some localized strings are stashed on #page-buttons...
            var pb = $('#page-buttons');

            // Define command and button for "New Page"
            editor.addCommand(pluginName + '-newpage', {
                exec: function (editor, data) {
                    // Treat this as cancellation for inline editor
                    var cancel_btn = $('.edited-section-ui.current .cancel');
                    if (cancel_btn.length) {
                        return cancel_btn.click();
                    }
                    // Otherwise, try treating as a new wiki page
                    var msg = pb.attr('data-new-page-msg'),
                        href = pb.attr('data-new-page-href');
                    if (!msg || !href) { return; }
                    if (window.confirm(msg)) {
                        window.location.href = href;
                    }
                }
            });
            editor.ui.addButton('mdnNewPage', {
                label: pb.attr('data-new-page-label'),
                className: 'cke_button_newpage',
                command: pluginName + '-newpage'
            });

            // Define command and button for "Preview"
            editor.addCommand(pluginName + '-preview', {
                exec: function (editor, data) {
                    editor.updateElement();
                    $('#btn-preview').click();
                }
            });
            editor.ui.addButton('mdnPreview', {
                label: $('#btn-preview').text(),
                className: 'cke_button_preview',
                command: pluginName + '-preview'
            });

        }
    });

})();
