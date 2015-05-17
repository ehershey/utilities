#!/usr/bin/env node
// Given a JIRA-exported XLS file, move a "Description" column in the last column
// to its own row

var jsdom = require('jsdom');
var fs = require('fs');

jsdom.env ( "/dev/stdin", ["http://code.jquery.com/jquery.js"], function(errors, window) {
  var td;
  var tds = window.document.getElementsByTagName('td');
  for(var i = 0 ; i < tds.length ; i++) {
    td = tds[i];
    check_adjust_cell(window,td);
  }

  var th;
  var ths = window.document.getElementsByTagName('th');
  for(var i = 0 ; i < ths.length ; i++) {
    th = ths[i];
    check_adjust_cell(window,th);
  }

  console.log(window.document.innerHTML);
});


// check if a cell is a header or normal table cell for a jira ticket description.
// If so, move it one row down
//
function check_adjust_cell(window,cell) {
  if(cell.className.match("description")) {
    var original_parent = cell.parentNode;
    var column_count = original_parent.getElementsByTagName("td").length + original_parent.getElementsByTagName("th").length - 1;
      cell.colSpan = column_count;
    var new_tr = window.document.createElement('tr');
    new_tr.appendChild(cell);
    if(original_parent.nextSibling) {
      original_parent.parentNode.insertBefore(new_tr,original_parent.nextSibling);
    } else {
      original_parent.parentNode.appendChild(new_tr);
    }
  }
  else
  {
  }
}
