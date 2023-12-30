// const commandFunctions = {
//     'participantJoined':participantJoined
// }

$(document).on('participantJoined', (e, data) => {
    const participantLi = data.participant_html
    $('#participants').prepend(participantLi);

    const numParticipants = data.num_participants;
    const participantName = data.participant_name;

    $('#num-participants').text(`(${numParticipants})`);

    if (Math.random() < 0.05) {
        showSnackbar(`Oh look, ${participantName} is here!`, 'success')
    } else if (Math.random() < 0.05) {
        showSnackbar(`Look who showed up, it's ${participantName}`, 'success')
    } else if (Math.random() < 0.05) {
        showSnackbar(`A wizard is never late, ${participantName} arrives precisely when they mean to`, 'success')
    } else {
        showSnackbar(`${participantName} joined`, 'success');
    }
});

$(document).on('memeUploaded', (e, data) => {
    const num_uploaders = data.num_uploaders;
    const num_memes = data.num_memes;
    const text = `${num_memes} meme${num_memes != 1 ? 's' : ''} submitted by ${num_uploaders} ${num_uploaders != 1 ? 'people' : 'person'}`
    $("#num_memes").text(text);
});

$(document).on('competitionCancelled', (e, data) => {
    console.log('Competiton has been cancelled');
    window.location.reload();
})

$(document).on('competitionFinished', (e, data) => {
    console.log('Competition has finished');
    $('#comp-timer').css('display', 'none');
    $('#comp-info-card').css('display', '');
    $("#comp-started").css('display', 'none');
    $("#comp-waiting").css('display', 'none');
    $("#comp-tiebreaker").css('display', 'none');
    $("#comp-finished").css('display', '');

    $("#next-meme-btn").css('display', 'none');
    showSnackbar('Competition has finished', 'info')

    $('#winning-meme').html(data.winner_html);
    $('#comp-results').html(data.results_html);


});

$(document).on('memeVoted', (e, data) => {
    $("#num_votes").text(data);
});

$(document).on('nextMeme', (e, data) => {
    console.log('advancing to next meme');

    // reset the page
    $('#vote-form')[0].reset();
    $('.vote-radio').prop('disabled', false)
    $('#comp-timer').css('display', 'none')
    $('#comp-info-card').css('display', '')
    $("#comp-started").css('display', '');
    $("#comp-waiting").css('display', 'none');
    $('input[name="vote"]').prop('checked', false);
    $("#num_votes").text('0');
    $(".square-image").attr("src", "");

    const memeUrl = data.url;
    const memeCtr = data.ctr;
    const numMemes = data.num_memes


    $('#meme-ctr').text(`Meme ${memeCtr}/${numMemes}`);
    $("#current-meme-image").attr('src', memeUrl)
    showSnackbar(`Time to Vote (${memeCtr}/${numMemes})`, 'success');

    // Disable the next meme button for 3 seconds after advancing
    // hopefully this will avoid accidental clicks
    $('#next-meme-btn').prop("disabled", true);
    setTimeout(function () {
        $("#next-meme-btn").prop("disabled", false);
    }, 3000);
    $("#vote-form :input").prop('readonly', false);

    // reset the timer
    startTimer();
});

$(document).on('updateEmoji', (e, data) => {
    createEmoji(data);
});

$(document).on('memeDeleted', (e, data) => {
    const memeId = data;
    const memesContainer = $('#submitted-memes-container')
    memesContainer.find(`[id="meme-${memeId}"]`).remove()

});

$(document).on('memeSubmitted', (e, data) => {
    // display the memes body div
    $('#memes-body').css('display', '');

    // add the uploaded memes to the page
    $('#submitted-memes-container').prepend(data.memes_html);
})

$(document).on('eventUpdated', (e, data) => {
    $('#events').prepend(data.log_html);
})