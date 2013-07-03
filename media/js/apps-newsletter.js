/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

var newsletter = {
  init: function(){
    $('#newsletter-sub').hide().addClass('modal');
    $('#newsletter .go').click(function(e){
      e.preventDefault();
      $('#newsletter-sub').modal({
        onOpen: newsletter.open,
        onShow: newsletter.show,
        onClose: newsletter.close
      });
    });
  },
  open: function(dialog){
    dialog.overlay.fadeIn(200, function () {
      dialog.container.fadeIn(200, function () {
        dialog.data.fadeIn(200);
        dialog.container.height('auto');
        $('#id_email').focus();
      });
    });
  },
  show: function(dialog){
    dialog.container.delegate('#newsletter-sub', 'submit', function(e){
      e.preventDefault();
      var $form = $(this);
      $form.children('fieldset').fadeOut(200, function(){
        $('#wait-modal').fadeIn(200, function(){
          $.ajax({
            url: $form.attr('action'),
            data: $form.serialize(),
            type: 'post',
            cache: false,
            success: function(data){
              $form.replaceWith(data);
            },
            error: function(xhr){
              $('#wait-modal').hide();
              $('#error-modal').show();
            }
          });
        });
      });
    });
  },
  close: function(dialog){
    dialog.data.fadeOut(200, function(){
      dialog.container.fadeOut(200, function(){
        dialog.overlay.fadeOut(200, function(){
          $.modal.close();
        })
      })
    })
  },
  error: function(xhr){
    alert(xhr.statusText);
  }
};

$(function(){
  $('.modules .boxed').each(function(){
    var maxHeight = 0;
    $(this).each(function(){
      $(this).height('auto');
      if (maxHeight < $(this).height()) { maxHeight = $(this).height(); }
    });
    $('.modules .boxed').each(function(){
      $(this).height(maxHeight);
    });
  });
  newsletter.init();
});
