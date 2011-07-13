// http://blog.lystor.org.ua/2010/11/ckeditor-plugin-and-toolbar-button-for.html
/*
(function(){
    var a= {
        exec:function(editor){
            var format = {
                element : "pre"
            };
            var style = new CKEDITOR.style(format);
            style.apply(editor.document);
        }
    };

    CKEDITOR.plugins.add("mdn-buttons",{
        init:function(editor){
            var pluginName = "mdn-buttons";
            editor.addCommand(pluginName, a);
            editor.ui.addButton(pluginName, {
                label:"Button PRE",
                icon: this.path + "button-pre.png",
                command:b
            });
        }
    });
})();
*/
CKEDITOR.config.mdnButtons_tags = ['code', 'pre', 'dl', 'dt', 'dd'];
(function(){
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
            for (var i = 0, j = tags.length; i < j; i++) {
                var tag = tags[i];
                var commandName = pluginName + '-' + tag;
                var command = tagCommand(tag);
//                alert('tag: ' + tag + ', commandName: ' + commandName);
//                alert(command);
                editor.addCommand(commandName, command);
                editor.ui.addButton(tag+'Button', {
                    label: tag,
                    command: commandName,
                    icon: this.path + 'button-' + tag + '.png'
                });
//                alert('addButton('+tag+'Button)');
            }
/*
            editor.addCommand(pluginName, command);
            editor.ui.addButton('MDNButton', {
                label: 'pre',
                command: pluginName,
                icon: this.path + 'button-pre.png',
            });
*/
        }
    });
})();
