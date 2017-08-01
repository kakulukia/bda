
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
    errorText: "",
    averageUsage: averageUsage
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
      });
      this.noErrors = !entriesNotOk;
      this.calcAreaUsage();
    },
    calcAreaUsage: function () {

      var years = 0;
      var used = 0;

      _.forEach(app.entries, function(entry){
        if (entry.ok) {
          var current_years = Math.abs(entry.year_to - entry.year_from);
          years += current_years;
          used += current_years * entry.living_space / entry.number_of_people;
        }
      });

      app.averageUsage = Math.round(used / years)
    },
    updateBio: function () {
      resetIntroTimer();

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
      resetIntroTimer();

      this.checkEntries();
      if (entry.ok) {
        if (entry.id) {
          superagent.put('/api/area-bios/' + this.bio.id + '/entries/' + entry.id + '/')
              .send(entry)
              .set('Authorization', auth_token)
              .end(function (err, res) {
                if (err) {
                  app.displayError(err);
                  entry.range_error = true
                }
              });
          setTimeout(this.loadGraph, 200);
        } else {
          superagent.post('/api/area-bios/' + this.bio.id + '/entries/')
              .send(entry)
              .set('Authorization', auth_token)
              .end(function (err, res) {
                if (err) {
                  app.displayError(err);
                  entry.range_error = true
                } else {
                  entry.id = JSON.parse(res.text).id;
                }
              });
          setTimeout(this.loadGraph, 200);
        }
      }
      this.addTheFuture();
    },
    addTheFuture: function(){
      var markTheNextOne = false;
      _.forEach(this.entries, function(entry, index){
        if (entry.year_to == new Date().getFullYear()){
          if (!entry.future && index == app.entries.length - 1){
            app.addEntry(true);
          }

        }
      });
    },
    getLastYear: function(){

      if (!app.bio.age) return 0;

      var max_year = new Date().getFullYear() - app.bio.age;
      _.forEach(app.entries, function (entry) {
        if (entry.year_to > max_year) {
          max_year = entry.year_to;
        }
      });
      return max_year;
    },
    setLastYear: function (entry) {
      resetIntroTimer();

      if (!/^[12][90][0-9]{2}-[12][90][0-9]{2}$/.test(entry.range) && app.bio.age){
        var max_year = this.getLastYear();
        entry.year_from = max_year;
        entry.range_error = true;
        this.setRange(entry);
        this.entries.splice();
      }
    },
    testEntry: function (entry) {
      resetIntroTimer();
      this.markTheFuture();

      if (entry.range == undefined && !entry.number_of_people && !entry.living_space && !entry.description){
        entry.ok = true;
        return true;
      }

      entry.living_space_error = !entry.living_space;
      entry.number_of_people_error = !entry.number_of_people || !Number.isInteger(parseInt(entry.number_of_people));
      entry.range_error = !/^[12][90][0-9]{2}-[12][90][0-9]{2}$/.test(entry.range);

      if (entry.number_of_people_error && entry.number_of_people){
        this.displayError("Trage bitte die Anzahl der Personen ein. Füge eine neue Zeile hinzu, wenn sich die Anzahl der Personen ändert.");
      }

      entry.ok = !(entry.range_error || entry.number_of_people_error || entry.living_space_error);
      return entry.ok

    },
    addEntry: function (markTheFuture, placeholder) {
      resetIntroTimer();

      var lastYear = this.getLastYear();
      if (lastYear == new Date().getFullYear()){
        markTheFuture = true;
      }

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
        range_error: false,
        future: markTheFuture === true,
        placeholder: placeholder
      };
      app.setRange(entry);
      this.entries.push(entry);
      var row_name = '.row_' + this.entries.length + ' input';
      setTimeout(focus_element, 200, row_name);
    },
    deleteEntry: function (entry) {
      resetIntroTimer();

      if (entry.id > 0) {
        superagent.delete('/api/area-bios/' + this.bio.id + '/entries/' + entry.id + '/')
            .set('Authorization', auth_token)
            .end(function (err, res) {
              if (err) console.log(err);
            });
      }
      _.pull(this.entries, entry);
      this.checkEntries();
      this.entries.splice(this.entries.length);
      setTimeout(this.loadGraph, 200);
    },
    updateRange: function (entry) {
      resetIntroTimer();

      if (!entry.range){
        entry.range_error = false;
        return
      }

      if (/^[12][90][0-9]{2}-[12][90][0-9]{2}$/.test(entry.range)) {
        var years = _.split(entry.range, '-', 2);
        entry.year_from = parseInt(years[0]);
        entry.year_to = parseInt(years[1]);
        app.updateEntry(entry);
        entry.range_error = false;
      } else {
        entry.range_error = true;
        this.displayError("Der Zeitraum kann maximal zwischen 1900 und 2099 liegen.")
      }

    },
    loadGraph: function () {
      $.get('/view-graph/' + this.bio.uuid + '/', function (data) {
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
      entry.future = false;
      this.setRange(entry);
    },
    markTheFuture: function(){
      var futureMarked = false;
      var gotLastYear = false;
      var lastYear = new Date().getFullYear();

      _.forEach(this.entries, function(entry){
        entry.future = false;

        // if this entry is in the future, mark it
        if(!futureMarked && entry.year_from >= new Date().getFullYear()){
          entry.future = true;
          futureMarked = true;
        }

        // if the next entry will be in the future, remember it
        if(entry.year_to == lastYear){
          gotLastYear = true;
        }

        // if we have an empty row and the last one had the last year, mark it
        if(!futureMarked && gotLastYear && !entry.year_from){
          entry.future = true;
          futureMarked = true;
        }
      })
    },
    nextRow: function(entry){
      resetIntroTimer();

      var retval = _.some($('.one input'), function (entry) {
        if(!$(entry).val()) {
          entry.focus();
          return true
        }
      });

      if (!retval) this.addEntry();
    },
    submitForm: function(){
      resetIntroTimer();

      if (this.noErrors) $('form').submit();
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
      app.loadGraph();

    });
    superagent.get('/api/area-bios/' + this.bio.id + '/entries/').end(function (err, res) {
      // Calling the end function will send the request
      var entries = JSON.parse(res.text);

      _.forEach(entries, function (entry) {
        app.initEntry(entry);
      });

      if (entries.length > 0){
        app.entries = entries;
        app.markTheFuture();
        app.noErrors = true;
      }
      else {
        app.addEntry(null, 'z.B. Elternhaus');
        app.addEntry(null, 'z.B. Studium / WG im Altbau');
        app.addEntry(null, 'z.B. Soziales Jahr / Wohnheim');
        setTimeout(function() { $('#id_name').focus(); }, 500);
      }
    });
  }

});
