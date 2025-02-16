// helper js file to add pop up messages at the corner of the screen

var container = document.getElementById('popup-messages-wrapper'); // get container

// add popUp
function popUp(message, isSuccess) {
    // create box
    let htmlMessageBox = document.createElement('div');
    htmlMessageBox.classList.add('popup-message');
    htmlMessageBox.classList.add(isSuccess ? 'success-message' : 'failure-message');

    // create text inside box
    let htmlMessageText = document.createElement('h3');
    htmlMessageText.textContent = message;
    htmlMessageBox.appendChild(htmlMessageText);

    // add pop up to the container
    container.appendChild(htmlMessageBox);

    var timeToDisappear = 5; // seconds
    var animationParts = 100; // how many times opacity will be changed in interval
    var opacity = 1; // current opacity

    // smoothly disappear message
    setInterval(() => {
        opacity -= (1 / animationParts);
        htmlMessageBox.style.opacity = opacity;
    }, (timeToDisappear * 1000 /*convert to milliseconds*/) / animationParts);

    // after timeToDisappear seconds remove message from html
    setTimeout(() => {
        htmlMessageBox.remove();
    }, timeToDisappear * 1000 /*convert to milliseconds*/);
}