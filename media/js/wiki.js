(function($) {

    $('.htab').each(function(index) {
        var $htab = $(this),
            $items = $htab.find('>ul>li');

        $htab.append($('div[id=compat-desktop]')[index]);
        $htab.append($('div[id=compat-mobile]')[index]);

        $items.find('a').click(function() {
            var $this = $(this)
            $items.removeClass('selected');
            $this.parent().addClass('selected');
            $htab.find('>div').hide().eq($items.index($this.parent())).show();
        }).eq(0).click();
    });

})(jQuery);