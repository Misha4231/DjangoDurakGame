const cardsVisualDir = "/static/images/playcards/"; // directory where card images are laying
var playerContainers = {}; // player id => html element id
var playZone = document.getElementById('play-zone'); // rectangle in the center where players put cards
var gameState = {}; // current state of game (global variable was to made to provide access for functions like throwCardOnPlayZone)
var actionButton = document.getElementById('action-button');

var floatingCard = null; // floating card is global because it should be available both in drag-drop action and connect() function
var rootFloatingCard = null; // card that was taken to make floating one

// if player dragged card and made some mistake / error occurred, then this function will roll back visual part
function rollBackDraggingCard() {
    if (floatingCard) {
        floatingCard.remove(); // remove from html dragging card
        floatingCard = null;
    }

    if (rootFloatingCard) rootFloatingCard.style.display = 'block'; // make card in player's hand visible
}

// helper function to create image for card and remove code repetition
function createCardElement(cardName) {
    let image = document.createElement("img");
    image.classList.add('play-card');
    image.alt = `card ${cardName}`;
    image.src = `${cardsVisualDir}${cardName}.png`; // image names in cardsVisualDir directory are the same as in enums in engine
    image.setAttribute('data-name', cardName);

    return image;
}

// helper function for drag-drop to determine if mouse is on top of the html element
function isMouseOver(mouseX, mouseY, element) {
    if (!element) return false; // null/undefined validation

    let boundaries = element.getBoundingClientRect(); // get boundaries
    return (mouseX >= boundaries.left && mouseX <= boundaries.right && mouseY >= boundaries.top && mouseY <= boundaries.bottom);
}

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

    // drag cards to play zone
    document.querySelector('#player-me-wrapper').querySelectorAll('.play-card').forEach((card) => {
        card.onmousedown = (e) => {
            e.preventDefault();

            rootFloatingCard = card;
            rootFloatingCard.style.display = 'none'; // hide card in player's hand while dragging

            floatingCard = createCardElement(rootFloatingCard.getAttribute('data-name')) // create new card representation for drag-drop
            floatingCard.style.position = 'absolute'
            // starting positioning to user mouse
            floatingCard.style.left = e.clientX - 40 + 'px';
            floatingCard.style.top = e.clientY - 60 + 'px';

            // append to body to make it independent of other tags
            document.body.appendChild(floatingCard);

            const isDefender = (gameState.player_id === gameState.state.players[gameState.state.next_turn].id);
            document.onmousemove = (e) => {
                // move along with user mouse and centering card
                floatingCard.style.left = e.clientX - 40 + 'px';
                floatingCard.style.top = e.clientY - 60 + 'px';

                if (isDefender) { // if the current user is defender, then he can put card on laying card
                    let attackSlotElements = document.querySelectorAll('.attack-slot');

                    attackSlotElements.forEach(slot => { // check if user hovers one of attack slots
                        if (isMouseOver(e.clientX, e.clientY, slot)) {
                            attackSlotElements.forEach(s => s.classList.remove('highlighted')) // remove highlight from every slot

                            slot.classList.add('highlighted') // add to hovered slot
                        }
                    })
                } else {
                    // if mouse is on top of the play zone
                    let isOver = isMouseOver(e.clientX, e.clientY, playZone);
                    if (isOver !== playZone.classList.contains("highlighted")) {
                        playZone.classList.toggle("highlighted", isOver); // toggle class for styles
                    }
                }
            }

            document.onmouseup = (e) => {
                // reset events
                document.onmouseup = null;
                document.onmousemove = null;

                if (isDefender) {
                    let attackSlotElements = document.querySelectorAll('.attack-slot');
                    let isOverAny = false; // is mouse overlaps one of slots

                    attackSlotElements.forEach(slot => { // check if user hovers one of attack slots
                        if (isMouseOver(e.clientX, e.clientY, slot)) {
                            slot.classList.remove('highlighted') // remove to hovered slot
                            isOverAny = true

                            // call defend action
                            defendCard(slot.querySelector('.play-card').getAttribute('data-name'), floatingCard.getAttribute('data-name'));
                        }
                    })

                    if (!isOverAny) rollBackDraggingCard(); // to slot chosen
                } else {
                    // cancel everything if mouse is not on top of the play zone
                    let onPlayZone = isMouseOver(e.clientX, e.clientY, playZone);
                    if (onPlayZone) {
                        throwCardOnPlayZone(floatingCard.getAttribute('data-name')); // put dragging card on table
                    } else {
                        rollBackDraggingCard();
                    }

                    playZone.classList.remove('highlighted'); // make sure play zone is not highlighted anymore
                }
            }
        }
    });

    document.getElementById('leave-game-button').addEventListener('click', () => {
        window.location.href = '/';
    })
}

