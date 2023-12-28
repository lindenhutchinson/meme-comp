function advanceCompetition(compName) {
    $.ajax({
        // url: "{% url 'advance_competition' competition.name %}",
        url: `/api/competition/${compName}/advance`,
        type: "POST",
        data: {},
        beforeSend: function (xhr) {
            xhr.setRequestHeader("X-CSRFToken", csrfToken);
        },
        success: function (response) {
        },
        error: function (xhr, status, error) {
            showSnackbar('Unable to advance competition', 'danger');
        }
    });
}
    // restart the competition via AJAX
function cancelCompetition(compName) {
    var cancelCheck = 'Are you sure you want to cancel the competition? This will erase all votes.'

    if(!confirm(cancelCheck)) {
        return
    }
    $.ajax({
        // url: "{% url 'cancel_competition' competition.name %}",
        url: `/api/competition/${compName}/cancel`,

        type: "POST",
        data: {},
        beforeSend: function (xhr) {
            xhr.setRequestHeader("X-CSRFToken", csrfToken);
        },
        success: function (response) {
            // Handle success response
            // Update necessary elements
            $('#start-comp-btn').attr('disabled', false);
            $('#cancel-comp-btn').attr('disabled', true);
            $('#start-comp-btn').text('Start Competition');
            $("#next-meme-btn").css('display', 'none');

        },
        error: function (xhr, status, error) {
            showSnackbar('Unable to cancel competition', 'danger');
        }
    });
}
    // Start competition via AJAX
function startCompetition(compName) {
    $.ajax({
        // url: "{% url 'start_competition' competition.name %}",
        url: `/api/competition/${compName}/start`,

        type: "POST",
        data: {},
        beforeSend: function (xhr) {
            xhr.setRequestHeader("X-CSRFToken", csrfToken);
        },
        success: function (response) {
            // Handle success response
            // Update necessary elements
            $('#start-comp-btn').attr('disabled', true);
            $('#cancel-comp-btn').attr('disabled', false);
            $('#start-comp-btn').text('Competition started');
            $("#next-meme-btn").css('display', 'inline');
        },
        error: function (xhr, status, error) {
            showSnackbar(xhr.responseJSON.detail, 'danger')
        }
    });
}


    // submit vote via AJAX
    function submitVote(compName) {
        // Get the selected vote option
        var selectedOption = document.querySelector('input[name="vote"]:checked').value;
        // Prepare the data to be sent in the AJAX request
        var formData = new FormData();
        formData.append('vote', selectedOption);
        $.ajax({
            // url: `/api/competition/{{competition.name}}/vote`,
            url: `/api/competition/${compName}/vote`,
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
            beforeSend: function (xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrfToken);
            },
            success: function (response) {
                if (Math.random() < 0.05 && selectedOption == 0) {
                    showSnackbar("Everyone's a critic", 'success');
                } else {
                    showSnackbar('Vote submitted', 'success')
                }
            },
            error: function (xhr, status, error) {
                if (xhr.status === 403) {
                    showSnackbar(xhr.responseJSON.detail, 'danger')
                } else {
                    showSnackbar("That vote was not submitted...", 'danger')
                }
            }
        });
    }


    function submitMeme(compName) {
        $('#meme-spinner').css('display', '');

        var form = document.getElementById("upload-form");
        var formData = new FormData(form);

        $.ajax({
            // url: "{% url 'meme_upload' comp_name=competition.name %}",
            url: `/api/competition/${compName}/upload`,
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
            success: function (response) {
                // Handle success response
                // Clear the input field
                $('#image').val('');
                // Load submitted memes
                if (Math.random() < 0.01) {
                    showSnackbar("lol that's a good one", "success");
                } else {
                    showSnackbar('Meme uploaded', 'success');
                }
                $('#memes-body').css('display', '');
                $(document).trigger('memeSubmitted', response);
            },
            error: function (xhr, status, error) {
                if (xhr.status === 403) {
                    showSnackbar(xhr.responseJSON.detail, 'danger')
                } else {
                    showSnackbar('Error uploading your meme :(', 'danger')
                }
            }
        }).then(() => {
            $('#meme-spinner').css('display', 'none');
        });
    }

    function deleteMeme(button) {
        if( deleteSafety ){
            var deleteCheck = 'Are you sure you want to delete that meme?'
            if (Math.random() < 0.01) {
                deleteCheck = "Try uploading the right meme next time"
            }
            if (!confirm(deleteCheck)) {
                return
            }
        }

        const memeId = $(button).data('meme-id');
        $.ajax({
            url: `/api/meme/${memeId}`,
            type: "DELETE",
            processData: false,
            contentType: false,
            beforeSend: function (xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrfToken);
            },
            success: function (response) {
                // Load submitted memes
                showSnackbar('Meme deleted', 'success')
                $(document).trigger('memeDeleted', memeId);

            },
            error: function (xhr, status, error) {
                if (xhr.status === 403) {
                    showSnackbar(xhr.responseJSON.detail, 'danger')
                } else {
                    showSnackbar('Unable to delete meme', 'danger')
                }
            }
        });
    }
