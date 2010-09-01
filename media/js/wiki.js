(function () {
    var fields = {
        title: {
            id: '#id_slug',
            dependency_ids: ['#id_title'],
            dependency_list: ['#id_title'],
            maxLength: 50
        }
    }, field = null;
    
    for (i in fields) {
        field = fields[i];
        $('#id_slug').addClass('prepopulated_field');
        $(field.id).data('dependency_list', field['dependency_list'])
               .prepopulate($(field['dependency_ids'].join(',')),
                            field.maxLength);
    };
}());