// should be called when player puts card on play zone i.e. wants to play turn, defend or add additional card
function throwCardOnPlayZone(cardName) { // returns false is putting should be canceled
    const isAttacker = (gameState.player_id === gameState.state.players[gameState.state.turn].id);
    if (isAttacker && gameState.state.attack_state.length === 0) { // if first move has to be made
        // play turn
        gameSocket.send(JSON.stringify({ // send to backend
            'action': 'play_turn',
            'card': cardName
        }));
    } else {
        // throw additional card
        gameSocket.send(JSON.stringify({
            'action': 'throw_additional',
            'card': cardName
        }));
    }
}
// defending action
function defendCard(bottomCard, topCard) {
    const isDefender = (gameState.player_id === gameState.state.players[gameState.state.next_turn].id);

    if (isDefender) { // validation
        let hasUnbeatenCards = false; // is there anything to beat
        for (let attackSlot in gameState.state.attack_state) { // iterate over all attacking cards
            if (attackSlot[1] == null) { // if unbeaten card is laying
                hasUnbeatenCards = true;
                break;
            }
        }

        if (!hasUnbeatenCards) { // if there is nothing to defend
            popUp('No any way to put card as a defender', false); //send pop up (see scripts/popup_messages.js)
            rollBackDraggingCard();
        } else {
            // defence

            gameSocket.send(JSON.stringify({
                'action': 'defend',
                'bottom_card': bottomCard,
                'top_card': topCard
            }));
        }
    }
}

