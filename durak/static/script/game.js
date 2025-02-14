const cardsVisualDir = "/static/images/playcards/";
var playerContainers = {};
var playZone = null;

// when DOM is loaded
document.addEventListener('DOMContentLoaded', loadPage);

// setup events and make helper variables
function loadPage() {
    // set up playerContainers to later work with state of game and visualization
    document.querySelectorAll(".player-wrapper").forEach((container) => {
        const playerId = container.getAttribute("data-id"); // get player id
        playerContainers[playerId] = container.id;
    })

    // When one of cards player own is clicked, mark it
    document.querySelector('#player-me-wrapper').addEventListener('mouseover', (e) => {
        if (e.target.classList.contains('play-card')) { // ensure a card was clicked
            // remove previous selections
            document.querySelectorAll('#player-me-wrapper .play-card').forEach(card =>
                card.classList.remove("selected-card")
            );

            // add the selected class
            e.target.classList.add("selected-card");
        }
    });

    playZone = document.getElementById('play-zone');
    // drag cards to play zone
    document.querySelector('#player-me-wrapper').querySelectorAll('.play-card').forEach((card) => {
        card.onmousedown = (e) => {
            e.preventDefault();

            card.style.display = 'none'; // hide card in player's hand while dragging

            var floatingCard = document.createElement("img"); // create new card representation for drag-drop
            floatingCard.className = "play-card";
            floatingCard.src = card.src; // set the same image
            floatingCard.style.position = 'absolute';
            // starting positioning to user mouse
            floatingCard.style.left = e.clientX - 40 + 'px';
            floatingCard.style.top = e.clientY - 60 + 'px';

            // append to body to make it independent of other tags
            document.body.appendChild(floatingCard);

            document.onmousemove = (e) => {
                // move along with user mouse and centering card
                floatingCard.style.left = e.clientX - 40 + 'px';
                floatingCard.style.top = e.clientY - 60 + 'px';

                // if mouse is on top of the play zone
                let isOver = isMouseOver(e.clientX, e.clientY, playZone);
                if (isOver !== playZone.classList.contains("highlighted")) {
                    playZone.classList.toggle("highlighted", isOver); // toggle class for styles
                }
            }

            document.onmouseup = (e) => {
                // reset events
                document.onmouseup = null;
                document.onmousemove = null;

                // cancel everything if mouse is not on top of the play zone
                let onPlayZone = isMouseOver(e.clientX, e.clientY, playZone);
                if (onPlayZone) {
                    // play turn
                } else {
                    floatingCard.remove();
                    card.style.display = 'block';
                }
            }
        }

    })

    // helper function for drag-drop to determine if mouse is on top of the html element
    function isMouseOver(mouseX, mouseY, element) {
        if (!element) return false;

        let boundaries = element.getBoundingClientRect(); // get boundaries
        return (mouseX >= boundaries.left && mouseX <= boundaries.right && mouseY >= boundaries.top && mouseY <= boundaries.bottom);
    }
}


function drawDeck(deck) { // draw deck coming from the game state
    let deckContainer = document.getElementById("deck"); // get container where all images are going to be dropped at

    // display trump card (the only one that is accessible)
    let trumpCard = document.createElement("img");
    trumpCard.className = "play-card";
    trumpCard.src = `${cardsVisualDir}${deck.trump}.png`; // image names in cardsVisualDir directory are the same as in enums in engine
    trumpCard.style.position = 'absolute';
    trumpCard.style.transform = `translateX(-80px) rotate(90deg)`;
    deckContainer.appendChild(trumpCard);

    // draw all cards (despite trump)
    for (let i = 0; i < deck.length - 1; i++) {
        let backCard = document.createElement("img");
        backCard.className = "play-card";
        backCard.src = `${cardsVisualDir}BACK.png`; // back side of the card because players shouldn't know what cards are laying next in deck
        backCard.style.position = 'absolute';

        const translation = i * 5; // add growing translation, so players see how many cards are left
        backCard.style.transform = `translateX(${translation}px)`;

        deckContainer.appendChild(backCard);
    }
}

// draw player hand visualization
function drawHand(player) {
    let playerWrapper = document.getElementById(playerContainers[player.id]); // get container where cards should be
    let playerHand = playerWrapper.querySelector('.player-hand'); // get hand
    playerHand.innerHTML = ''; // clear previous cards

    const pxPerCardRatio = 70; // how many pixels next card will be moved from the previous (to avoid overlapping of absolute elements)
    var translation = -(player.hand_len / 2) * pxPerCardRatio; // (for centering purposes) start with -middle
    for (let i = 0; i < player.hand_len; i++) {
        let cardImage = document.createElement('img');

        cardImage.src = `${cardsVisualDir}${player.hand === undefined ? 'BACK' : player.hand[i]}.png`; // player.hand is sent only for current user
        cardImage.className = "play-card";
        cardImage.style.position = 'absolute';

        // transform depends on player position on screen
        if (playerWrapper.id.includes('player-0')) { // Top
            cardImage.style.transform = `translateX(${translation}px) rotate(180deg)`;
        } else if (playerWrapper.id.includes('player-1')) { // Left
            cardImage.style.transform = `translateY(${translation}px) rotate(90deg)`;
        } else if (playerWrapper.id.includes('player-2')) { // Right
            cardImage.style.transform = `translateY(${translation}px) rotate(-90deg)`;
        } else { // Bottom (me)
            cardImage.style.transform = `translateX(${translation}px)`;
        }

        translation += pxPerCardRatio; // move next card

        playerHand.appendChild(cardImage); // add card to hand
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

            data.state.players.forEach(p => { // draw each player's hand
                drawHand(p);
            })

            loadPage(); // update bindings after loading state
        }
    }

    gameSocket.onerror = (ev) => {
        console.log("WebSocket encountered an error: " + ev.message);
    }
}

connect();