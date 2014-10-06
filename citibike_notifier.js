#!/usr/bin/env node
//
// Send mail with trip duration after every citibike trip
//
//

var STARTURL = "https://www.citibikenyc.com/login";
var TRIPURL = "https://www.citibikenyc.com/member/trips";

var CHECK_INTERVAL_MILLIS = 5 * 60 * 1000;
//var MAILFROM = 'Ernie Hershey <citinotifier@ernie.org>';
//var MAILTO = 'Ernie Hershey <citinotify@ernie.org>';
var MAILTO = 'Ernie Hershey <ehershey@gmail.com>';
var MAILFROM = 'Ernie Hershey <ehershey@gmail.com>';
var SUBJECT = 'New Bikeshare Trip';

var citibike_auth = require("citibike_auth");
var Browser = require("zombie");
var storage = require('node-persist');
var nodemailer = require('nodemailer');
var moment = require('moment');


storage.initSync();
var nodemailer_transport = nodemailer.createTransport();

// Load the page from localhost
browser = new Browser()
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
    if(err) throw(err);
    console.log('browser.location.pathname: ' + browser.location.pathname);
    if(browser.location.pathname !== '/member/profile')
    {
      console.error("Login error? Path after login form submit: " + browser.location.pathname + " but expected /member/profile");
    }
    check_trips();
    setInterval(check_trips,CHECK_INTERVAL_MILLIS);
  });
});


function check_trips() 
{
  console.log("checking for new trips");
  browser.visit(TRIPURL, function(err, passed_browser, status, errors) {
    console.log('in trips callback');
    var trip_trs = browser.querySelectorAll("tr.trip");
    console.log('trip_trs: ' + trip_trs);
    for(var i = 0 ; i < trip_trs.length ; i++) 
    {
      var trip_tr = trip_trs[i];
      var trip_id = trip_tr.id;
      var trip_duration = trip_tr.getAttribute('data-duration-seconds');
      console.log('trip_id: ' + trip_id);
      console.log('trip_duration: ' + trip_duration);
      if(is_trip_new(trip_tr))
      {
        notify_trip(trip_tr);
      }
      else
      {
        console.log("seen trip already, not notifying");
      }
    }
  });
}

// <tr class="trip" id="trip-15932144" data-start-station-id="248" data-start-timestamp="1412458608" data-end-station-id="514" data-end-timestamp="1412459885" data-duration-seconds="1277">
//

function notify_trip(trip_tr) {
  var trip_id = trip_tr.id;
  console.log("notifying for trip with id: " + trip_id);
  var duration = moment.duration(trip_tr.getAttribute("data-duration-seconds")*1, "seconds").humanize();

  nodemailer_transport.sendMail({
      from: MAILFROM,
      to: MAILTO,
      subject: SUBJECT,
      text: 'Recent trip took: ' + duration,
      html: 'Recent trip took: ' + duration
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

