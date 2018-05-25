$.ajaxSetup({
    timeout: 30000,
    cache: false
});

var audioElement;
var currentPlayButton;

function submitCollaborative() {
    $("#collaborative_div").html("<h2>Loading...</h2>");
    $.ajax({
        type: "GET",
        data: $("#collaborative_form").serialize(),
        dataType: "html",
        url: '/collaborative'
    }).done(function (data) {
        $("#collaborative_div").html(data);
    }).fail(function(jqXHR, textStatus, error) {
        setTimeout(submitCollaborative, 5000);
    });
}

function submitKNearest() {
    $("#k-nearest_div").html("<h2>Loading...</2>");
    $.ajax({
        type: "GET",
        data: $("#k-nearest_form").serialize(),
        dataType: "html",
        url: '/k-nearest'
    }).done(function (data) {
        $("#k-nearest_div").html(data);
    }).fail(function(jqXHR, textStatus, error) {
        setTimeout(submitKNearest, 5000);
    });
}

function stopAudio() {
    if (audioElement != null) {
        audioElement.pause();
    }

    if (currentPlayButton != null) {
        currentPlayButton.text('Play');
        currentPlayButton = null;
    }
}

$(document).ready(function() {
    $("#collaborative_form").submit(function(event) {
        event.preventDefault();

        stopAudio();

        submitCollaborative();
    });

    $("#k-nearest_form").submit(function(event) {
        event.preventDefault();

        stopAudio();

        submitKNearest();
    });

    $(document).on("click", ".preview_play", function(event) {
        if (currentPlayButton != null) {
            currentPlayButton.text('Play');
            audioElement.pause();
        } else if (audioElement == null) {
            audioElement = document.createElement('audio');
        }

        if (currentPlayButton != null && $(this).data('url') === currentPlayButton.data('url')) {
            currentPlayButton = null;
            return;
        }
        
        audioElement.setAttribute('src', $(this).data('url'));
        
        $(this).text('Pause');
        currentPlayButton = $(this);

        audioElement.addEventListener('ended', function() {
            currentPlayButton.text('Play');
        });

        audioElement.play();
    });
});