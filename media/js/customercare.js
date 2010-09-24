var has_twitter_access = false;
// cookie names are duplicated in apps/customercare/views.py
if ($.cookie('custcare_twitter_access_id'))
  has_twitter_access = true;


$(document).ready(function() {
  $('.reply-message').NobleCount('.character-counter');

  $('.reply-message').autoPlaceholderText();

  $('#accordion').accordion({
    'icons': false,
    'autoHeight': false,
  });

  $('.tweet').click(function() {
    if (!has_twitter_access) {
      $('#twitter-modal').dialog({
        'modal': 'true',
        'position': 'top',
      });
      $('#twitter-modal .cancel').click(function(e) {
        $('#twitter-modal').dialog('close');
        e.preventDefault();
        return false;
      });
      return;
    }

    var avatar_href = $(this).find('.avatar').attr('href');
    var avatar_img = $(this).find('.avatar img').attr('src');
    var twittername = $(this).find('.twittername').text();
    var text = $(this).find('.text').text();

    var modal = $('#reply-modal');
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
});
