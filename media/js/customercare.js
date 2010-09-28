$(document).ready(function() {
    $('.reply-message').NobleCount('.character-counter');

    $('.reply-message').autoPlaceholderText();

    $('#accordion').accordion({
        'icons': false,
        'autoHeight': false,
        'collpsible': true,
        'active': false,
    });

    $('.tweet').click(function() {
        var twitter_modal = $('#twitter-modal');
        if (twitter_modal.attr('data-authed') == 'False') {
          twitter_modal.dialog({
              'modal': 'true',
              'position': 'top',
          });
          twitter_modal.find('.cancel').click(function(e) {
              twitter_modal.dialog('close');
              e.preventDefault();
              return false;
          });
          return;
        }

        var reply_to = $(this).attr('data-reply_to')
        var avatar_href = $(this).find('.avatar').attr('href');
        var avatar_img = $(this).find('.avatar img').attr('src');
        var twittername = $(this).find('.twittername').text();
        var text = $(this).find('.text').text();

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
        var tweet = $('.reply-message').val();
        var reply_to = $('#reply_to').val();
        $.post(
            action, 
            { 'tweet': tweet, 'reply_to': reply_to },
            function() {
                $('#submit-message').show();
                setTimeout(function () { 
                    $('#reply-modal').dialog('close');  
                    $('#submit-message').hide(); 
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
