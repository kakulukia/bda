
var app = new Vue({
  el: '.app',
  data: {
    minAge: 0,
    maxAge: 100,
    country: "",
    currentGraph: ''
  },
  methods: {
    viewGraph: function (uuid, title) {
      this.currentGraph = title;
      $.get('view-graph/' + uuid + '/', function (data) {
        $('#graphView .graph-area').html(data);
        $('#graphView').modal('show');
      });

    },
    updateGraphs: function () {
      superagent.get('/api/area-bios/')
          .query({
            minAge: app.minAge,
            maxAge: app.maxAge,
            country: app.country
          })
          .end(function (err, res) {
            if (err) console.log(err);
            else {
              var bios = JSON.parse(res.text);
              $('.list-area').html('');
              _.forEach(bios, function (bio) {
                $.get('/graph/' + bio.id + '/bare-name/', function (data) {
                  $('.list-area').append(data);
                });
              })
            }
          });
    },
    openIntro: function() {
      if (!localStorage.introTimer || (parseInt(localStorage.introTimer) < new Date().getTime())){
        this.resetIntroTimer();
        $('#intro').modal('show');
      }
    },
    resetIntroTimer: function(){
      localStorage.introTimer = new Date().getTime() + 60 * 5 * 1000;
    }
  },
  filters: {

  },

  // When this module is ready run this
  created: function () {
  }
});

var element = document.getElementById('age-slider');
var ageSlider = new Slider(element, {
  isDate: false,
  min: 0,
  max: 100,
  start: 0,
  end: 100,
  overlap: true
});
ageSlider.subscribe('moving', function(data) {
  app.minAge = Math.round(data.left);
  app.maxAge = Math.round(data.right);
});
ageSlider.subscribe('stop', function(data) {
  app.updateGraphs();
});

app.openIntro();
