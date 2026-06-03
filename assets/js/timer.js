function getModal(id) {
  return document.getElementById(id);
}

function isModalShown(element) {
  return Boolean(element && element.classList.contains('show'));
}

function showModal(element) {
  if (!element) {
    return;
  }

  element.style.display = 'block';
  element.classList.add('show');
  document.body.classList.add('modal-open');
}

function hideModal(element) {
  if (!element) {
    return;
  }

  element.classList.remove('show');
  element.style.display = 'none';

  if (!document.querySelector('.modal.show')) {
    document.body.classList.remove('modal-open');
  }
}

function openIntro() {
  if (!localStorage.introTimer || (parseInt(localStorage.introTimer, 10) < new Date().getTime())) {
    if (window.location.pathname !== '/') {
      window.location = '/';
      return;
    }

    resetIntroTimer();
    hideModal(getModal('newBio'));
    hideModal(getModal('graphView'));
    hideModal(getModal('errorDialog'));

    var intro = getModal('intro');
    if (!isModalShown(intro)) {
      showModal(intro);
    }
  }
}

function resetIntroTimer() {
  localStorage.introTimer = new Date().getTime() + 60 * 5 * 1000;
}

function runTimer() {
  setTimeout(runTimer, 5000);
  openIntro();
}

resetIntroTimer();
runTimer();
