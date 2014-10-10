#!/usr/bin/env node
//
//
// Hit the My Fitness Pal diary page and pull data out of it that isn't available anywhere else. 
// Specifically this includes: 
// Daily total calorie intake
// Daily total macronutrient intake (ideally carbs/fat/protein, but dynamic based on report 
// configuration)
//
// Usage: save_myfitnesspal_data.js [ <start of daterange - YYYY-MM-DD> <end of daterange - YYYY-MM-DD> ] # defauls to date range including yesterday and today
//
// See bottom of file for sample data
var mongodb = require('mongodb');
var jsdom = require('jsdom');
var util = require('util');
var strftime = require('strftime');
var moment = require('moment');

// set database options
//
var dbname = "ernie_org";
var dbserver = "localhost";
var dbport = 27017;

var dbuser = '';
var dbpass = '';

var dboptions = '';


var url = "http://www.myfitnesspal.com/reports/printable_diary/%s?from=%s&to=%s";

var from;
var to;
if(process.argv[2])
{
  from = process.argv[2];
  to = process.argv[3];
}
else
{
  from = moment().subtract(1,'day').format('YYYY-MM-DD');
  to = moment().format('YYYY-MM-DD');
}
username = 'ehershey'

var full_url = util.format(url,username,from,to)
console.log('full_url: ' + full_url);

// process database options
// 

var dbuserpass = '';

if(dbuser && dbpass)
{
  dbuserpass = dbuser + ':' + dbpass + '@';
}

if(dboptions) { 
  dboptions = '?' + dboptions;
}

var dburl = 'mongodb://' + dbuserpass + dbserver + ':' + dbport + '/' + dbname + dboptions;

console.log('dburl: ' + dburl);

var MongoClient = mongodb.MongoClient
  , Server = mongodb.Server;


var summaries_to_save = [];

jsdom.env ( full_url, ["http://code.jquery.com/jquery.js"], function(errors, window) { handler(errors, window); });

function handler(errors, window) 
{
  if(errors) {
    console.log(errors);
    return;
  }
  var calorie_headers = window.$("thead:contains(Calories)");
  calorie_headers.map(function(index,calorie_header) {
    var column_names = [];
    var summary_data = {};
    window.$("td",calorie_header).map(function(index,header_cell) {
      column_names[index] = window.$(header_cell).text();
    });

    var calorie_footer = window.$("tfoot", calorie_header.parentNode);
    console.log('column_names:'); console.log(column_names);
    console.log('calorie_footer.length:'); console.log(calorie_footer.length);
    if(calorie_footer.length !== 1) {
      throw Error("More than one tfoot in thead parent!");
    }
    window.$("td",calorie_footer).map(function(index,footer_cell) {
      summary_data[column_names[index]] = window.$(footer_cell).text();
    });
    console.log('summary_data:'); console.log(summary_data);

    var date = window.$(calorie_header).parent().prev("#date").text();
    // var date = "some day";
    console.log('date: ' + date);
    summary_data.date = date;

    // for exercise summaries, date is ""
    //
    if(date) 
    {
      summaries_to_save[summaries_to_save.length] = summary_data; 
    }
  });
  console.log('summaries_to_save.length: ' + summaries_to_save.length);
  var saved_count = 0;
  MongoClient.connect(dburl, function(err, db) 
  {
    if (err) throw err;
    var collection = db.collection("nutrition_summary");
  
    for(var i = 0 ; i < summaries_to_save.length ; i++) 
    {
      summary_data = summaries_to_save[i];
      date = summary_data['date'];

      collection.update({date: date}, summary_data, {upsert:true, w: 1}, function(err, result) 
      {
        if (err) throw err;
        console.log("saved summary");
        saved_count++;
        if(saved_count == summaries_to_save.length)
        {
          process.exit();
        }
      }); // collection.update
    } // for each summary to save
 
  }); // connect



} // handler()

