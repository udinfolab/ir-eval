#!/usr/bin/env perl

#
# Analyze the qrels (distribution from different pools)
#
# Version: 1.0.
#
# Usage: analyze-qrels.pl [-v] <qrels> <pool>\n";
#        -v: verbose mode (default: no)
#
# HISTORY
#
# 1.0  original release

use strict;
use POSIX;
use Getopt::Long;

my $script = "analyze-qrels.pl";
my $usage = "$script [-v] <qrels> <pool>\n";
my $verbose = 0;

GetOptions('verbose!' => \$verbose,
    ) or die $usage;

# allow qrels and runfiles to be compressed with gzip
#@ARGV = map { /.gz$/ ? "gzip -dc $_ |" : $_ } @ARGV;

my $qrels_file = shift or die $usage;
my $pool_file = shift or die $usage;

# global variables
my %qrels;
my %pool;

# main routine

main();

sub main {
  load_qrels();
  load_pool();
  do_analysis();
}

sub load_qrels {
  open QRELS, $qrels_file or die "Can not open `$qrels_file': $!\n";
  print "Loading $qrels_file\n";

  while(<QRELS>){
    chomp;
    next if /^$/;

    my($qid, undef, $did, $rel) = split;
    #next if $rel <= 0;
    $qrels{$qid}{$did} = $rel;
  }

  close QRELS;
}

sub load_pool {
  open POOL, $pool_file or die "Can not open `$pool_file': $!\n";
  print "Loading $pool_file\n";

  while(<POOL>){
    chomp;
    next if /^$/;

    my($qid, $did, $num) = split;
    #next if $num <= 0;
    $pool{$qid}{$did} = $num;
  }

  close POOL;
}

sub do_analysis {
  my %cum;

  for my $qid(sort {$a<=>$b} keys %qrels){
    $cum{$qid}{total} = scalar keys %{$qrels{$qid}};
    $cum{$qid}{non_rel} = 0;
    $cum{$qid}{rel_1} = 0;
    $cum{$qid}{rel_2} = 0;

    $cum{$qid}{non_rel_pool} = 0;
    $cum{$qid}{rel_1_pool} = 0;
    $cum{$qid}{rel_2_pool} = 0;

    for my $did(keys %{$qrels{$qid}}){
      my $rel = $qrels{$qid}{$did};
      if(0 == $rel){
        $cum{$qid}{non_rel} ++;
        if(defined $pool{$qid}{$did}){
          $cum{$qid}{non_rel_pool} ++;
        }
      }elsif (1 == $rel){
        $cum{$qid}{rel_1} ++;
        if(defined $pool{$qid}{$did}){
          $cum{$qid}{rel_1_pool} ++;
        }
      }elsif (2 == $rel){
        $cum{$qid}{rel_2} ++;
        if(defined $pool{$qid}{$did}){
          $cum{$qid}{rel_2_pool} ++;
        }
      }else{
        die "[Error] Unknown relevance level: $rel\n";
      }
    }
  }

  # output the summary
  my %avg;
  for my $qid(sort {$a<=>$b} keys %cum){
    for my $key(keys %{$cum{$qid}}){
      $avg{$key} += $cum{$qid}{$key};
    }
  }
  my $num_query = scalar keys %cum;
  for my $key(keys %avg){
    printf "%20s\t%.4f\n", $key, $avg{$key} / $num_query;
  }
}

