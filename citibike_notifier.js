#!/usr/bin/env node
//
// Send mail with trip duration after every citibike trip
//
//

var STARTURL = "https://member.citibikenyc.com/profile/login";
var TRIPURL = "https://member.citibikenyc.com/profile/trips/00002139-1";
var USERNAME_SELECTOR = ".ed-popup-form_login__form-input_username";
var PASSWORD_SELECTOR = ".ed-popup-form_login__form-input_password";
var SUBMIT_BUTTON_SELECTOR = "button.ed-popup-form_login__form-btn";

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
var jsdom = require("jsdom");
var window = jsdom.jsdom().defaultView;

jsdom.jQueryify(window, "http://code.jquery.com/jquery-2.1.1.js", function () {
    window.$("body").append('<div class="testing">Hello World, It works</div>');

      console.log(window.$(".testing").text());
});

// Never refer to under 60 minutes as "an hour"
//
moment.relativeTimeThreshold('m',60);


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
    var usernameinput =   browser.query(USERNAME_SELECTOR);
    console.log('usernameinput: ' + usernameinput);
    var passwordinput =   browser.query(PASSWORD_SELECTOR);
    console.log('passwordinput: ' + passwordinput);
    browser.fill(USERNAME_SELECTOR, citibike_auth.username);
    browser.fill(PASSWORD_SELECTOR, citibike_auth.password);
    browser.pressButton(SUBMIT_BUTTON_SELECTOR, function(err)
    {
      console.log('in submit callback');
      if(err) callback(err);
      var pathname = browser.location.pathname;
      console.log('pathname: ' + pathname);
      console.log('browser.saveCookies(): ' + browser.saveCookies());
      storage.setItem("cookies", browser.saveCookies());
      if(pathname.indexOf('/profile/trips') === -1 && pathname !== '/profile/login')
      {
        callback("Login error? Path after login form submit: " + pathname + " but expected /profile/trips or /profile/login");
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
  browser.visit(url, function() {
    console.log("IN CALLBACK");
  });
  browser.visit(url, function(err, passed_browser, status, errors) {
    console.log('in trips callback');
    var pathname = browser.location.pathname;
    console.log('pathname: ' + pathname);
    if(pathname.indexOf('/profile/trips') === -1)
    {
      console.log("location is not trip page, re-running login()");
      login(null,function(err) { check_trips(err,callback); });
      return;
    }

    var trip_elements = browser.querySelectorAll("div.ed-table__item_trip");
    console.log('trip_elements: ' + trip_elements);
    console.log('trip_elements.length: ' + trip_elements.length);
    if(trip_elements.length === 0)
    {
      console.log("trip_elements.length === 0");
      callback();
      return;
    }
    for(var i = 0 ; i < trip_elements.length ; i++)
    {
      var trip_element = trip_elements[i];
      console.log('trip_element: ' + trip_element);
      console.log('window.$(trip_element).text(): ' + window.$(trip_element).text());
      var trip_id = window.$(trip_element).text().replace(/[^0-9a-zA-Z]/g,"");
      var now = (new Date()).getTime()/1000;
      var start_timestamp = moment(window.$(".ed-table__item__info__sub-info_trip-start-date",trip_element).text())/1000;
      var end_timestamp = moment(window.$(".ed-table__item__info__sub-info_trip-end-date",trip_element).text())/1000;
      var trip_duration = end_timestamp - start_timestamp;
      var trip_age = moment.duration(now - start_timestamp, "seconds").humanize();



      console.log('trip_id: ' + trip_id);
      console.log('now: ' + now);
      console.log('trip_duration: ' + trip_duration);
      console.log('start_timestamp: ' + start_timestamp);
      console.log('end_timestamp: ' + end_timestamp);
      console.log('trip_age: ' + trip_age);

      // Only notify if the trip is new and it's either a legitimate length (over 60 seconds) or older than 60 seconds -
      // The extra logic is to account for trips showing up as tiny amounts of time immediately after they're over
      // then getting populated with real durations after the notification has been sent
      //
      if(is_trip_new(trip_element) && (trip_duration > 60 || trip_age > 60))
      {
        notify_trip(trip_element, trip_elements);
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

function notify_trip(trip_element, trip_elements) {
  var trip_id = window.$(trip_element).text().replace(/[^0-9a-zA-Z]/g,"");
  console.log("notifying for trip with id: " + trip_id);



  var start_timestamp = moment(window.$(".ed-table__item__info__sub-info_trip-start-date",trip_element).text())/1000;
  var end_timestamp = moment(window.$(".ed-table__item__info__sub-info_trip-end-date",trip_element).text())/1000;
  var duration_seconds = end_timestamp - start_timestamp;

  var verbose_start_timestamp = moment(new Date(start_timestamp * 1000)).format('HH:mm MM/DD/YYYY');
  console.log('duration_seconds: ' + duration_seconds);
  console.log('verbose_start_timestamp: ' + verbose_start_timestamp);
  console.log('start_timestamp: ' + start_timestamp);
  var duration = moment.duration(duration_seconds*1, "seconds").humanize();

  var title = SUBJECT;
  var body_text = 'Bikeshare trip took ' + duration + ' at ' + verbose_start_timestamp;
  console.log('body_text: ' + body_text);
  nodemailer_transport.sendMail({
      from: MAILFROM,
      to: MAILTO,
      subject: SUBJECT,
      text: body_text,
      html: '<html><head><title>' + title + '</title></head><body>' + body_text + '</body></html>'
  }, function(error, info){
    if(error) {
        console.log(error);
    } else{
        console.log('Message sent: ' + info.response);
    }
});



  var trip_notify_info = { notified_at: new Date() };
  var key = "trip_notify_info_" + trip_id;
  storage.setItem(key, trip_notify_info);
}

// if we have notification info, it's not new
//
function is_trip_new(trip_element) {
  var trip_id = window.$(trip_element).text().replace(/[^0-9a-zA-Z]/g,"");
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

