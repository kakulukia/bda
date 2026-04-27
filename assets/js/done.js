
function focus_element(selector){
  $(selector)[0].focus();
}


var app = new Vue({
  el: '#app',
  data: {
    range: 10,
    open_tab: undefined

  },
  computed: {
    openCompare: function () {
      return this.tabClass('.compare')
    }
  },
  methods: {
    tabClass: function(name){
      return {
        'active': this.open_tab == name
      }
    },
    show: function(whichOne){
      resetIntroTimer();

      if (whichOne == this.open_tab) return;

      $('.compare').slideUp();
      $('.discard').slideUp();

      $(whichOne).slideDown();
      this.open_tab = whichOne;
    },
    compare: function(){
      resetIntroTimer();

      $('.right').html("<div class='charts'></div>");
      $('.charts').html('');
      $.get('/graph/' + graph_id + '/bare/original/', function (data) {
        $('.charts').append(data);
      });
      superagent.get('/api/area-bios/' + graph_id + '/compare/')
        .query({ range: this.range })
        .end(function (err, res) {
          if (err) console.log(err);
          else {
            var bios = JSON.parse(res.text);
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

  }

});
