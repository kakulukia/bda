

var app = new Vue({
  el: '#app',
  data: {
    name: 'Andy',
    age: '36',
    country: 'Germany'
  },
  methods: {
    updateBio: function () {
      alert('hallo');
    }
  }

});

superagent.get('http://localhost:8000/api/area-bio/1/').end(function(err, res){
  // Calling the end function will send the request
  console.log(JSON.parse(res.text));
});
