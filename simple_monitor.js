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
// and the detail text (return value of text_finder_from_cell_jqobj($(cell_selector)) !== "ignore_text",
// send email from MAILFROM to MAILTO with details on the error
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
    url: 'https://jenkins.10gen.com/robots.txt',
    cell_selector: "body:contains(Disallow)",
    text_finder_from_cell_jqobj: function(jqobj) { return "Unused"; },
    ignore_text: '',
    negated: true
  },
  { 
    url: 'http://mci.10gen.com/ui/',
    cell_selector: "#content",
    text_finder_from_cell_jqobj: function(jqobj) { return "Unused"; },
    ignore_text: '',
    negated: true
  },
  { 
    url: 'http://mci-motu.10gen.cc:8080/api/',
    cell_selector: "body:contains(api)",
    text_finder_from_cell_jqobj: function(jqobj) { return "Unused"; },
    ignore_text: '',
    negated: true
  },
  { 
    url: 'http://mci.10gen.com/ui/hosts/',
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
    ignore_text: '',
    negated: false
  },
  { 
    url: 'https://github.com/ehershey',
    
    // Date logic to get the full month name and day number of the day that was 23 hours ago,
    // so until 11pm this will return yesterday. This can be shaky logic since most days it shouldn't
    // trigger anyways
    cell_selector: 'div.contrib-streak-current:contains(' + (new Date((new Date()) - 23 * 60 * 60 * 1000)).toFormat("MMMM DD") + '), ' +
                      'div.contrib-streak-current:contains(' + (new Date()).toFormat("MMMM DD") + ')',
    text_finder_from_cell_jqobj: function(jqobj) { return "Date not found in page! (" + (new Date((new Date()) - 23 * 60 * 60 * 1000)).toFormat("MMMM DD") + ')'; },
    ignore_text: '',
    negated: true
  }
];

var errors_found = 0;

async.each(url_configs, check_url, done_checking_all);

function check_url(url_config, done_checking_one) {
  var url = url_config.url;
  var cell_selector = url_config.cell_selector;
  var ignore_text = url_config.ignore_text;
  var negated = url_config.negated;

  var text_finder_from_cell_jqobj = url_config.text_finder_from_cell_jqobj;

  console.log('Starting request for url: ' + url);

  jsdom.env ( url, ["http://code.jquery.com/jquery.js"], function(errors, window) {
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
  });
}

function done_checking_all(err) {
  if(err) throw err;
  console.log('');
  console.log('Total errors found: ' + errors_found);
}



