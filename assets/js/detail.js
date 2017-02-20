

var app = new Vue({
  el: '#app',
  data: {
    user: {
      name: '',
      age: 0,
      country: ''
    }
  },
  methods: {
    updateBio: function () {

      superagent.put('/api/area-bios/1/').send(app.user).end(function(err, res){
        console.log(res.text);
      });
      console.log('changed');

    }
  }

});

//  init user data
superagent.get('/api/area-bios/1/').end(function(err, res){
  // Calling the end function will send the request
  app.user = JSON.parse(res.text);
});
