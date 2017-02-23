
function focus_element(selector){
  $(selector)[0].focus();
}


var app = new Vue({
  el: '#app',
  data: {
    bio: {
      name: '',
      age: 0,
      country: '',
      id: bio_id
    },
    entries: []
  },
  methods: {
    updateBio: function () {
      superagent.put('/api/area-bios/'+ this.bio.id +'/')
          .send(this.bio)
          .set('Authorization', auth_token)
          .end(function(err, res){
      });

    },
    updateEntry: function (entry) {
      if (entry.id){
        console.log('we have id');
        superagent.put('/api/area-bios/'+ this.bio.id +'/entries/'+ entry.id +'/')
            .send(entry)
            .set('Authorization', auth_token)
            .end(function(err, res){
              if (err) {
                console.log(err);
              } else {
                console.log(res.text);
              }
            });
        console.log('changed entry');
      } else {
        if (entry.living_space && entry. number_of_people && entry.year_from && entry.year_to){
          superagent.post('/api/area-bios/'+ this.bio.id +'/entries/')
              .send(entry)
              .set('Authorization', auth_token)
              .end(function(err, res){
                if (err){
                  console.log(err);
                } else {
                  console.log(res.text);
                  entry.id = JSON.parse(res.text).id;
                }
              });
          console.log('changed added');
        }
      }
      setTimeout(this.loadGraph, 200);
    },
    getLastYear: function(){
      var max_year = 0;
      _.forEach(app.entries, function(entry){
        if (entry.year_to > max_year){
          max_year = entry.year_to;
        }
      });
      return max_year
    },
    addEntry: function(){
      var entry = {
        description: '',
        id: 0,
        living_space: null,
        number_of_people: null,
        year_from: null,
        year_to: null,
        area_bio: bio_id,
        range_error: false
      };
      entry.year_from = app.getLastYear() + 1;
      app.setRange(entry);
      this.entries.push(entry);
      var row_name = '.row_' + this.entries.length + ' input';
      setTimeout(focus_element, 200, row_name);
    },
    deleteEntry: function(entry){
      if (entry.id > 0){
        superagent.delete('/api/area-bios/'+ this.bio.id +'/entries/'+ entry.id +'/')
            .set('Authorization', auth_token)
            .end(function(err, res){
              console.log(res.text);
              console.log(err);
            });
        console.log('changed deleted');
      }
      _.pull(this.entries, entry);
      this.entries.splice(this.entries.length);
    },
    updateRange: function(entry){

      if(/^[12][90][0-9]{2}-[12][90][0-9]{2}$/.test(entry.range)){
        var years = _.split(entry.range, '-', 2);
        entry.year_from = parseInt(years[0]);
        entry.year_to = parseInt(years[1]);
        app.updateEntry(entry);
        entry.range_error = false;
      } else {
        entry.range_error = true;
      }

    },
    loadGraph: function(){
      $.get('/graph/' + this.bio.id + '/', function(data){
        $('.graph-area').html(data);
        console.log('geladen!');
      });
      console.log('angestoßen');
    },
    setRange: function(entry) {
      if (entry.year_from){
        entry.range = entry.year_from + '-';
      }
      if (entry.year_to){
        entry.range += entry.year_to
      }
    }
  },
  filters: {
    caps: function (value) {
      if (!value) return '';
      return value.toString().toUpperCase();
    }
  },

  // When this module is ready run this
  created: function() {
    // initialize data
    superagent.get('/api/area-bios/'+ this.bio.id +'/').end(function(err, res){
      // Calling the end function will send the request
      app.bio = JSON.parse(res.text);
    });
    superagent.get('/api/area-bios/'+ this.bio.id +'/entries/').end(function(err, res){
      // Calling the end function will send the request
      var entries = JSON.parse(res.text);

      _.forEach(entries, function(entry){
        app.setRange(entry);
      });

      app.entries = entries;
    });
    setTimeout(this.loadGraph, 500);
  }

});

