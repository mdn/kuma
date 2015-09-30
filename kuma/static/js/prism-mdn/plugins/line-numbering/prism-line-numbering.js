/*
	This plugins was created based on the Prism line-numbering plugin.
	This plugin aims to number all lines and is independent of highlighting.
*/
(function(){

    var doc = document;

    if(!window.Prism || !doc.querySelectorAll) {
        return;
    }

    function $$(expr, con) {
        return Array.prototype.slice.call((con || doc).querySelectorAll(expr));
    }

    function numberLines(pre) {
        var offset = +pre.getAttribute('data-line-offset') || 0;
        var lineHeight = parseFloat(getComputedStyle(pre).lineHeight);
        var code = pre.querySelector('code');
        var numLines = code.innerHTML.split('\n').length;
        pre.setAttribute('data-number', '');

        for (var i=1; i <= numLines; i++) {
            var line = doc.createElement('div');
            line.className = 'line-number';
            line.setAttribute('data-start', i);
            line.style.top = ((i - offset - 1) * lineHeight) + 'px';
            (code || pre).appendChild(line);
        }
    }

    Prism.hooks.add('after-highlight', function(env) {
        var pre = env.element.parentNode;

        if (!pre || !/pre/i.test(pre.nodeName) || pre.getAttribute('data-prism-prevent-line-number')) {
            return;
        }

        $$('.line-number', pre).forEach(function (line) {
            line.parentNode.removeChild(line);
        });

        numberLines(pre);
    });

})();
