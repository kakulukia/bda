

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
          .send(app.bio)
          .set('Authorization', auth_token)
          .end(function(err, res){
      });

    },
    updateEntry: function (entry) {
      superagent.put('/api/area-bios/'+ this.bio.id +'/entries/'+ entry.id +'/')
          .send(entry)
          .set('Authorization', auth_token)
          .end(function(err, res){
            console.log(res.text);
          });
      console.log('changed entry');

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
      app.entries = JSON.parse(res.text);
    });
  }

});

