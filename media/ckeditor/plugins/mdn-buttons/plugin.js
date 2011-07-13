// See: http://blog.lystor.org.ua/2010/11/ckeditor-plugin-and-toolbar-button-for.html

// the plugin automatically creates button commands for these tags
CKEDITOR.config.mdnButtons_tags = ['code', 'pre', 'dl', 'dt', 'dd'];

(function(){
    // make a generic command object that wraps text in <tag>
    var tagCommand = function(tag) {
        var command = {
            exec: function(editor, data){
                var format = {
                    element: tag
                };
                var style = new CKEDITOR.style(format);
                style.apply(editor.document);
            }
        };
        return command;
    };
    CKEDITOR.plugins.add("mdn-buttons", {
        init: function(editor) {
            var tags = CKEDITOR.config.mdnButtons_tags;
            var pluginName = "mdn-buttons";
            // addCommand and addButton for each tag in the list
            for (var i = 0, j = tags.length; i < j; i++) {
                var tag = tags[i];
                var commandName = pluginName + '-' + tag;
                var command = tagCommand(tag);
                editor.addCommand(commandName, command);
                editor.ui.addButton(tag+'Button', {
                    label: tag,
                    command: commandName,
                    icon: this.path + 'button-' + tag + '.png'
                });
            }
        }
    });
})();
