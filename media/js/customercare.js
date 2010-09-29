function clear_reply_dialog() {
    $('.reply-message').val('').trigger('blur');
    $('#submit-message').hide(); 
}

memory = {
    _id: null,
    _name: 'custcare_persist_reply',

    get id() { 
        if (!this._id) {
            if (Modernizr.localstorage)
                this._id = localStorage[this._name];
            else
                this._id = $.cookie(this._name);
        }

        return parseInt(this._id);
    },
    set id(val) {
        this._id = val;
    
        if (Modernizr.localstorage)
            localStorage[this._name] = this._id;
        else
            $.cookie(this._name, this._id);
    },
    del: function () {
        if (Modernizr.localstorage)
            localStorage.removeItem(this._name);
        else
            $.cookie(this._name, null);
    }
}

$(document).ready(function() {

    $('.reply-message').NobleCount('.character-counter');

    $('.reply-message').autoPlaceholderText();

    $('#accordion').accordion({
        'icons': false,
        'autoHeight': false,
        'collpsible': true,
        'active': false,
    });

    var $twitter_modal = $('#twitter-modal');
    var authed = ($twitter_modal.attr('data-authed') == 'True');

    $twitter_modal.find('.cancel').click(function(e) {
        $twitter_modal.dialog('close');
        e.preventDefault();
        return false;
    });

    $('.tweet').live('click', function() {
        var $tweet = $(this);
        var reply_to = $tweet.attr('data-reply_to')
        var avatar_href = $tweet.find('.avatar').attr('href');
        var avatar_img = $tweet.find('.avatar img').attr('src');
        var twittername = $tweet.find('.twittername').text();
        var text = $tweet.find('.text').text();

        if (!authed) {
            $twitter_modal.dialog({
                'modal': 'true',
                'position': 'top',
                'width': 500,
            });
            $twitter_modal.find('.signin').click(function() {
                memory.id = reply_to;
            });
            
            return;
        }

        var modal = $('#reply-modal');
        modal.find('#reply_to').val(reply_to);
        modal.find('.avatar').attr('href', avatar_href);
        modal.find('.avatar img').attr('src', avatar_img);
        modal.find('.twittername').text(twittername);
        modal.find('.text').text(text);
        modal.dialog({
            'modal': true, 
            'position': 'top',
            'width': 500,
            'close': clear_reply_dialog
        });
    });

    if (authed && memory.id) {
        $('#tweet-'+ memory.id).trigger('click');
        memory.del();
    }

    $('.reply-topic').click(function(e) {
        snippet = $(this).next('.snippet').text();
        $('.reply-message').val(snippet);
        $('.reply-message').trigger('keydown');

        e.preventDefault();
        return false;
    });

    $('#reply-modal #submit').click(function(e) {
        var action = $('#reply-modal form').attr('action');
        var reply_to = $('#reply_to').val();
        var reply_to_name = $('#reply-modal .twittername').text();
        var tweet = $('.reply-message').val();
        $.post(
            action, 
            { 
                'tweet': tweet, 
                'reply_to': reply_to, 
                'reply_to_name': reply_to_name,
            },
            function() {
                $('#submit-message').show();
                setTimeout(function () { 
                    $('#reply-modal').dialog('close');  
                }, 2000);
            }
        );
        e.preventDefault();
        return false;
    });

    $(".ui-widget-overlay").live("click", function() {  
        $("#reply-modal").dialog("close"); 
        $("#twitter-modal").dialog("close"); 
    });

    $('#refresh-tweets').click(function(e) {
        $.get(
            $(this).attr('href'), {},
            function(data) {
                $('#tweets').html(data);
            }); 
        e.preventDefault();
        return false;
    });
});
