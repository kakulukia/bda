
function focus_element(selector){
  $(selector)[0].focus();
}


var app = new Vue({
  el: '#app',
  data: {
    bio: {
      name: '',
      age: null,
      country: '',
      id: bio_id,
      uuid: null
    },
    entries: [],
    bioFilled: false,
    noErrors: false,
    name_error: false,
    age_error: false,
    country_error: false,
    errorText: ""
  },
  methods: {
    displayError: function(err){
      try {
        var error = JSON.parse(err.response.text);

        if (error.non_field_errors) {
          this.errorText = error.non_field_errors[0];
        }
      }
      catch(error){

        if (typeof err == "string"){
          this.errorText = err;
        }
        else {
          this.errorText = _.truncate(err.response.text, {
            'length': 177,
            'separator': /Request Method.*/
          });
        }
      }
      $('#errorDialog').modal('show');
    },
    hasErrors: function () {
      return !this.bioFilled || !this.noErrors
    },
    checkBio: function() {
      this.name_error = !this.bio.name;
      this.age_error = !this.bio.age;
      this.country_error = !this.bio.country;
      this.bioFilled = !(this.name_error || this.age_error || this.country_error);
    },
    checkEntries: function () {
      var entriesNotOk = _.some(this.entries, function(entry){
        return !app.testEntry(entry);
      })
      this.noErrors = !entriesNotOk;
    },
    updateBio: function (justCheck) {

      this.checkBio();

      if (this.bioFilled){
        superagent.put('/api/area-bios/' + this.bio.id + '/')
            .send(this.bio)
            .set('Authorization', auth_token)
            .end(function (err, res) {
              if (err) app.displayError(err);
              else {
                _.forEach(app.entries, function(entry){
                  if (entry.living_space) app.updateEntry(entry);
                });
              }
          });
      }
    },
    updateEntry: function (entry) {

      this.checkEntries();
      if (entry.ok) {
        if (entry.id) {
          superagent.put('/api/area-bios/' + this.bio.id + '/entries/' + entry.id + '/')
              .send(entry)
              .set('Authorization', auth_token)
              .end(function (err, res) {
                if (err) app.displayError(err);
              });
          setTimeout(this.loadGraph, 200);
        } else {
          superagent.post('/api/area-bios/' + this.bio.id + '/entries/')
              .send(entry)
              .set('Authorization', auth_token)
              .end(function (err, res) {
                if (err) {
                  app.displayError(err);
                } else {
                  entry.id = JSON.parse(res.text).id;
                }
              });
          setTimeout(this.loadGraph, 200);
        }
      }

    },
    getLastYear: function (entry) {

      if (!/^[12][90][0-9]{2}-[12][90][0-9]{2}$/.test(entry.range) && app.bio.age){
        var max_year = new Date().getFullYear() - app.bio.age;
        _.forEach(app.entries, function (entry) {
          if (entry.year_to > max_year) {
            max_year = entry.year_to;
          }
        });
        entry.year_from = max_year;
        entry.range_error = true;
        this.setRange(entry);
        this.entries.splice();
      }
    },
    testEntry: function (entry) {

      if (entry.range == undefined && !entry.number_of_people && !entry.living_space && !entry.description){
        entry.ok = true;
        return true;
      }

      entry.living_space_error = !entry.living_space;
      entry.number_of_people_error = !entry.number_of_people;
      entry.range_error = !/^[12][980][0-9]{2}-[12][980][0-9]{2}$/.test(entry.range);

      entry.ok = !(entry.range_error || entry.number_of_people_error || entry.living_space_error);
      return entry.ok

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
              // console.log(res.text);
              if (err) console.log(err);
            });
      }
      _.pull(this.entries, entry);
      this.checkEntries();
      this.entries.splice(this.entries.length);
      setTimeout(this.loadGraph, 200);
    },
    updateRange: function (entry) {

      if (/^[12][980][0-9]{2}-[12][980][0-9]{2}$/.test(entry.range)) {
        var years = _.split(entry.range, '-', 2);
        entry.year_from = parseInt(years[0]);
        entry.year_to = parseInt(years[1]);
        app.updateEntry(entry);
        entry.range_error = false;
      } else {
        entry.range_error = true;
        this.displayError("Der Zeitraum kann maximal von 1800 bis heute eingegeben werden.")
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
    },
    nextRow: function(entry){
      var retval = _.some($('.one input'), function (entry) {
        if(!$(entry).val()) {
          entry.focus();
          return true
        }
      });

      if (!retval) this.addEntry();
    },
    submitForm: function(){
      if (this.noErrors) $('form').submit();
    },
    getPlaceholder: function (index) {
      if (index == 0) return "z.B. Elternhaus";
      return ""
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
      app.checkBio();

    });
    superagent.get('/api/area-bios/' + this.bio.id + '/entries/').end(function (err, res) {
      // Calling the end function will send the request
      var entries = JSON.parse(res.text);

      _.forEach(entries, function (entry) {
        app.initEntry(entry);
      });

      if (entries.length > 0){
        app.entries = entries;
        app.noErrors = true;
      }
      else {
        app.addEntry();
        app.addEntry();
        app.addEntry();
        setTimeout(function() { $('#id_name').focus(); }, 500);
      }
    });
    setTimeout(this.loadGraph, 200);
  }

});
