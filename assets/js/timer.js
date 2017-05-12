function openIntro() {
  // console.log((parseInt(localStorage.introTimer) - new Date().getTime()) / 1000);
  if (!localStorage.introTimer || (parseInt(localStorage.introTimer) < new Date().getTime())){
    if (window.location.pathname != '/') {
      window.location = '/';
    }
    else {
      this.resetIntroTimer();
      if (($("#newBio").data('bs.modal') || {})._isShown) {
        $('#newBio').modal('hide');
      }
      if (($("#graphView").data('bs.modal') || {})._isShown) {
        $('#graphView').modal('hide');
      }
      if (($("errorDialog").data('bs.modal') || {})._isShown) {
        $('#errorDialog').modal('hide');
      }
      if (!($("#intro").data('bs.modal') || {})._isShown) {
        $('#intro').modal('show');
      }
    }
  }
}
function resetIntroTimer() {
  // console.log('resetting timer ..');
  localStorage.introTimer = new Date().getTime() + 60 * 5 * 1000;
  // localStorage.introTimer = new Date().getTime() + 10 * 1000;
}
function runTimer(){
  setTimeout(runTimer, 5000);
  openIntro();
}
resetIntroTimer();
// runTimer();
