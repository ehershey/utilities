#!/usr/bin/env perl
#
#
# Take gps log data exported via:
# mysqldump ernie_org gps_log --tab=gps_log --fields-terminated-by="," --fields-enclosed-by="\"" --lines-terminated-by="\r\n"
#
# Import it into mongodb to look like: 
# {
#   _id: blah,
#   loc : { type : "Point" ,
#         coordinates : [ 40, 5 ]
#   },
#   last_update: ISODate("2013-12-30T11:43:36.362Z"),
#   entry_date: ISODate("2013-12-30T11:43:36.362Z"),
#   entry_source: "movesapp",
#   accuracy: null
# }
#
#
# SQL table columns are:
# entry_id, last_update, entry_date, longitude, latitude, entry_source, accuracy
#
# Data looks like:
# "20","2006-06-27 05:00:32","2006-06-27 05:00:32","-73.99283599853515600000","40.76315689086914100000",\N,\N
#
#
#
# To improve upon simplistic import:
#
# mongoimport  --drop --fields original_id,last_update,entry_date,longitude,latitude,entry_source,accuracy --type csv --db test --collection gps_log < ~/gps_log.txt
#
# Usage: 
# 
# gps_log_csv_to_json.sh  < gps_log.txt | mongoimport --db ernie_org --collection locations

use Data::Dumper;
use Text::CSV;

my @rows;
my $csv = Text::CSV->new ()
or die "Cannot use CSV: ".Text::CSV->error_diag ();

my $fh = \*STDIN;
while ( my $row = $csv->getline( $fh ) ) {
  push @rows, $row;
}
$csv->eof or $csv->error_diag();
close $fh;

$csv->eol ("\r\n");

print "row count: " . scalar(@rows) . "\n";
print Dumper \@rows;
