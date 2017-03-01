
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
      superagent.put('/api/area-bios/' + this.bio.id + '/')
          .send(this.bio)
          .set('Authorization', auth_token)
          .end(function (err, res) {
          });

    },
    updateEntry: function (entry) {

      this.testEntry(entry);
      console.log(entry);
      console.log(entry.ok);
      if (entry.ok) {
        console.log('inside');
        if (entry.id) {
          console.log('we have id');
          superagent.put('/api/area-bios/' + this.bio.id + '/entries/' + entry.id + '/')
              .send(entry)
              .set('Authorization', auth_token)
              .end(function (err, res) {
                if (err) {
                  console.log(err);
                } else {
                  console.log(res.text);
                }
              });
          setTimeout(this.loadGraph, 200);
        } else {
          superagent.post('/api/area-bios/' + this.bio.id + '/entries/')
              .send(entry)
              .set('Authorization', auth_token)
              .end(function (err, res) {
                if (err) {
                  console.log(err);
                } else {
                  console.log(res.text);
                  entry.id = JSON.parse(res.text).id;
                }
              });
          setTimeout(this.loadGraph, 200);
        }
      }

    },
    getLastYear: function (entry) {
      var max_year = 0;
      _.forEach(app.entries, function (entry) {
        if (entry.year_to > max_year) {
          max_year = entry.year_to;
        }
      });
      entry.year_from = max_year;
      this.setRange(entry);
    },
    testEntry: function (entry) {

      entry.living_space_error = !entry.living_space;
      entry.number_of_people_error = !entry.number_of_people;
      entry.range_error = !/^[12][90][0-9]{2}-[12][90][0-9]{2}$/.test(entry.range);

      entry.ok = !(entry.range_error && entry.number_of_people_error && entry.living_space_error);

    },
    addEntry: function () {
      var entry = {
        description: '',
        id: 0,
        living_space: null,
        number_of_people: null,
        year_from: null,
        year_to: null,
        area_bio: bio_id,
        living_space_error: false,
        number_of_people_error: false,
        range_error: false
      };
      app.setRange(entry);
      this.entries.push(entry);
      var row_name = '.row_' + this.entries.length + ' input';
      setTimeout(focus_element, 200, row_name);
    },
    deleteEntry: function (entry) {
      if (entry.id > 0) {
        superagent.delete('/api/area-bios/' + this.bio.id + '/entries/' + entry.id + '/')
            .set('Authorization', auth_token)
            .end(function (err, res) {
              console.log(res.text);
              if (err) console.log(err);
            });
      }
      _.pull(this.entries, entry);
      this.entries.splice(this.entries.length);
      setTimeout(this.loadGraph, 200);
    },
    updateRange: function (entry) {

      if (/^[12][90][0-9]{2}-[12][90][0-9]{2}$/.test(entry.range)) {
        var years = _.split(entry.range, '-', 2);
        entry.year_from = parseInt(years[0]);
        entry.year_to = parseInt(years[1]);
        app.updateEntry(entry);
        entry.range_error = false;
      } else {
        entry.range_error = true;
      }

    },
    loadGraph: function () {
      $.get('/graph/' + this.bio.id + '/', function (data) {
        $('.graph-area').html(data);
      });
    },
    setRange: function (entry) {
      if (entry.year_from) {
        entry.range = entry.year_from + '-';
      }
      if (entry.year_to) {
        entry.range += entry.year_to
      }
    },
    initEntry: function (entry) {
      entry.living_space_error = false;
      entry.number_of_people_error = false;
      entry.range_error = false;
      this.setRange(entry);
    }
  },
  filters: {
    caps: function (value) {
      if (!value) return '';
      return value.toString().toUpperCase();
    },
    extractName: function (bio) {
      var name = bio.name;
      if (bio.name && bio.age) {
        name += ', ' + bio.age;
      }
      if (bio.age && bio.country) {
        name += ', ' + bio.country;
      }
      return name
    }
  },

  // When this module is ready run this
  created: function () {
    // initialize data
    superagent.get('/api/area-bios/' + this.bio.id + '/').end(function (err, res) {
      // Calling the end function will send the request
      app.bio = JSON.parse(res.text);
    });
    superagent.get('/api/area-bios/' + this.bio.id + '/entries/').end(function (err, res) {
      // Calling the end function will send the request
      var entries = JSON.parse(res.text);

      _.forEach(entries, function (entry) {
        app.initEntry(entry);
      });

      app.entries = entries;
    });
    setTimeout(this.loadGraph, 500);
  }

});
