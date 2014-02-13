$(function() {

  // If there is a highlighted row, let's expand it
  if (window.location.hash) {
    $(window.location.hash).find(".hideme").toggle();
  }

  // Toggle summary if you click on a row
  $('tr').click(function() {
    $(this).find(".hideme").toggle();
  });
});
