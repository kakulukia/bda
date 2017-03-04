
function focus_element(selector){
  $(selector)[0].focus();
}


var app = new Vue({
  el: '#app',
  data: {
    mail_sent: false,
    range: 10,
    open_tab: undefined

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
      $('.charts').html('');
      superagent.get('/api/area-bios/' + graph_id + '/compare/')
        .query({ range: this.range })
        .end(function (err, res) {
          if (err) console.log(err);
          else {
            var bios = JSON.parse(res.text);
            $('.right').html("<div class='charts'></div>");
            _.forEach(bios, function (bio) {
              $.get('/graph/' + bio.id + '/bare/', function (data) {
                $('.charts').append(data);
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
