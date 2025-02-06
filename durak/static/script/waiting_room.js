var roomSocket = null;

function connect() {
    roomSocket = new WebSocket('ws://' + window.location.host + "/ws/waiting_room/"); // connect to web socket

    roomSocket.onmessage = (e) => {
        const data = JSON.parse(e.data); // parse received data to object
        //console.log(data);

        switch (data.type) {
            case 'start_game': // room is full
                roomSocket.close(1000); // close with 1000 (everything as expected)
                window.location.href = data.redirect_url; // redirect to the giver url
                break;
            case 'players_count': // new player joined room
                document.querySelector('#connected_players_count').textContent = data.connected_users_count; // update count
                break;
            default:
                console.log("Not available option");
                break;
        }
    }

    roomSocket.onerror = (err) => {
        console.log("WebSocket encountered an error: " + err.message);
        roomSocket.close(4000); // close with 4000 to delete player from database
    }
    roomSocket.onclose = (ev) => { // room has more players than possible
        console.log(ev)
        if (ev.code === 3003) {
            window.location.href = "/"; // redirect to index
        }
    }
    document.querySelector('.cancel-button').addEventListener('click', (e) => {
        if (roomSocket) {
            roomSocket.close(4000); // close with 4000 to delete player from database
        }
        window.location.href = "/"; // redirect to index
    });
}

connect();