#!/usr/bin/env node
//
// Send mail with trip duration after every citibike trip
//
//

var STARTURL = "https://www.citibikenyc.com/login";
var TRIPURL = "https://www.citibikenyc.com/member/trips";

// Kill ourselves if we take this long
//
var PROCESS_TIMEOUT_MILLIS = 20000;

// var MAILFROM = 'Ernie Hershey <citinotifier@ernie.org>';
// var MAILTO = 'Ernie Hershey <citinotify@ernie.org>';
var MAILTO = 'Ernie Hershey <ehershey+citibike@gmail.com>';
var MAILFROM = 'Ernie Hershey <ehershey+citibike@gmail.com>';
var SUBJECT = 'New Bikeshare Trip';

var citibike_auth = require("citibike_auth");
var Browser = require("zombie");
var storage = require('node-persist');
var nodemailer = require('nodemailer');
var moment = require('moment');


var fatal_timeout = setTimeout(function() { console.log('timeout'); process.exit(); }, PROCESS_TIMEOUT_MILLIS);

storage.initSync();
var nodemailer_transport = nodemailer.createTransport({
      service: 'Gmail',
        auth: {
            user: citibike_auth.gmail_username,
            pass: citibike_auth.gmail_password
      }
});
var browser = new Browser();

var cookies = storage.getItem("cookies");

var done = function(err) { clearTimeout(fatal_timeout); if(err) { console.log("err: " + err); } else { console.log("Checked for trips") } };

console.log("cookies: " + cookies);

if(cookies && typeof(cookies) === 'string') {
  browser.loadCookies(cookies);
  check_trips(null,done);
  console.log('browser.saveCookies(): ' + browser.saveCookies());
  storage.setItem("cookies", browser.saveCookies());
}
else {
  login(null, function(err) { check_trips(err, done); });
  console.log('browser.saveCookies(): ' + browser.saveCookies());
  storage.setItem("cookies", browser.saveCookies());
}

function login(err,callback)
{
  if(err) {
    callback(err);
    return;
  }
  browser.visit(STARTURL, function (err, passed_browser, status, errors) {
    console.log('err: ' + err);
    console.log('passed_browser: ' + passed_browser);
    console.log('browser: ' + browser);
    console.log('status: ' + status);
    console.log('errors: ' + errors);
    if(err) throw(err);
    var usernameinput =   browser.query("#subscriberUsername");
    console.log('usernameinput: ' + usernameinput);
    var passwordinput =   browser.query("#subscriberPassword");
    console.log('passwordinput: ' + passwordinput);
    browser.fill("#subscriberUsername", citibike_auth.username);
    browser.fill("#subscriberPassword", citibike_auth.password);
    browser.pressButton("#login_submit", function(err) 
    { 
      console.log('in submit callback');
      if(err) callback(err);
      var pathname = browser.location.pathname;
      console.log('pathname: ' + pathname);
      console.log('browser.saveCookies(): ' + browser.saveCookies());
      storage.setItem("cookies", browser.saveCookies());
      if(pathname.indexOf('/member/trips') === -1 && pathname !== '/member/profile')
      {
        callback("Login error? Path after login form submit: " + pathname + " but expected /member/profile or /member/trips");
      }
      callback();
    });
  });
}


// can be used as a callback for login() or called directly and will
// call login() if not logged in with itself as a callback
//
function check_trips(err, callback, page) 
{
  if(err) { 
    callback(err);
    return;
  }
  console.log("checking for new trips");
  var url = TRIPURL;
  if(page)
  {
    url += '/' + page;
  }
  console.log('url: ' + url);
  browser.visit(url, function(err, passed_browser, status, errors) {
    console.log('in trips callback');
    var pathname = browser.location.pathname;
    console.log('pathname: ' + pathname);
    if(pathname.indexOf('/member/trips') === -1)
    {
      console.log("location is not trip page, re-running login()");
      login(null,function(err) { check_trips(err,callback); });
      return;
    }

    var trip_trs = browser.querySelectorAll("tr.trip");
    console.log('trip_trs: ' + trip_trs);
    if(trip_trs.length === 0)
    {
      console.log("trip_trs.length === 0, looking at next page");
      var after_slash = pathname.replace(/.*\//,'');
      var next_page;
      if(after_slash === 'trips')
      {
        next_page = 2;
      } 
      else 
      {
        next_page = after_slash*1 + 1;
      }
      console.log('next_page: ' + next_page);

      check_trips(null,callback,next_page);
      return;
    }
    for(var i = 0 ; i < trip_trs.length ; i++) 
    {
      var trip_tr = trip_trs[i];
      var trip_id = trip_tr.id;
      var trip_duration = trip_tr.getAttribute('data-duration-seconds');
      var now = (new Date()).getTime()/1000;
      var end_timestamp = trip_tr.getAttribute("data-start-timestamp");
      var trip_age = moment.duration(now - end_timestamp, "seconds").humanize();



      console.log('trip_id: ' + trip_id);
      console.log('now: ' + now);
      console.log('trip_duration: ' + trip_duration);
      console.log('end_timestamp: ' + end_timestamp);
      console.log('trip_age: ' + trip_age);

      // Only notify if the trip is new and it's either a legitimate length (over 60 seconds) or older than 60 seconds - 
      // The extra logic is to account for trips showing up as tiny amounts of time immediately after they're over
      // then getting populated with real durations after the notification has been sent
      //
      if(is_trip_new(trip_tr) && (trip_duration > 60 || trip_age > 60))
      {
        notify_trip(trip_tr);
      }
      else
      {
        console.log("seen trip already, not notifying");
      }
    }
    callback(null);
  });
}

// <tr class="trip" id="trip-15932144" data-start-station-id="248" data-start-timestamp="1412458608" data-end-station-id="514" data-end-timestamp="1412459885" data-duration-seconds="1277">
//

function notify_trip(trip_tr) {
  var trip_id = trip_tr.id;
  console.log("notifying for trip with id: " + trip_id);

  

  var duration_seconds = trip_tr.getAttribute("data-duration-seconds");
  console.log('duration_seconds: ' + duration_seconds);
  var duration = moment.duration(duration_seconds*1, "seconds").humanize();

  nodemailer_transport.sendMail({
      from: MAILFROM,
      to: MAILTO,
      subject: SUBJECT,
      text: 'Recent trip took: ' + duration,
      html: '<html><head><title>' + SUBJECT + '</title></head><body>Recent trip took: ' + duration + '</body></html>'
  }, function(error, info){
    if(error){
        console.log(error);
    }else{
        console.log('Message sent: ' + info.response);
    }
});
 


  var trip_notify_info = { notified_at: new Date() };
  var key = "trip_notify_info_" + trip_id;
  storage.setItem(key, trip_notify_info);
}

// if we have notification info, it's not new
// 
function is_trip_new(trip_tr) {
  var trip_id = trip_tr.id;
  var key = "trip_notify_info_" + trip_id;
  var trip_notify_info = storage.getItem(key);
  if(trip_notify_info)
  {
    return false;
  }
  else
  {
    return true;
  }
}

