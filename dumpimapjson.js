#!/usr/bin/env node
var util = require('util');

var Imap = require('imap');

var since = 'January 01, 2013';
var folder = 'UNSEEN';
//var since = 'January 01, 2012';
//var folder = 'ALL';

var authdata = require('authdata');

var imap = new Imap({
  user: authdata.username,
  password: authdata.password,
  host: 'imap.gmail.com',
  port: 993,
  tls: true,
  tlsOptions: { rejectUnauthorized: false }
});


function show(obj) {
  return util.inspect(obj, false, Infinity);
}

function die(err) {
  process.stderr.write('Uh oh: ' + err + "\n");
  process.exit(1);
}

function openInbox(cb) {
  imap.openBox('INBOX', true, cb);
}

imap.once('ready', function() {
  openInbox(function(err, mailbox) {
    if (err) die(err);
    process.stderr.write('opened inbox\n');
    //imap.search([ folder, ['SINCE', since] ], function(err, results) {
    imap.search([ folder, ['SINCE', 'Dec 20, 2013'] ], function(err, results) {
      if (err) die(err);
      var index = 0;
      var f = imap.fetch(results, { headers: true, bodies: 'HEADER.FIELDS (FROM TO SUBJECT DATE)', struct: true });
      f.on('message', function(msg, seqno) { 
        index++;
        var this_index = index;
        var message_output = {msg: msg, seqno: seqno, index: this_index}; 
        process.stderr.write('.');
        // process.stderr.write('starting message no. ' + this_index + "\n");
        msg.on('body', function(stream, info) {
          var buffer = '';
          stream.on('data', function(chunk) {
            buffer += chunk.toString('utf8');
          });
          stream.once('end', function() {
            // process.stderr.write('buffer: ' + Imap.parseHeader(buffer)); // 'Parsed header: %s', util.inspect(Imap.parseHeader(buffer)));
            message_output.headers = Imap.parseHeader(buffer);
          });
        });
        msg.once('attributes', function(attrs) {
          // console.log(prefix + 'Attributes: %s', inspect(attrs, false, 8));
          message_output.attrs = attrs;
          // process.stderr.write('Headers for no. ' + seqno + ': ' + show(attrs) + "\n");
        });
        msg.once('end', function() {
          // process.stderr.write('ending message no. ' + this_index + "\n");
          process.stderr.write('.');
          process.stdout.write(JSON.stringify(message_output));
          process.stdout.write("\n");
        });
      });
      f.once('error', function(err) {
          if (err) die(err);
      });
      f.once('end',function() {
          process.stderr.write('Done fetching all messages!' + "\n");
          imap.end();
          process.exit();
      });
    });
  });
});
imap.once('error', function(err) {
    process.stderr.write("imap.once error: " + err + "\n");
});

imap.once('end', function() {
    process.stderr.write('Connection ended' + "\n");
});
imap.connect();
