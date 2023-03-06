$(document).ready(function() {
  $("#generate-joke-btn").click(function() {
    // Make API call to retrieve random joke
    var url = "https://icanhazdadjoke.com/";
    $.ajax({
      url: url,
      headers: {
        "Accept": "application/json"
      },
      success: function(result) {
        // Display joke
        var joke = "";
        joke += result.joke;
        $("#joke-container").html("<div class='notification is-info'>" + joke + "</div>");
      }
    });
  });
});
