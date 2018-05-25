$(document).ready(function () {
    var queryVal= "";
    document.getElementById('submit').addEventListener("click", function() {
        queryVal= document.getElementById('query').value;
        console.log(queryVal);
        if (queryVal != "") {
        var link= "http://localhost:8888/userName/".concat(queryVal);
        console.log(link);
        $.ajax({
            type: 'POST',
            url: link
        });
    }
    });
});
