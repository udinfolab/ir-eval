#!/usr/bin/env perl

#
# Estimate the nDCG_O (nDCG based on other users' queries)
#
# Version: 1.0.
#
# Usage: gen-eval-item.pl [-v] <save_avg_eval>\n";
#        -v: verbose mode (default: no)
#
# HISTORY
#
# 1.0  original release

use strict;
use POSIX;
use Getopt::Long;

my $script = "gen-eval-item.pl";
my $usage = "$script [-v] <save_avg_eval>\n";
my $verbose = 0;

GetOptions('verbose!' => \$verbose,
    ) or die $usage;

# allow qrels and runfiles to be compressed with gzip
#@ARGV = map { /.gz$/ ? "gzip -dc $_ |" : $_ } @ARGV;

my $save_avg_eval_file = shift or die $usage;

# global variables
my %query;
my %rf;
my %eval;
my %avg_eval;

# global static variables
my $query_file = 'data/query.list';
my $rf_file = 'data/rf.list';
my $eval_file = 'data/eval.list';
my $avg_eval_file = 'data/avg_eval.list';

# main routine

main();

sub main {
  if(-f $save_avg_eval_file){
    die "$avg_eval_file exists!\n";
  }

  load_query_list();
  load_rf_list();
  load_eval();
  load_avg_eval();
  gen_ndcg_o();
  save_avg_eval();
}

sub load_query_list {
  open QUERY, $query_file 
    or die "Can not open `$query_file': $!\n"; 
  print "Loading $query_file\n";

  while(<QUERY>){
    chomp;
    next if /^$/;
    next if /^#/;

    my($qid, $uid, $query) = split / : /;
    $query{$qid} = $uid;
  }
  close QUERY;
}

sub load_rf_list {
  open RF, $rf_file 
    or die "Can not open `$rf_file': $!\n"; 
  print "Loading $rf_file\n";

  while(<RF>){
    chomp;
    next if /^$/;
    next if /^#/;

    my($id, $uid, $rf_id) = split / : /;
    $rf{$rf_id} = $uid;
  }
  close RF;
}

sub load_eval {
  open EVAL, $eval_file 
    or die "Can not open `$eval_file': $!\n"; 
  print "Loading $eval_file\n";

  while(<EVAL>){
    chomp;
    next if /^$/;
    next if /^#/;

    my($rf_id, $qid, $map, $p5, $ndcg) = split;
    $eval{$rf_id}{$qid}{ndcg} = $ndcg;
  }
  close EVAL;
}

sub load_avg_eval {
  open AVG_EVAL, $avg_eval_file 
    or die "Can not open `$avg_eval_file': $!\n"; 
  print "Loading $avg_eval_file\n";

  while(<AVG_EVAL>){
    chomp;
    next if /^$/;
    next if /^#/;

    my($rf_id, $map, $p5, $ndcg) = split;
    $avg_eval{$rf_id}{map} = $map;
    $avg_eval{$rf_id}{p5} = $p5;
    $avg_eval{$rf_id}{ndcg} = $ndcg;
  }
  close AVG_EVAL;
}

sub gen_ndcg_o {
  my $num_query = scalar keys %query;
  for my $rf_id(keys %avg_eval){
    my $avg_ndcg = $avg_eval{$rf_id}{ndcg};
    my $ndcg_sum = $avg_ndcg * $num_query;

    my $rf_uid = $rf{$rf_id};
    my $num_removed = 0;
    for my $qid(keys %{$eval{$rf_id}}){
      my $q_uid = $query{$qid};
      # if the query is associated with the user of rf, remove the nDCG
      # value from the sum
      if($q_uid == $rf_uid){
        $num_removed += 1;
        my $ndcg = $eval{$rf_id}{$qid}{ndcg};
        $ndcg_sum -= $ndcg;
      }
    }

    my $ndcg_o_avg = $ndcg_sum / ($num_query - $num_removed);
    $avg_eval{$rf_id}{ndcg_o} = $ndcg_o_avg;
  }
}

sub save_avg_eval {
  open AVG_EVAL, ">" . $save_avg_eval_file 
    or die "Can not open `$save_avg_eval_file': $!\n";
  print "Saving $save_avg_eval_file\n";

  for my $rf_id(sort {$a<=>$b} keys %avg_eval){
    my $map = $avg_eval{$rf_id}{map};
    my $p5 = $avg_eval{$rf_id}{p5};
    my $ndcg = $avg_eval{$rf_id}{ndcg};
    my $ndcg_o = $avg_eval{$rf_id}{ndcg_o};
    printf AVG_EVAL "%s %.4f %.4f %.4f %.4f\n", $rf_id, $map, $p5,
      $ndcg, $ndcg_o;
  }

  close AVG_EVAL;
}