//
// 
// Sample Data:
// <h2 class="main-title-2" id="date">January 11, 2014</h2>
// <table class="table0" id="food" width="800">
// 	<colgroup>
// 		<col class="col-1">
// 		<col class="col-2">
// 		<col class="col-2">
// 		<col class="col-2">
// 		<col class="col-2">
// 		<col class="col-2">
// 		<col class="col-2">
// 		<col class="col-2">
// 		<col class="col-2">
// 	</colgroup>
// 
// 	<thead>
// 		<tr>
// 			<td class="first">Foods</td>
// 			<td>Calories</td>
// 			<td>Carbs</td>
// 			<td>Fat</td>
// 			<td>Protein</td>
// 			<td>Cholest</td>
// 			<td>Sodium</td>
// 			<td>Sugars</td>
// 			<td class="last">Fiber</td>
// 		</tr>
// 	</thead>
// 	
// 	<tbody>
// 
// 		  <tr class="title">
//   			<td class="first last" colspan="9">Breakfast</td>
//   		</tr>
// 			<tr>
// 				<td class="first">Kashi Go Lean - High Fiber Cereal, 1 cup</td>
// 				<td>160</td>
// 				<td>35g</td>
// 				<td>1g</td>
// 				<td>13g</td>
// 				<td>0mg</td>
// 				<td>90mg</td>
// 				<td>9g</td>
// 				<td class="last">10g</td>
// 			</tr>
// 			<tr>
// 				<td class="first">Silk - Pure Almond - Almond Milk - Original - Unsweetened, 1 cup</td>
// 				<td>40</td>
// 				<td>0g</td>
// 				<td>3g</td>
// 				<td>1g</td>
// 				<td>0mg</td>
// 				<td>160mg</td>
// 				<td>0g</td>
// 				<td class="last">0g</td>
// 			</tr>
// 		  <tr class="title">
//   			<td class="first last" colspan="9">Dinner</td>
//   		</tr>
// 			<tr>
// 				<td class="first">Crown Prince - Kipper Snacks, 1 can (92g)</td>
// 				<td>190</td>
// 				<td>0g</td>
// 				<td>13g</td>
// 				<td>19g</td>
// 				<td>60mg</td>
// 				<td>390mg</td>
// 				<td>0g</td>
// 				<td class="last">0g</td>
// 			</tr>
// 			<tr>
// 				<td class="first">Mixed Green Salad - Field Greens, 1 cup</td>
// 				<td>20</td>
// 				<td>2g</td>
// 				<td>0g</td>
// 				<td>1g</td>
// 				<td>0mg</td>
// 				<td>20mg</td>
// 				<td>1g</td>
// 				<td class="last">1g</td>
// 			</tr>
// 			<tr>
// 				<td class="first">Paul Newman's - Olive Oil and Vinegar, 2 tbls.</td>
// 				<td>150</td>
// 				<td>1g</td>
// 				<td>16g</td>
// 				<td>0g</td>
// 				<td>0mg</td>
// 				<td>150mg</td>
// 				<td>1g</td>
// 				<td class="last">0g</td>
// 			</tr>
// 			<tr>
// 				<td class="first">Typical Mexican Restaurant Order - Chips and Salsa, 1/2 order</td>
// 				<td>200</td>
// 				<td>35g</td>
// 				<td>15g</td>
// 				<td>6g</td>
// 				<td>0mg</td>
// 				<td>300mg</td>
// 				<td>0g</td>
// 				<td class="last">0g</td>
// 			</tr>
// 			<tr>
// 				<td class="first">Kashi Go Lean - High Fiber Cereal, 1 cup</td>
// 				<td>160</td>
// 				<td>35g</td>
// 				<td>1g</td>
// 				<td>13g</td>
// 				<td>0mg</td>
// 				<td>90mg</td>
// 				<td>9g</td>
// 				<td class="last">10g</td>
// 			</tr>
// 			<tr>
// 				<td class="first">Honey, 3 tbsp</td>
// 				<td>192</td>
// 				<td>52g</td>
// 				<td>0g</td>
// 				<td>0g</td>
// 				<td>0mg</td>
// 				<td>3mg</td>
// 				<td>52g</td>
// 				<td class="last">0g</td>
// 			</tr>
// 			<tr>
// 				<td class="first">Fage Total - Total 2% Plain Greek Yogurt, 7 ounces</td>
// 				<td>150</td>
// 				<td>8g</td>
// 				<td>4g</td>
// 				<td>20g</td>
// 				<td>15mg</td>
// 				<td>65mg</td>
// 				<td>9g</td>
// 				<td class="last">0g</td>
// 			</tr>
// 		  <tr class="title">
//   			<td class="first last" colspan="9">Buffer</td>
//   		</tr>
// 			<tr>
// 				<td class="first">Generic - Banana (7" to 7-7/8" Inch), 1 Medium</td>
// 				<td>105</td>
// 				<td>27g</td>
// 				<td>0g</td>
// 				<td>1g</td>
// 				<td>0mg</td>
// 				<td>1mg</td>
// 				<td>14g</td>
// 				<td class="last">3g</td>
// 			</tr>
// 			<tr>
// 				<td class="first">Eggs - Hard-boiled (whole egg), 2 large</td>
// 				<td>155</td>
// 				<td>1g</td>
// 				<td>11g</td>
// 				<td>13g</td>
// 				<td>424mg</td>
// 				<td>124mg</td>
// 				<td>1g</td>
// 				<td class="last">0g</td>
// 			</tr>
// 			<tr>
// 				<td class="first">Quest Bar - Natural Protein Bar - Chocolate Peanut Butter, 1 bar</td>
// 				<td>160</td>
// 				<td>25g</td>
// 				<td>5g</td>
// 				<td>20g</td>
// 				<td>5mg</td>
// 				<td>270mg</td>
// 				<td>1g</td>
// 				<td class="last">17g</td>
// 			</tr>
// 			<tr>
// 				<td class="first">Quest Bar-natural Protein Bar - Strawberry Cheesecake (6g Sugar Alcohols), 1 bar (60g)</td>
// 				<td>160</td>
// 				<td>25g</td>
// 				<td>5g</td>
// 				<td>20g</td>
// 				<td>5mg</td>
// 				<td>105mg</td>
// 				<td>2g</td>
// 				<td class="last">17g</td>
// 			</tr>
// 			<tr>
// 				<td class="first">Fa - Lindt - Lindor - Truffles - Milk Chocolate, 3 balls (36 g)</td>
// 				<td>220</td>
// 				<td>16g</td>
// 				<td>17g</td>
// 				<td>2g</td>
// 				<td>5mg</td>
// 				<td>35mg</td>
// 				<td>14g</td>
// 				<td class="last">1g</td>
// 			</tr>
// 		
// 	</tbody>
// 	
// 	<tfoot>
// 	  <tr>
//   		<td class="first">TOTAL:</td>
//   		<td>2,062</td>
//   		<td>262g</td>
//   		<td>91g</td>
//   		<td>129g</td>
//   		<td>514mg</td>
//   		<td>1,803mg</td>
//   		<td>113g</td>
//   		<td class="last">59g</td>
//   	</tr>
// 	</tfoot>
// 		
// </table>
// <table class="table0" id="excercise">
// 	
// 	<colgroup>
// 		<col class="col-1">
// 		<col class="col-2">
// 		<col class="col-2">
// 		<col class="col-2">
// 		<col class="col-2">
// 		<col class="col-2">
// 	</colgroup>
// 
// 	<thead>
// 		<tr>
// 			<td class="first">Exercises</td>
// 			<td>Calories</td>
// 			<td>Minutes</td>
// 			<td>Sets</td>
// 			<td>Reps</td>
// 			<td class="last">Weight</td>
// 		</tr>
// 	</thead>
// 	
// 	<tbody>
// 	  
//   		<tr class="title">
//   			<td class="first last" colspan="6">Cardiovascular</td>
//   		</tr>
//   		<tr>
//   			<td class="first">Walking, 3.0 mph, mod. pace</td>
//   			<td>21</td>
//   			<td>5</td>
//   			<td class="last" colspan="3">&nbsp;</td>
//   		</tr>
//   		<tr>
//   			<td class="first">Walking, 3.0 mph, mod. pace</td>
//   			<td>50</td>
//   			<td>14</td>
//   			<td class="last" colspan="3">&nbsp;</td>
//   		</tr>
//   		<tr>
//   			<td class="first">Walking, 3.0 mph, mod. pace</td>
//   			<td>121</td>
//   			<td>23</td>
//   			<td class="last" colspan="3">&nbsp;</td>
//   		</tr>
//   		<tr>
//   			<td class="first">Bicycling, &lt;10 mph, leisure (cycling, biking, bike riding)</td>
//   			<td>61</td>
//   			<td>9</td>
//   			<td class="last" colspan="3">&nbsp;</td>
//   		</tr>
//   		<tr>
//   			<td class="first">Bicycling, &lt;10 mph, leisure (cycling, biking, bike riding)</td>
//   			<td>295</td>
//   			<td>41</td>
//   			<td class="last" colspan="3">&nbsp;</td>
//   		</tr>
//   		<tr>
//   			<td class="first">Walking, 3.0 mph, mod. pace</td>
//   			<td>21</td>
//   			<td>5</td>
//   			<td class="last" colspan="3">&nbsp;</td>
//   		</tr>
//   		<tr>
//   			<td class="first">Walking, 3.0 mph, mod. pace</td>
//   			<td>65</td>
//   			<td>7</td>
//   			<td class="last" colspan="3">&nbsp;</td>
//   		</tr>
//   		<tr>
//   			<td class="first">Running (jogging), 6.7 mph (9 min mile)</td>
//   			<td>807</td>
//   			<td>57</td>
//   			<td class="last" colspan="3">&nbsp;</td>
//   		</tr>
//   		<tr>
//   			<td class="first">Walking, 3.0 mph, mod. pace</td>
//   			<td>24</td>
//   			<td>5</td>
//   			<td class="last" colspan="3">&nbsp;</td>
//   		</tr>
//   		<tr>
//   			<td class="first">Bicycling, &lt;10 mph, leisure (cycling, biking, bike riding)</td>
//   			<td>250</td>
//   			<td>32</td>
//   			<td class="last" colspan="3">&nbsp;</td>
//   		</tr>
//   		<tr>
//   			<td class="first">Bicycling, &lt;10 mph, leisure (cycling, biking, bike riding)</td>
//   			<td>376</td>
//   			<td>49</td>
//   			<td class="last" colspan="3">&nbsp;</td>
//   		</tr>
//   		<tr>
//   			<td class="first">Walking, 3.0 mph, mod. pace</td>
//   			<td>23</td>
//   			<td>5</td>
//   			<td class="last" colspan="3">&nbsp;</td>
//   		</tr>
//   		<tr>
//   			<td class="first">Walking, 3.0 mph, mod. pace</td>
//   			<td>52</td>
//   			<td>10</td>
//   			<td class="last" colspan="3">&nbsp;</td>
//   		</tr>
//   		<tr>
//   			<td class="first">Running (jogging), 6 mph (10 min mile)</td>
//   			<td>829</td>
//   			<td>57</td>
//   			<td class="last" colspan="3">&nbsp;</td>
//   		</tr>
//   		<tr>
//   			<td class="first">Running (jogging), 6.7 mph (9 min mile)</td>
//   			<td>879</td>
//   			<td>57</td>
//   			<td class="last" colspan="3">&nbsp;</td>
//   		</tr>
//   	
// 	</tbody>
// 	
// 	<tfoot>
// 		<tr>
//   		<td class="first">TOTALS:</td>
//   		<td>3,874</td>
//   		<td>376</td>
//   		<td>0</td>
//   		<td>0</td>
//   		<td class="last">0</td>
// 		</tr>
// 	</tfoot>
// 	
// </table>


