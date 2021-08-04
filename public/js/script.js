$(function () {
    $('#gen-form').submit(function (e) {
      e.preventDefault();
      $.ajax({
        type: "POST",
        url: "https://smb-email-aid-5kntub6c2a-uc.a.run.app/",
        dataType: "json",
        data: JSON.stringify(getInputValues()),
        beforeSend: function (data) {
          $('#generate-text').addClass("is-loading");
          $('#generate-text').prop("disabled", true);
        },
        success: function (data) {
          $('#generate-text').removeClass("is-loading");
          $('#generate-text').prop("disabled", false);
          $('#tutorial').remove();
          var gentext = data.text;
          if ($("#prefix").length & $("#prefix").val() != '') {
            var pattern = new RegExp('^' + $("#prefix").val(), 'g');
            var gentext = gentext.replace(pattern, '<strong style=\"color:#A50B5E\">' + $("#prefix").val() + '</strong>');
          }

          var gentext = gentext.replace(/\n\n/g, "<div><br></div>").replace(/\n/g, "<div></div>");
          $("#model-output").append("<li style=\"color:white;\">"+gentext+"</li></br>").hide().fadeIn("slow");;
        },
        error: function (jqXHR, textStatus, errorThrown) {
          $('#generate-text').removeClass("is-loading");
          $('#generate-text').prop("disabled", false);
          $('#tutorial').remove();
          var html = '<div class="gen-box warning"></div>';
          $("#model-output").append("<li style=\"color:#EA350D;\">Error generating phrases - please try again</li></br>").hide().fadeIn("slow");;
        }
      });
    });
    $('#clear-text').click(function (e) {
      $('#model-output').text('')
    });
  });

function getInputValues() {
    var inputs = {};
    $("textarea, input").each(function () {
      inputs[$(this).attr('id')] = $(this).val();
    });
    return inputs;
}
