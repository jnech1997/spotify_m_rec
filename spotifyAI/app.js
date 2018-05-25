var express= require('express');
var request= require('request');
var querystring = require('querystring');
var client_id= '418a5497c83c448d9edcc219d9fce50b';
var client_secret= '6c2c9a1b9f374338bf9a525fba167f42';
var redirect_uri = "http://localhost:8888/callback/"; // Your redirect uri
var cookieParser = require('cookie-parser');
var fs = require('fs');
var username= undefined;

/**
 * Generates a random string containing numbers and letters
 * @param  {number} length The length of the string
 * @return {string} The generated string
 */
var generateRandomString = function(length) {
  var text = '';
  var possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';

  for (var i = 0; i < length; i++) {
    text += possible.charAt(Math.floor(Math.random() * possible.length));
  }
  return text;
};
var stateKey = 'spotify_auth_state';
var app = express();
/*Set up public 'home' directory */
app.use(express.static(__dirname + '/public'))
   .use(cookieParser());

/* Post typed in username */
app.post('/userName/:userId', function(req, res) {
  username= req.params.userId;
  console.log(username);
});

/* Post authorization request request */
app.get('/Query', function(req, res) {
  //console.log(username);
    var state = generateRandomString(16);
    res.cookie(stateKey, state);
    //console.log("inside query responder");
    // your application requests authorization
    var scope = 'user-read-private user-read-email';
    res.redirect('https://accounts.spotify.com/authorize?' +
      querystring.stringify({
        response_type: 'code',
        client_id: client_id,
        scope: scope,
        redirect_uri: redirect_uri,
        state: state
      }));
});

/* Get access token */
app.get('/callback', function(req, res) {
  // your application requests refresh and access tokens
  // after checking the state parameter
  var code = req.query.code || null;
  var state = req.query.state || null;
  var storedState = req.cookies ? req.cookies[stateKey] : null;

  if (state === null || state !== storedState) {
    //console.log("inside callback function");
    res.redirect('/#' +
      querystring.stringify({
        error: 'state_mismatch'
      }));
  } else {
    res.clearCookie(stateKey);
    var authOptions = {
      url: 'https://accounts.spotify.com/api/token',
      form: {
        code: code,
        redirect_uri: redirect_uri,
        grant_type: 'authorization_code'
      },
      headers: {
        'Authorization': 'Basic ' + (new Buffer(client_id + ':' + client_secret).toString('base64'))
      },
      json: true
    };

    request.post(authOptions, function(error, response, body) {
      if (!error && response.statusCode === 200) {
        var access_token = body.access_token,
            refresh_token = body.refresh_token;
        var playlists = {
          url: 'https://api.spotify.com/v1/users/'.concat(username).concat('/playlists'),
          headers: { 'Authorization': 'Bearer ' + access_token },
          json: true
        };
        var tracksLink;
        // use the access token to access the Spotify Web API
        if (username != undefined) {
            request.get(playlists, function(error, response, body) {
              for (i in body.items) {
                tracksLink= body.items[i].tracks.href;
                var tracks = {
                    url: tracksLink,
                    headers: { 'Authorization': 'Bearer ' + access_token },
                    json: true
                };
                request.get(tracks, function(error, response, body) {
                    /*fs.appendFile("output.txt", body.items, function(err) {
                        if (err) {
                            return console.log(err);
                        }
                    });*/
                    for (el in body.items) {
                    
                      var trackName= body.items[el].track;
                      //console.log(trackName);
                      var jsonTrackName= JSON.stringify(trackName, null, 4);
                      fs.appendFile("output.txt", jsonTrackName.concat("\n"), function(err) {
                          if(err) {
                            return console.log(err);
                          }
                      });
                    }
                });
              }
            });
            //reset username value so it doesn't linger after callback
            username=undefined;
        }
         // we can also pass the token to the browser to make requests from there
        res.redirect('/#' +
          querystring.stringify({
            access_token: access_token,
            refresh_token: refresh_token
          }));
      } else {
        res.redirect('/#' +
          querystring.stringify({
            error: 'invalid_token'
          }));
      }
    });
  }
});
/* Start the server */
console.log('Listening on 8888');
app.listen(8888);
