var gameSocket = null;

function connect() {
    gameSocket = new WebSocket("ws://" + window.location.host + "/ws/durak_game/"); // connect to game web socket

    gameSocket.onmessage = (e) => {
        const data = JSON.parse(e.data)
        console.log(data)

        if (data.type === "game_state") {

        }
    }

    gameSocket.onerror = (ev) => {
        console.log("WebSocket encountered an error: " + ev.message);
    }
}

connect();