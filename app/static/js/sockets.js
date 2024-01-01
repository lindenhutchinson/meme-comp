var socket = null; // Declare the socket variable outside the function
function connectWebSocket(wsScheme, compName) {
    socket = new WebSocket(`${wsScheme}://${window.location.host}/competitions/${compName}/`);

    socket.onopen = function (event) {
        console.log("Websocket connection opened.");
        showSnackbar('Connected', 'success');
    };

    // Handle received messages
    socket.onmessage = function (event) {
        const message = JSON.parse(event.data);
        const command = message.command;
        console.log(message);
        $(document).trigger(command, message.data);

        switch (command) {
            case 'update_shame':
                showSnackbar(message.data, 'danger');
                break;
            case 'update_button':
                showSnackbar(message.data + ' let the crabs out', 'danger');
                unleashTheCrabs();
                break;
        }
    };

    socket.onclose = function (event) {
        console.log("Websocket connection closed")
        switch (event.code) {
            case 3000:
                showSnackbar('You have been disconnected. Refresh the page to reconnect.', 'danger', false)
                break;
            case 1000:
                // normal socket close
                break;
            case 1001:
                // tab was closed
                break;
            default:
                showSnackbar('You have been disconnected ¯\\_(ツ)_/¯ Try refreshing the page to reconnect.', 'danger', false)
        }
    };

    socket.onerror = function (error) {
        console.log("Websocket error")
        showSnackbar("Something bad happened. Try refreshing the page.", 'danger', false)
    };
}