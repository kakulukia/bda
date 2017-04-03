
var app = new Vue({
  el: '.app',
  data: {
    minAge: 0,
    maxAge: 100,
    country: "",
    currentGraph: '',
    showLegend: false,
    median_usage: 0
  },
  methods: {
    createNewBio: function(){
      resetIntroTimer();

      $('#newBio').modal('show');
    },
    viewGraph: function (uuid, title, median) {
      resetIntroTimer();

      this.currentGraph = title;
      this.median_usage = median;
      $.get('view-graph/' + uuid + '/', function (data) {
        $('#graphView .graph-area').html(data);
        var smallEntries = $('#graphView .description .text.small-entry');
        var legend = $('#legend .entries');

        // reset the legend text
        legend.html('');

        // set the current entries
        _.forEach(smallEntries, function(value) {
          var elem = $(value);
          elem.removeClass();
          elem.appendTo(legend);
        });

        app.showLegend = smallEntries.length > 0;
        $('#graphView').modal('show');
      });

    },
    updateGraphs: function () {
      resetIntroTimer();
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