// draw deck coming from the game state
function drawDeck(deck) {
    let deckContainer = document.getElementById("deck-images"); // get container where all images are going to be dropped at
    deckContainer.innerHTML = '';

    if (deck.length !== 0) {
        // display trump card (the only one that is accessible)
        let trumpCard = createCardElement(deck.trump);
        trumpCard.style.position = 'absolute';
        trumpCard.style.transform = `translateX(-80px) rotate(90deg)`;
        deckContainer.appendChild(trumpCard);
    } else { // if deck is empty, remove it from screen
        document.getElementById('deck').innerHTML = '';
    }

    // draw all cards (despite trump)
    for (let i = 0; i < deck.length - 1; i++) {
        let backCard = createCardElement('BACK');  // back side of the card because players shouldn't know what cards are laying next in deck
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
        let cardImage = createCardElement(player.hand === undefined ? 'BACK' : player.hand[i]); // player.hand is sent only for current user
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

// update who is attacker and defender
function drawTurn(players, turn, next_turn) {
    if (players.length <= turn || players.length <= next_turn) return;

    const attackerId = players[turn].id; // get attacker id
    const defenderId = players[next_turn].id; // get defender id

    for (let [playerId, containerId] of Object.entries(playerContainers)) {
        let role = ''; // user role or empty string
        if (playerId === attackerId) {
            role = '(attacker)'
        }
        else if (playerId === defenderId) {
            role = '(defender)'
        }
        // change current role of the player
        document.getElementById(containerId).querySelector('.current-role').textContent = role;
    }
}

// draw contents of the play zone (attack state)
function drawPlayZoneContent(attackState) {
    playZone.innerHTML = '' // clear previous cards before draw new ones

    attackState.forEach(slot => { // iterate over all slots in attack state
        let slotElement = document.createElement('div');
        slotElement.classList.add('attack-slot');

        const bottomCardName = slot[0];
        const topCardName = slot[1];

        // create images for bottom and top cards
        let bottomImage = createCardElement(bottomCardName);
        slotElement.appendChild(bottomImage);
        if (topCardName !== "None") {
            let topImage = createCardElement(topCardName);
            slotElement.appendChild(topImage);
        }

        playZone.appendChild(slotElement);
    });
}

// draw button to take cards or show that player is finished with throwing additional cards
function drawActionButton() {
    if (gameState.state.players.length <= gameState.state.next_turn) return;
    const isDefender = (gameState.player_id === gameState.state.players[gameState.state.next_turn].id);

    let isWinner = false;
    gameState.state.winners.forEach(w => {
        if (w.id === gameState.player_id) isWinner = true;
    })

    if (gameState.state.attack_state.length === 0  /* if attack didn't start */ ||
        (isDefender && gameState.state.defender_takes) /* if player made choice to take as a defender */ ||
        (gameState.state.finished_player_ids.includes(gameState.player_id)) /* if player made choice to finish */ ||
        (isWinner))
    {
        actionButton.style.display = 'none';
        return;
    }

    if (isDefender) {
        actionButton.textContent = 'Take' // defender can take all cards if not able (or don't want) defend cards
        actionButton.style.display = 'block' // default is none
    } else {
        actionButton.textContent = 'Finished'
        actionButton.style.display = 'block' // default is none
    }

    actionButton.onclick = () => { // send info to backend
        if (isDefender) {
            gameSocket.send(JSON.stringify({
                'action': 'take_cards'
            }))
        } else {
            gameSocket.send(JSON.stringify({
                'action': 'finished'
            }))
        }
    };
}

// visualize winners and durak
function drawResults() {
    gameState.state.winners.forEach(winner => { // mark winners
        winnerContainerId = playerContainers[winner.id];
        let winnerContainerElement = document.getElementById(winnerContainerId).querySelector('.current-role');

        winnerContainerElement.innerHTML = '<h1><u>Winner</u></h1>';
    })

    if (gameState.state.players.length === 1) { // if 1 is left, then is it durak (loser)
        durakContainerId = playerContainers[gameState.state.players[0].id];
        let durakContainerElement = document.getElementById(durakContainerId).querySelector('.current-role');

        durakContainerElement.innerHTML = '<h1><u>Durak</u></h1>';
    }
}

// when the game is over or player became winner, he has the ability to leave game
function drawLeaveButton() {
    let leaveButton = document.getElementById('leave-game-button');

    let isWinner = false;
    gameState.state.winners.forEach(w => {
        if (w.id === gameState.player_id) isWinner = true;
    })

    if (gameState.state.players.length <= 1 || isWinner) {
        leaveButton.style.display = 'block';
    }
}

var gameSocket = null;
function connect() {
    gameSocket = new WebSocket("ws://" + window.location.host + "/ws/durak_game/"); // connect to game web socket

    gameSocket.onmessage = (e) => {
        gameState = JSON.parse(e.data);
        console.log(gameState)

        if (gameState.type === "game_state") {
            // remove dragging card on screen of user who put it on table
            if (gameState?.last_action?.type === 'play_turn' && gameState.player_id === gameState.state.players[gameState.state.turn].id) rollBackDraggingCard();
            if (gameState?.last_action?.type === 'throw_additional' && gameState.player_id === gameState?.last_action?.player_id) rollBackDraggingCard();
            if (gameState?.last_action?.type === 'defend' && gameState.player_id === gameState?.last_action?.player_id) rollBackDraggingCard();
            if (gameState?.last_action?.type === 'player_removed') { // remove player's hand
                document.getElementById(playerContainers[gameState.last_action.player_id]).innerHTML = '';
            }

            drawDeck(gameState.state.deck); // draw deck

            gameState.state.players.forEach(p => { // draw each player's hand
                drawHand(p);
            })
            drawTurn(gameState.state.players, gameState.state.turn, gameState.state.next_turn); // add marks to attacker and defender names
            drawPlayZoneContent(gameState.state.attack_state) // draw play zone
            drawActionButton();
            drawResults();
            drawLeaveButton();

            loadPage(); // update bindings after loading state
        }
        else if (gameState.type === "player_mistake") {
            rollBackDraggingCard();
            popUp(gameState.message, false);
        }
    }

    gameSocket.onerror = (ev) => {
        console.log("WebSocket encountered an error: " + ev.message);
    }
}

connect();