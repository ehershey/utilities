#!/usr/bin/perl
#
# Rename push task to patchable "realpush" task
# Remove "*" dependencies
# Insert "base_build_id" expansion into each build variant
# Replace ${build_id} in S3 paths with ${base_build_id}
# Replace downloads s3 buckets with test buckets
#
# Usage:
# hack-patch-skip-compile.pl < etc/evergreen.yml > etc/evergreen.yml.new

use warnings;
use strict;

use LWP::Simple qw(get);

my $project = "mongodb-mongo-master";
my $revision = `git merge-base origin/master HEAD`;

chomp($revision);

my $project_underscored = $project;
$project_underscored =~ s/-/_/g;

#
my $build_ids_by_variant_underscored = {};

my $url = "https://evergreen.mongodb.com/version/${project_underscored}_$revision";
#print STDERR "url: $url\n";
my $waterfall_html = get($url);
#print STDERR "waterfall_html: $waterfall_html\n";
foreach my $build_id ($waterfall_html =~ /\bbuild_id"*:"([^"]+)"/g) {
  if($build_id =~ /${project_underscored}_(.*)_${revision}_(.*)/) {
    my $variant_underscored = $1;
    my $timestamp = $2;
    $build_ids_by_variant_underscored->{$variant_underscored} = $build_id;
  }
  else {
    die("Unrecognized build_id pattern: $build_id (doesn't match ${project_underscored}_(.*)_${revision}_(.*))");
  }
}

my $push_task_placeholder='
- name: push
  patchable: false
  depends_on:
  - name: "*"
';

# Track the name of the object being defined in the current line
#
my $current_object_name = "";

# Track the most recent "depends_on" line
#
my $saved_depends_on_line = "";

# Track whether we're in a list of expansion definitions
#
my $in_expansions = 0;

while(<>) {
   s/name: push/name: realpush/g;

   if($saved_depends_on_line) {
    if(/"\*"/) {
      $_ = "$saved_depends_on_line []\n";
    }
    else {
      $_ = "$saved_depends_on_line\n$_"
    }
  }

  if(/patchable:/) {
    next;
  }

  if(/\bdepends_on:\s*$/) {
    chomp();
    $saved_depends_on_line = $_;
    $_="";
  }
  else {
    $saved_depends_on_line = "";
  }
  if(/^\S/) {
    $current_object_name = "";
  }
  if(/^- name: (.*)$/) {
    $current_object_name = $1;
  }
  if(/^tasks:/) {
    $_ = "$_$push_task_placeholder"
  }

  if($in_expansions) {
    # copy indentation from this expansion line and add base_build_id expansion
    #
    my $new_expansion = $_;
    chomp($new_expansion);
    my $variant_underscored = $current_object_name;
    $variant_underscored =~ s/-/_/g;
    my $build_id = $build_ids_by_variant_underscored->{$variant_underscored};
    if(!$build_id) {
      die("Can't find base build id for variant: $current_object_name (underscored: $variant_underscored)");
    }
    $new_expansion =~ s/\S.*/base_build_id: $build_id/;
    $_ = "$new_expansion\n$_";
  }
  if(/expansions:/) {
    $in_expansions = 1;
  }
  else {
    $in_expansions = 0;
  }

  s/\${build_id}/\${base_build_id}/g;
  s/downloads.10gen.com/downloads-test.10gen.com/g;
  s/downloads.mongodb.org/downloads-test.mongodb.org/g;
  print;
}
