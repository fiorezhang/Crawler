// a phantomjs example
var page = require('webpage').create();
phantom.outputEncoding="gbk";
//page.open("http://www.cnblogs.com/front-Thinking", function(status) {
page.open("https://www.8muses.com/comics/picture/Various-Authors/NLT-Media/A-Sunday-Schooling/2", function(status) {
    if ( status === "success" ) {
       console.log(page.title); 
       page.render("front-Thinking.png");
    } else {
       console.log("Page failed to load."); 
    }
    phantom.exit(0);
 });