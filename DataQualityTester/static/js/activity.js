var Activity = {
  init:function(){
    this.bindEvents();

    // pretty print xml
    var $p = $('.prettyprint');
    $p.text(vkbeautify.xml($p.text()));
  },
  bindEvents:function(){
    $('body').on('click', '.progress-bar',this.toggleTestOverview);
  },
  toggleTestOverview:function(e){
    e.preventDefault();
    var id_ = $(this).attr('id').substring(4) + '-info';
    $('.summary').slideUp();
    $('#' + id_).slideToggle();
  }

};
$(function(){
  Activity.init();
});
