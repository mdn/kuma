function clear_reply_dialog() {
    $('.reply-message').val('').trigger('blur');
    $('#submit-message').hide(); 
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
    $twitter_modal.find('.cancel').click(function(e) {
        $twitter_modal.dialog('close');
        e.preventDefault();
        return false;
    });
    $('.tweet').click(function() {
        var $tweet = $(this);
        if ($twitter_modal.attr('data-authed') == 'False') {
            $twitter_modal.dialog({
                'modal': 'true',
                'position': 'top',
                'width': 500,
            });
            return;
        }

        var reply_to = $tweet.attr('data-reply_to')
        var avatar_href = $tweet.find('.avatar').attr('href');
        var avatar_img = $tweet.find('.avatar img').attr('src');
        var twittername = $tweet.find('.twittername').text();
        var text = $tweet.find('.text').text();

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
});
