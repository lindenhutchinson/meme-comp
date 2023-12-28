var socket = null; // Declare the socket variable outside the function
function connectWebSocket(wsScheme, compName) {
    socket = new WebSocket(`${wsScheme}://${window.location.host}/competitions/${compName}/`);

    socket.onopen = function (event) {
        console.log("Websocket connection opened.");
    };

    // Handle received messages
    socket.onmessage = function (event) {
        var message = JSON.parse(event.data);
        console.log(message);

        var command = message.command;
        $(document).trigger(command, message.data);

        switch(command) {
            case 'competition_results':
                doCompetitionResults(message.data);
                break;
            case 'update_emoji':
                createEmoji(message.data);
                break;
            case 'update_shame':
                showSnackbar(message.data, 'danger');
                break;
            case 'update_button':
                showSnackbar(message.data + ' let the crabs out', 'danger');
                unleashTheCrabs();
                break;	
            case 'meme_voted':
                $("#num_votes").text(message.data);
                break;
            case 'timer_start':
                doTimerStarted();
                break;
        }
    };

    socket.onclose = function (event) {
        console.log("Websocket connection closed")
        switch(event.code) {
            case 3000:
                showSnackError('You have been disconnected. Refresh the page to reconnect.')
                break;
            case 1000:
            // normal socket close
                break;
            case 1001:
            // tab was closed
                break;
            default:
                showSnackError('You have been disconnected ¯\\_(ツ)_/¯ Try refreshing the page to reconnect.')
        }
    };

    socket.onerror = function (error) {
        console.log("Websocket error")
        showSnackError("Something bad happened. Try refreshing the page.")
    };
}

function doTimerStarted() {
    $('#comp-timer').css('display','')
    $('#comp-info-card').css('display', 'none')
    startTimer()
}


function doCompetitionResults(results) {
    // switch out the timer for the info card
    $('#comp-timer').css('display','none')
    $('#comp-info-card').css('display', '')
    // disable the ready up button
    $('#readyup-btn').prop('disabled', true);		
    $("#comp-started").css('display', 'none');
    $("#comp-waiting").css('display', 'none');
    $("#comp-tiebreaker").css('display', 'none');
    $("#comp-finished").css('display', '');

    $("#next-meme-btn").css('display', 'none');
    showSnackbar('Competition has finished', 'info')

    if (results) {
        html = `
            <div class="row item-header">
                <h5 class="card-title">${results.participant}</h5>
                <h6 class="card-subtitle">Score: ${results.score}</h6>
            </div>
            <div class="row meme-item-body">
                <div class="winning-container">
                    <img src="/competition/{{ competition.name }}/memes/${results.id}"
                            alt="Meme Image"
                            class="card-img-top">
                </div>
            </div>
        `;

        $('#winning-meme').html(html);
        for (const [key, value] of Object.entries(results.statistics)) {
            $(`#${key}`).text(value);
        }
    }
}