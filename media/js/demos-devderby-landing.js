(function() {

  var targetRegex = /.*?#(.*)/g,
      tabRegex = /.*?#tab-*/;

  window.derbyTabs = function(targetblock) {
    var currentblock;
    $('#current-challenge .block').addClass('block-hidden');

    if(targetblock) {
      currentblock = targetblock.replace(targetRegex, '$1'); // determine which block to show by extracting the id from the href
      tabSwitch(currentblock);
    }
    else if(!targetblock && (tabRegex.test(window.location))) { // if no target is supplied, check the url for a fragment id prefixed with 'tab-' (this means inbound links can point directly to a tab)
      currentblock = window.location.href.replace(targetRegex, '$1');
      $('html,body').animate({scrollTop: $('#current-challenge').offset().top - 150}, 0); // HACK: compensate for overshooting the tabs when the page loads
      tabSwitch(currentblock);
    }
    else {
      var href = $('#current-challenge .tabs li.current a').attr('href');
      if(href) {
        currentblock = href.replace(targetRegex, '$1');
        tabSwitch(currentblock);
      }
    }
    $('#'+currentblock).removeClass('block-hidden'); // make the current block visible
  };

  window.tabSwitch = function(targettab) {
    var tabs = $('#current-challenge .tabs li a');    
    if (targettab) {
      for (var i = 0; i < tabs.length; i++) { // loop through the tabs
        var tab = $(tabs[i]).attr('href').replace(targetRegex, '$1'); // strip down the href
        if ( targettab == tab ) { // if one of them matches our target
          $('#current-challenge .tabs li').removeClass('current'); // first clean the slate
          $('#current-challenge .tabs li a[href$=#'+targettab+']').parents('li').addClass('current'); // then set that tab as current
        }    
      }
    } 
  };

  $('#current-challenge .tabs li a').click(function(){
    $('#current-challenge .tabs li').removeClass('current');
    $(this).parents('li').addClass('current');
    derbyTabs($(this).attr('href').replace(targetRegex, '$1')); // transmit target
    return false;
  });
  
  $('#nav-derby a[rel=tab]').click(function(){
    derbyTabs($(this).attr('href').replace(targetRegex, '$1')); // transmit target
  });

  $(document).ready(function(){
    if ($('body').hasClass('derby-closed')) {
        // On hiatus - no tabs to manage.
        return;
    }
    derbyTabs();

    $('#upcoming li').hover(
      function(){
        $(this).children('.desc').fadeIn('fast');
      },
      function(){
        $(this).children('.desc').fadeOut('fast');
      }
    );
  });

})();
