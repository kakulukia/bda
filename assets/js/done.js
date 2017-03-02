
function focus_element(selector){
  $(selector)[0].focus();
}


var app = new Vue({
  el: '#app',
  data: {
    mail_sent: false,
    range: 10,
    open_tab: undefined,

  },
  methods: {
    show: function(whichOne){

      if (whichOne == this.open_tab) return;

      $('.publish').slideUp();
      $('.email').slideUp();
      $('.compare').slideUp();
      $('.discard').slideUp();

      $(whichOne).slideDown();
      this.open_tab = whichOne;
    },
    compare: function(){
      superagent.get('/api/area-bios/' + this.bio.id + '/entries/').end(function (err, res) {
        if (err) console.log(err);
        else {
          var bios = JSON.parse(res.text);
          _.forEach(bios, function (bio) {
            $.get('/graph/' + bio.id + '/', function (data) {
              $('.graph-area').html(data);
            });
          })
        }
      });
    }
  },
  filters: {

  },

  // When this module is ready run this
  created: function () {
    // initialize data

  }

});
