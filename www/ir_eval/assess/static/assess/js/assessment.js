function is_handheld(){
  //return (navigator.userAgent.indexOf("iPad") != -1);
  return /Android|iPhone|iPad|IEMobile|Mobile/i.test(navigator.userAgent);
}

function is_phone(){
  //return (navigator.userAgent.indexOf("iPhone") != -1);
  return $(window).width() <= 768;
}

$(document).ready(function(){
  // set up the header, iframe and footer
  $('div#container').removeClass( "container" ).addClass( "container-fluid" );
  //$('div#container').height($(window).height());
  $('div#raw_html_viewer').height($(window).height()-55);
  $('body').css('padding-bottom', '0px');
  $('div#footer').remove();
  
  $('div#float-info-wrapper').click(function(){
    $(this).clearQueue().slideUp('fast');
  });
  
  // set up the label form
  $('form#label').submit(function(event){
    event.preventDefault();
    
    // first, perform form validation
    if('undefined' === typeof $("input[name='relevance']:checked").val()){
      $('p#submit-info').hide();
      $('p#submit-success').hide();
      msg = 'Relevance must be selected! (Click to dismiss)';
      $('p#submit-error').text(msg).show();
      $('div#float-info-wrapper').slideDown('fast', function(){
        $(this).delay(5000).slideUp('fast');
      });
    }else{
      // we are ready to submit
      $('p#submit-success').hide();
      $('p#submit-error').hide();
      $('p#submit-info').text('Submitting ...');
      
      $('div#float-info-wrapper').slideDown('fast', function(){
        // animation complete
        //$('div#float-info-wrapper').delay(1000).slideUp('fast');
      
        url_path = $('form#label').attr('action');
        $.post(url_path, $('form#label').serialize())
        .done(function(response){
          $('p#submit-info').hide();
          $('p#submit-error').hide();
          msg = response.info + ' Will return.';
          $('p#submit-success').text(msg).show();
          // return to the query page
          setTimeout(function(){
            window.location.href = response.redirect;
          }, 1000);
        })
        .fail(function(response) {
          $('p#submit-info').hide();
          $('p#submit-success').hide();
          msg = 'Oops. An error has occurred: ' 
            + response.responseJSON.error_msg + ' (Click to dismiss)';
          //msg = 'Oops. An error has occurred. (Click to dismiss)';
          $('p#submit-error').text(msg).show();
          $('div#float-info-wrapper').delay(5000).slideUp('fast');
        })
        .always(function() {
          // do something always
        });
      });
    }
  });
  
  $('button#label-submit').prop('disabled', 'disabled');

  $('input#option-rel-yes').click(function(){
    $('button#label-submit').prop('disabled', false);
  });
  
  $('input#option-rel-no').click(function(){
    $('button#label-submit').prop('disabled', false);
  });
  
  $('a#view_itunes').click(function(event){
    event.preventDefault();
    url = $(this).attr('url');
    console.log('Redirect to ' + url);
    $('#doc_view').attr('src', url);
    $('li.active').removeClass();
    $(this).parent().addClass('active');
  });
  
  $('a#view_raw_doc').click(function(event){
    event.preventDefault();
    url = $(this).attr('url');
    console.log('Redirect to ' + url);
    $('#doc_view').attr('src', url);
    $('li.active').removeClass();
    $(this).parent().addClass('active');
  });
});
