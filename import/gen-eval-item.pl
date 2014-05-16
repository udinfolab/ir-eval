#!/usr/bin/env perl

#
# Generate the evaluation items to be imported to DB
#
# Version: 1.0.
#
# Usage: gen-eval-item.pl [-v] <ret_dir> <eval> <avg_eval>\n";
#        -v: verbose mode (default: no)
#
# HISTORY
#
# 1.0  original release

use strict;
use POSIX;
use Getopt::Long;

my $script = "gen-eval-item.pl";
my $usage = "$script [-v] <ret_dir> <eval> <avg_eval>\n";
my $verbose = 0;

GetOptions('verbose!' => \$verbose,
    ) or die $usage;

# allow qrels and runfiles to be compressed with gzip
#@ARGV = map { /.gz$/ ? "gzip -dc $_ |" : $_ } @ARGV;

my $ret_dir = shift or die $usage;
my $eval_file = shift or die $usage;
my $avg_eval_file = shift or die $usage;

# global static variables
my $eval_script = "trec_eval -q -m all_trec qrels";

# global variables
my %eval;
my %avg_eval;

# main routine

main();

sub main {
  if(-f $eval_file){
    die "$eval_file exists!\n";
  }
  if(-f $avg_eval_file){
    die "$avg_eval_file exists!\n";
  }

  process();
  save_eval();
  save_avg_eval();
}

sub process {
  # open the directory of retrieval results generated
  opendir(my $dh, $ret_dir) or die "Can not opendir `$ret_dir': $!\n";
  my @files = grep { !/^\./ && -f "$ret_dir/$_" } readdir($dh);
  closedir $dh;
  print @files . " files in total in $ret_dir\n";

  for my $file (sort {$a cmp $b} @files){
    my $ret_file = "$ret_dir/$file";
    do_eval($ret_file, $file);
  }
}

# evaluate the retrieval result
sub do_eval(){
  my $usage = "do_eval(\$ret_file, \$id)\n";
  my $ret_file = shift;
  my $ret_id = shift;

  unless(defined $ret_file and defined $ret_id){
    die $usage;
  }

  printf "[Info] Evaluating %20s\n", $ret_id;

  my $eval_cmd = "$eval_script $ret_file |";
  
  my %res;
  open PIPE, $eval_cmd or die "Can not open `$eval_cmd': $!\n";
  while (<PIPE>) {
    chomp;
    next if /^$/;

    my($key, $qid, $val) = split;
    if("all" ne $qid){
      # for one query
      if("map_cut_5" eq $key){
        $eval{$ret_id}{$qid}{map_cut_5} = $val;
      }elsif("P_5" eq $key){
        $eval{$ret_id}{$qid}{P_5} = $val;
      }elsif("ndcg_cut_5" eq $key){
        $eval{$ret_id}{$qid}{ndcg_cut_5} = $val;
      }
    }else{
      # for all queries, on average
      if("map_cut_5" eq $key){
        $avg_eval{$ret_id}{map_cut_5} = $val;
      }elsif("P_5" eq $key){
        $avg_eval{$ret_id}{P_5} = $val;
      }elsif("ndcg_cut_5" eq $key){
        $avg_eval{$ret_id}{ndcg_cut_5} = $val;
      }
    }
  }
  close PIPE;
}

sub save_eval(){
  open EVAL, ">" . $eval_file 
    or die "Can not open `$eval_file': $!\n";
  print "Saving $eval_file\n";

  for my $ret_id(sort {$a<=>$b} keys %eval){
    for my $qid(sort {$a<=>$b} keys %{$eval{$ret_id}}){
      my $map = $eval{$ret_id}{$qid}{map_cut_5};
      my $p5 = $eval{$ret_id}{$qid}{P_5};
      my $ndcg = $eval{$ret_id}{$qid}{ndcg_cut_5};
      printf EVAL "%s %d %.4f %.4f %.4f\n", $ret_id, $qid, $map, $p5, 
        $ndcg;
    }
  }

  close EVAL;
}

sub save_avg_eval(){
  open AVG_EVAL, ">" . $avg_eval_file 
    or die "Can not open `$avg_eval_file': $!\n";
  print "Saving $avg_eval_file\n";

  for my $ret_id(sort {$a<=>$b} keys %eval){
    my $map = $avg_eval{$ret_id}{map_cut_5};
    my $p5 = $avg_eval{$ret_id}{P_5};
    my $ndcg = $avg_eval{$ret_id}{ndcg_cut_5};
    printf AVG_EVAL "%s %.4f %.4f %.4f\n", $ret_id, $map, $p5, $ndcg;
  }

  close AVG_EVAL;
}

