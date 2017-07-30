
function focus_element(selector){
  $(selector)[0].focus();
}


var app = new Vue({
  el: '#app',
  data: {
    mail_sent: false,
    range: 10,
    open_tab: '.email',
    bio: {
      published: false
    },
    email: '',
    sending: false

  },
  computed: {
    openPublish: function () {
      return this.tabClass('.publish')
    },
    openCompare: function () {
      return this.tabClass('.compare')
    },
    openEmail: function () {
      return this.tabClass('.email')
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

      $('.publish').slideUp();
      $('.email').slideUp();
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
    },
    publish: function () {
      resetIntroTimer();

      superagent.post('/graph/' + graph_id + '/publish/').end(function (err, res) {
        if (err) console.log(err);
        else {
          app.bio.published = true;
        }
      });
    },
    sendGraph: function () {
      resetIntroTimer();

      this.sending = true;
      superagent.post('/graph/' + graph_id + '/send/').type('form')
        .send({email: app.email}).end(function (err, res) {
          if (err) console.log(err);
          else {
            app.mail_sent = true;
            app.sending = false;
            app.show('.publish');
          }
      });
    }
  },
  filters: {

  },

  // When this module is ready run this
  created: function () {
    // initialize data
    superagent.get('/api/area-bios/' + graph_id + '/').end(function (err, res) {
      // Calling the end function will send the request
      app.bio = JSON.parse(res.text);
    });
  }

});
