(function($, sh) {
  SyntaxHighlighter.brushes.JScript.aliases.push('json');

  $(document).ready(function() {
    $('pre').each(function() {
        var $this = $(this),
            newText = $this.text().replace(/<span class="nowiki">(.*)<\/span>/g, '$1');
        $this.text(newText);
    });
    sh.defaults.toolbar = false;
    sh.defaults['auto-links'] = false;
    sh.all();
  });
})(jQuery, SyntaxHighlighter);