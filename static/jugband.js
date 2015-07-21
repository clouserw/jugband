(function($) {

  var $body, $overlay;

  $(function() {
    $body = $('body');

    $overlay = $('<div/>', {
      'class': 'overlay'
    }).insertBefore($body.find('header nav'));

    $body.on('click', '.hamburger, .overlay', function(evt) {
      evt.preventDefault();
      $body.toggleClass('show-nav');
    });
  });

})(jQuery);