var system = require("system");
var url = system.args[1];
var filename = system.args[2];
console.log('url: ' + url);
console.log('filename: ' + filename);


var page = require('webpage').create();
page.open(url, function() {
      page.render(filename);
        phantom.exit();
        });
