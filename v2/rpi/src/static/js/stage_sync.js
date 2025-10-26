// static/js/stage_sync.js
// Requires the Socket.IO client library to already be loaded on the page.
(function(){
  if(typeof io === "undefined") {
    console.error('Socket.IO client library not loaded!');
    return;
  }
  var socket = io();
  socket.on('stage_update', function(data) {
    var routes = {
      'standby': '/',
      'welcome': '/welcome',
      'collecting': '/collecting',
      'processing': '/processing',
      'results': function(d){ return d && d.sample_id ? '/results/' + d.sample_id : '/results'; },
      'history': function(d){ return '/history/' + d.user_id; },
      'goodbye': '/goodbye'
    };
    var route = routes[data.stage];
    if(typeof route === 'function') {
      window.location.href = route(data);
    } else if(route) {
      window.location.href = route;
    }
  });
})();
