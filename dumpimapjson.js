#!/usr/bin/env node
var util = require('util');

var Imap = require('imap');

var since = 'January 01, 2001';
var folder = 'UNSEEN';
//var since = 'January 01, 2012';
//var folder = 'ALL';

var authdata = require('authdata');

  var imap = new Imap({
        user: authdata.username,
        password: authdata.password,
        host: 'imap.gmail.com',
        port: 993,
        secure: true
      });

 function show(obj) {
    return util.inspect(obj, false, Infinity);
  }

  function die(err) {
    process.stderr.write('Uh oh: ' + err + "\n");
    process.exit(1);
  }

  function openInbox(cb) {
    imap.connect(function(err) {
      if (err) die(err);
      imap.openBox('INBOX', true, cb);
    });
  }

  openInbox(function(err, mailbox) {
    if (err) die(err);
    imap.search([ folder, ['SINCE', since] ], function(err, results) {
      if (err) die(err);
      imap.fetch(results,
        //{ headers: ['from', 'to', 'subject', 'date'],
        { headers: true,
          cb: function(fetch) {
            var index = 0;
            fetch.on('message', function(msg) {
              index++;
              process.stderr.write('.');
              // process.stderr.write('starting message no. ' + index + "\n");
              msg.on('headers', function(hdrs) {
                process.stdout.write(JSON.stringify({ msg: msg, sequenceNo: msg.seqno, headers: hdrs}) + "\n");
                // process.stderr.write('Headers for no. ' + msg.seqno + ': ' + show(hdrs) + "\n");
              });
              msg.on('end', function() {
                //process.stderr.write('ending message no. ' + index + "\n");
              });
            });
          }
        }, function(err) {
          if (err) throw err;
          process.stderr.write('Done fetching all messages!' + "\n");
          imap.logout();
        }
      );
    });
  });
