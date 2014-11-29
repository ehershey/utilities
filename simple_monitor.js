#!/usr/bin/env node
// Monitor simple URL's for jquery selectors, send email on failures
// 
// To override errors to ignore by detail text, modify 'ignore_text' 
// fields in url_configs objects.
//
//

var async = require('async');
var jsdom = require('jsdom');
var fs = require('fs');
var nodemailer = require('nodemailer');
var date_utils = require('date-utils');

var MAILTO = 'Ernie Hershey <ernie@mongodb.com>'
var MAILFROM = 'Simple Monitor <ernie@mongodb.com>'
var SUBJECT = 'Simple_monitor alert!'

var nodemailer_transport = nodemailer.createTransport();

// For each object in url_configs, hit "url" and run the "cell_selector" through jquery. 
// if anything is matched and "negated" is not true (or if nothing matches and "negated" is true), 
// and the detail text (return value of text_finder_from_cell_jqobj($(cell_selector)) !== 
// "ignore_text", send email from MAILFROM to MAILTO with details on the error
//
//

var url_configs = [ 
    { 
    url: 'https://jira.mongodb.org/issues/?jql=assignee%20%3D%20%22ernie.hershey%4010gen.com%22%20AND%20(priority%20%3D%20%22Blocker%20-%20P1%22%20OR%20priority%20%3D%20%22Critical%20-%20P2%22)%20AND%20status%20!%3D%20%22Resolved%22%20and%20status%20!%3D%20%22Closed%22%20AND%20status%20!%3D%20%22In%20Progress%22',
    cell_selector: "a.issue-link",
    text_finder_from_cell_jqobj: function(jqobj) { return jqobj.text(); },
    ignore_text: '',
    negated: false
  },
 
  { 
    url: 'http://buildbot.mongodb.org:8081/builders/Windows%2032-bit/builds/-1',
    cell_selector: "div.success:contains('( 0 secs )')",
    text_finder_from_cell_jqobj: function(jqobj) { return "Windows 32-bit builder in zombie state"; },
    ignore_text: '',
    negated: false
  },
 
  { 
    url: 'http://downloads-distro.mongodb.org/repo/ubuntu-upstart/dists/dist/10gen/binary-amd64/',
    cell_selector: "a:contains(deb)",
    text_finder_from_cell_jqobj: function(jqobj) { return "Unused"; },
    ignore_text: '',
    negated: true
  },
 
  { 
    url: 'http://repo.mongodb.org/repo/ubuntu-upstart/dists/dist/10gen/binary-amd64/',
    cell_selector: "a:contains(deb)",
    text_finder_from_cell_jqobj: function(jqobj) { return "Unused"; },
    ignore_text: '',
    negated: true
  },
  
  { 
    url: 'http://repo.mongodb.com/yum/redhat/6/mongodb-enterprise/2.6/x86_64/repodata/',
    cell_selector: "a:contains(repomd.xml)",
    text_finder_from_cell_jqobj: function(jqobj) { return "Unused"; },
    ignore_text: '',
    negated: true
  },
  { 
    url: 'https://jenkins.10gen.com/',
    cell_selector: "body:contains(Please wait while Jenkins is restarting.)",
    text_finder_from_cell_jqobj: function(jqobj) { return jqobj.text(); },
    ignore_text: '',
    negated: false
  },
  { 
    url: 'https://jenkins.10gen.com/robots.txt',
    cell_selector: "body:contains(Disallow)",
    text_finder_from_cell_jqobj: function(jqobj) { return "Unused"; },
    ignore_text: '',
    negated: true
  },
  { 
    url: 'http://mci.10gen.com/',
    cell_selector: "#content",
    text_finder_from_cell_jqobj: function(jqobj) { return "Unused"; },
    ignore_text: '',
    negated: true
  },
  { 
    url: 'http://mci-motu.10gen.cc:8080/api/',
    cell_selector: "body:contains(API)",
    text_finder_from_cell_jqobj: function(jqobj) { return "Unused"; },
    ignore_text: '',
    negated: true
  },
  { 
    url: 'http://mci.10gen.com/hosts/',
    cell_selector: "td:contains(unreachable)",
    // Crazy jquery magic to get a delimited string of all the unreachable hostnames
    // 
    // Mostly from http://bugs.jquery.com/ticket/5858
    //
    text_finder_from_cell_jqobj: function(jqobj) { return jqobj.parent().children(":first-child").not(":last").append(" | ").end().text(); },
    ignore_text: '',
    negated: false
  },
  { 
    url: 'http://www.mongodb.org/downloads',
    cell_selector: ".release-version",
    text_finder_from_cell_jqobj: function(jqobj) { return "Unused"; },
    ignore_text: '',
    negated: true
  },
  { 
    url: 'http://buildlogs.mongodb.org/',
    cell_selector: "body",
    text_finder_from_cell_jqobj: function(jqobj) { return "Unused"; },
    ignore_text: '',
    negated: true
  },
  /* 
   { 
    url: 'http://buildbot.mongodb.org/buildslaves',
    cell_selector: ".offline",
    text_finder_from_cell_jqobj: function(jqobj) { return jqobj.parent().children(":first-child").text(); },
    ignore_text: '',
    negated: false
  },
  { 
    url: 'http://buildbot-special.10gen.com/buildslaves',
    cell_selector: ".offline",
    text_finder_from_cell_jqobj: function(jqobj) { return jqobj.parent().children(":first-child").text(); },
    // ignore_text: 'bs-e-rhel57',
    ignore_text: '',
    negated: false
  },
  */

  //{
    //url: 'http://frau.ernie.org/',
    //cell_selector: "body:contains(frau.ernie.org)",
    //text_finder_from_cell_jqobj: function(jqobj) { return jqobj.text(); },
    //ignore_text: '',
    //negated: true
  //},
  //{ 
    //url: 'http://dropbox.ernie.org/weather.html',
    //cell_selector: "body:contains(Weather widget)",
    //text_finder_from_cell_jqobj: function(jqobj) { return jqobj.text(); },
    //ignore_text: '',
    //negated: true
  //},
  //{ 
    //url: 'http://numpebble.ernie.org/config.html',
    //cell_selector: "body:contains(Title)",
    //text_finder_from_cell_jqobj: function(jqobj) { return jqobj.text(); },
    //ignore_text: '',
    //negated: true
  //},
  //{ 
    //url: 'http://goeverywhere.ernie.org/get_points.cgi?from=09/15/2014&to=09/15/2014&min_lon=-80&max_lon=80&min_lat=-90&max_lat=90&bound_string=%28%2840.661127887535734%2C%20-74.28702794525663%29%2C%20%2840.77718145714685%2C%20-73.68380986664334%29%29&rind=1/1',
    //cell_selector: "body:contains(point)",
    //text_finder_from_cell_jqobj: function(jqobj) { return jqobj.text(); },
    //ignore_text: '',
    //negated: true
  //},
  { 
    url: 'https://github.com/ehershey',
    
    // Date logic to get the full month name and day number of the day that was 23 hours ago,
    // so until 11pm this will return yesterday. This can be shaky logic since most days it 
    // shouldn't trigger anyways
    //
    cell_selector: 'div.contrib-column:contains(Current streak):contains(' + (new Date((new Date()) - 23 * 60 * 60 * 1000)).toFormat("MMMM D") + '), ' +
                      'div.contrib-column:contains(Current streak):contains(' + (new Date()).toFormat("MMMM D") + ')',
    text_finder_from_cell_jqobj: function(jqobj) { return "date not found in page! (" + (new date((new date()) - 23 * 60 * 60 * 1000)).toformat("mmmm dd") + ')'; },
    ignore_text: '',
    negated: true
  },

];

