#!/usr/bin/env node
// Monitor simple URL's for jquery selectors, send email on failures
// 
// To override errors to ignore by detail text, modify 'ignore_text' 
// fields in url_configs objects.
//
//

var jsdom = require('jsdom');
var fs = require('fs');
var nodemailer = require('nodemailer');
var date_utils = require('date-utils');

var MAILTO = 'Ernie Hershey <ernie@mongodb.com>'
var MAILFROM = 'Simple Monitor <ernie@mongodb.com>'
var SUBJECT = 'Simple_monitor alert!'

var nodemailer_transport = nodemailer.createTransport();

// For each object in url_configs, hit "url" and run the "badcell_selector" through jquery. 
// if anything is matched and "negated" is not true (or if nothing matches and "negated" is true), 
// and the detail text (return value of text_finder_from_badcell_jqobj($(badcell_selector)) !== "ignore_text",
// send email from MAILFROM to MAILTO with details on the error
//
//

var url_configs = [ 
  { 
    url: 'http://buildbot.mongodb.org:8081/builders/Windows%2032-bit/builds/-1',
    badcell_selector: "div.success:contains('( 0 secs )')",
    text_finder_from_badcell_jqobj: function(jqobj) { return "Windows 32-bit builder in zombie state"; },
    ignore_text: '',
    negated: false
  },
 
  { 
    url: 'http://downloads-distro.mongodb.org/repo/ubuntu-upstart/dists/dist/10gen/binary-amd64/',
    badcell_selector: "a:contains(deb)",
    text_finder_from_badcell_jqobj: function(jqobj) { return "Unused"; },
    ignore_text: '',
    negated: true
  },
 
  { 
    url: 'http://mci.10gen.com/ui/',
    badcell_selector: "#content",
    text_finder_from_badcell_jqobj: function(jqobj) { return "Unused"; },
    ignore_text: '',
    negated: true
  },
  { 
    url: 'http://mci.10gen.com/ui/',
    badcell_selector: "body:contains(Service Unavailable)",
    text_finder_from_badcell_jqobj: function(jqobj) { return jqobj.text(); },
    ignore_text: '',
    negated: false
  },

  { 
    url: 'http://www.mongodb.org/downloads',
    badcell_selector: ".release-version",
    text_finder_from_badcell_jqobj: function(jqobj) { return "Unused"; },
    ignore_text: '',
    negated: true
  },
  { 
    url: 'http://buildbot.mongodb.org/buildslaves',
    badcell_selector: ".offline",
    text_finder_from_badcell_jqobj: function(jqobj) { return jqobj.parent().children().first().text(); },
    ignore_text: '',
    negated: false
  },
  { 
    url: 'http://buildbot-special.10gen.com/buildslaves',
    badcell_selector: ".offline",
    text_finder_from_badcell_jqobj: function(jqobj) { return jqobj.parent().children().first().text(); },
    ignore_text: '',
    negated: false
  },
  { 
    url: 'https://github.com/ehershey',
    
    // Date logic to get the full month name and day number of the day that was 23 hours ago,
    // so until 11pm this will return yesterday. This can be shaky logic since most days it shouldn't
    // trigger anyways
    badcell_selector: 'div.contrib-streak-current:contains(' + (new Date((new Date()) - 23 * 60 * 60 * 1000)).toFormat("MMMM DD") + '), ' +
                      'div.contrib-streak-current:contains(' + (new Date()).toFormat("MMMM DD") + ')',
    text_finder_from_badcell_jqobj: function(jqobj) { return "Date not found in page! (" + (new Date((new Date()) - 23 * 60 * 60 * 1000)).toFormat("MMMM DD") + ')'; },
    ignore_text: '',
    negated: true
  }
];


url_configs.forEach( function(url_config) { 
  var url = url_config.url;
  var badcell_selector = url_config.badcell_selector;
  var ignore_text = url_config.ignore_text;
  var negated = url_config.negated;

  var text_finder_from_badcell_jqobj = url_config.text_finder_from_badcell_jqobj;

  console.log('checking url: ' + url);

  jsdom.env ( url, ["http://code.jquery.com/jquery.js"], function(errors, window) {
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

      console.log("looking for bad cells with selector: " + badcell_selector);
      var badcells = window.$(badcell_selector);
      var detail_text;

      console.log('found badcells: ' + badcells.length);

      if( ( badcells.length && !negated ) || ( !badcells.length && negated ) ) { 

        detail_text = text_finder_from_badcell_jqobj(badcells);

        if(ignore_text && detail_text === ignore_text) {
          console.log('detail_text === ignore_text; ignoring error (' + detail_text + ')');
        } else {
          console.log('detail_text: ' + detail_text);
          console.log('sending mail');
          nodemailer_transport.sendMail({
              from: MAILFROM,
              to: MAILTO,
              subject: SUBJECT,
              text: 'Error checking URL: ' + url + "\nError detail text: " + detail_text,
              html: '<b>Error checking URL: <a href="' + url + '">' + url + '</a></b><br/>Error detail text: ' + detail_text
          });
        }
      }
    }
  });
})


