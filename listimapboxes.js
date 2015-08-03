#!/usr/bin/env node
//
//
// List imap "boxes"
//
// Requires "authdata.js" file exporting username and password fields.
//
//
var SERVER = 'imap.gmail.com';

var util = require('util');

var Imap = require('imap');

var authdata = require('authdata');

var imap = new Imap({
  user: authdata.username,
  password: authdata.password,
  host: SERVER,
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
  // imap.openBox('INBOX', true, cb);
  imap.openBox('All Mail', true, cb);
}


imap.once('ready', function() {
  imap.getBoxes(function(err,boxes) {
    if (err) die(err);
    console.log(boxes);
  });
});
imap.once('error', function(err) {
    process.stderr.write("imap.once error: " + err + "\n");
});

imap.once('end', function() {
    process.stderr.write('Connection ended' + "\n");
});
imap.connect();
