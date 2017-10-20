// See also: http://stackoverflow.com/questions/6086651/minimize-the-list-filter-in-django-admin
(function($){
    'use strict';

    var ListFilterCollapsePrototype = {
        bindToggle: function(){
            var that = this;
            this.$filterTitle.click(function(){
                that.$filterContent.slideToggle();
                that.$list.toggleClass('filtered');
            });
        },
        init: function(filterEl) {
            this.$filterTitle = $(filterEl).children('h2');
            this.$filterContent = $(filterEl).children('h3, ul');
            $(this.$filterTitle).css('cursor', 'pointer');
            this.$list = $('#changelist');
            this.bindToggle();
        }
    };
    function ListFilterCollapse(filterEl) {
        this.init(filterEl);
    }
    ListFilterCollapse.prototype = ListFilterCollapsePrototype;

    $(document).ready(function(){
        $('#changelist-filter').each(function(){
            new ListFilterCollapse(this);
        });
    });
})(window.django.jQuery);
