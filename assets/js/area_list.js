
var app = new Vue({
  el: '.app',
  data: {
    minAge: 0,
    maxAge: 100
  },
  methods: {
    viewGraph: function (uuid) {
      $.get('view-graph/' + uuid + '/', function (data) {
        $('#graphView .graph-area').html(data);
      });
      $('#graphView').modal('show');
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
  superagent.get('/api/area-bios/')
      .query({ minAge: app.minAge, maxAge: app.maxAge })
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
});
