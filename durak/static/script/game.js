const cardsVisualDir = "/static/images/playcards/";

function drawDeck(deck) { // draw deck coming from the game state
    let deckContainer = document.getElementById("deck"); // get container where all images are going to be dropped at

    // display trump card (the only one that is accessible)
    let trumpCard = document.createElement("img");
    trumpCard.className = "play-card";
    trumpCard.src = `${cardsVisualDir}${deck.trump}.png`; // image names in cardsVisualDir directory are the same as in enums in engine
    trumpCard.style.position = 'absolute';
    trumpCard.style.transform = `translateX(-100px) rotate(90deg)`;
    deckContainer.appendChild(trumpCard);

    // draw all cards (despite trump)
    for (let i = 0; i < deck.length - 1; i++) {
        let backCard = document.createElement("img");
        backCard.className = "play-card";
        backCard.src = `${cardsVisualDir}BACK.png`; // back side of the card because players shouldn't know what cards are laying next in deck
        backCard.style.position = 'absolute';

        const translation = i * 7; // add growing translation, so players see how many cards are left
        backCard.style.transform = `translateX(${translation}px)`;

        deckContainer.appendChild(backCard);
    }

}

var gameSocket = null;

function connect() {
    gameSocket = new WebSocket("ws://" + window.location.host + "/ws/durak_game/"); // connect to game web socket

    gameSocket.onmessage = (e) => {
        const data = JSON.parse(e.data)
        console.log(data)

        if (data.type === "game_state") {
            drawDeck(data.state.deck); // draw deck
        }
    }

    gameSocket.onerror = (ev) => {
        console.log("WebSocket encountered an error: " + ev.message);
    }
}

connect();