var errors_found = 0;

async.each(url_configs, check_url, function() { done_checking_all() });

function check_url(url_config, done_checking_one) {
  var url = url_config.url;
  var cell_selector = url_config.cell_selector;
  var ignore_text = url_config.ignore_text;
  var negated = url_config.negated;

  var text_finder_from_cell_jqobj = url_config.text_finder_from_cell_jqobj;

  console.log('Starting request for url: ' + url);

  var handler = function(errors, window) {
    console.log('');
    console.log('In callback for url: ' + url);

    if(errors) {
      console.log('errors loading url: ' + errors);
      console.log('sending mail');
      nodemailer_transport.sendMail({
          from: MAILFROM,
          to: MAILTO,
          subject: SUBJECT,
          text: 'Error checking URL: ' + url + "\nError detail text: " + errors,
          html: '<b>Error checking URL: <a href="' + url + '">' + url + '</a></b><br/>Error detail text: ' + errors
      });
 
    }
    else {

      console.log("looking for cells with selector: " + cell_selector);
      var cells = window.$(cell_selector);
      var detail_text;

      console.log('found cells: ' + cells.length);

      if( ( cells.length && !negated ) || ( !cells.length && negated ) ) { 

        detail_text = text_finder_from_cell_jqobj(cells);

        if(ignore_text && detail_text === ignore_text) {
          console.log('detail_text === ignore_text; ignoring error (' + detail_text + ')');
        } else {
          console.log('detail_text: ' + detail_text);
          console.log('sending mail');
          nodemailer_transport.sendMail({
              from: MAILFROM,
              to: MAILTO,
              subject: SUBJECT,
              text: 'Error checking URL: ' + url + '\nCell selector: ' + cell_selector + '\nMatching cell count: ' + cells.length + '\nError detail text: ' + detail_text,
              html: '<b>Error checking URL: <a href="' + url + '">' + url + '</a></b><br/>Cell selector: ' + cell_selector + '<br/>Matching cell length: ' + cells.length + '<br/>Error detail text: ' + detail_text
          });
          errors_found++;
        }
      }
    }
    done_checking_one();
  };
  var timeout = setTimeout(function() { handler('timed out',null); }, 10000);
  jsdom.env ( url, ["http://code.jquery.com/jquery.js"], function(errors, window) { clearTimeout(timeout); handler(errors, window); });
}

function done_checking_all(err) {
  console.log('err: ' + err);
  console.log('Total errors found: ' + errors_found);
}
