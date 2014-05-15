#!/usr/bin/env perl

#
# Merge the retrieval results (TREC format) from multiple runs
# * baselines
# * student submitted retrieval functions
#
# Version: 1.0.
#
# Usage: merge-ret.pl [-v] <bl_dir> <stu_dir> <save>\n";
#        -v: verbose mode (default: no)
#
# HISTORY
#
# 1.0  original release

use strict;
use POSIX;
use Getopt::Long;

my $usage = "merge-ret.pl [-v] <bl_dir> <stu_dir> <save>\n";
my $verbose = 0;
my $rp = 0;

GetOptions('verbose!' => \$verbose,
    ) or die $usage;

# allow qrels and runfiles to be compressed with gzip
#@ARGV = map { /.gz$/ ? "gzip -dc $_ |" : $_ } @ARGV;

my $bl_dir = shift or die $usage;
my $stu_dir = shift or die $usage;
my $save_file = shift or die $usage;

# global statical variables
my $BL_RANK_THRED = 20;
my $STU_RANK_THRED = 5;

# global variables
my %ret;

# main routine

main();

sub main(){
  if(-f $save_file){
    print "$save_file exists!\n";
    return;
  }
  load_bl_ret_list();
  load_stu_ret_list();
  save_merged();
}

sub load_bl_ret_list(){
  # open the directory of retrieval results generated from baselines
  opendir(my $dh, $bl_dir) or die "Can not opendir `$bl_dir': $!\n";
  my @files = grep { !/^\./ && -f "$bl_dir/$_" } readdir($dh);
  closedir $dh;
  print @files . " files in total in $bl_dir\n";

  my $so_far = 0;
  for my $file (sort {$a cmp $b} @files){
    my $ret_file = "$bl_dir/$file";
    load_bl_ret_file($ret_file, $BL_RANK_THRED);
  }
}

sub load_stu_ret_list(){
  # open the directory of retrieval results generated from students
  opendir(my $dh, $stu_dir) or die "Can not opendir `$stu_dir': $!\n";
  my @files = grep { !/^\./ && -f "$stu_dir/$_" } readdir($dh);
  closedir $dh;
  print @files . " files in total in $stu_dir\n";

  my $so_far = 0;
  for my $file (sort {$a cmp $b} @files){
    my $ret_file = "$stu_dir/$file";
    load_stu_ret_file($ret_file, $STU_RANK_THRED);
  }
}

sub load_bl_ret_file(){
  my $usage = "Usage: load_bl_ret_file(\$ret_file, \$thred)\n";
  my $ret_file = shift;
  my $thred = shift;
  
  unless(defined $ret_file and defined $thred){
    die $usage;
  }

  open RET, $ret_file or die "Can not open `$ret_file': $!\n";
  print "Loading $ret_file\n";

  while(<RET>){
    chomp;
    next if /^$/;

    my($qid, undef, $did, $rank, $score, $tag) = split;
    next if $rank > $thred;
    $ret{$qid}{$did} += 1;
  }

  close RET;
}

sub load_stu_ret_file(){
  my $usage = "Usage: load_stu_ret_file(\$ret_file, \$thred)\n";
  my $ret_file = shift;
  my $thred = shift;
  
  unless(defined $ret_file and defined $thred){
    die $usage;
  }

  open RET, $ret_file or die "Can not open `$ret_file': $!\n";
  print "Loading $ret_file\n";

  while(<RET>){
    chomp;
    next if /^$/;

    my($qid, $did, $rank, $score) = split;
    next if $rank > $thred;
    $ret{$qid}{$did} += 1;
  }

  close RET;
}

sub save_merged(){
  open SAVE, ">" . $save_file or die "Can not open `$save_file': $!\n";
  print "Saving $save_file\n";

  for my $qid(sort {$a<=>$b} keys %ret){
    my $num_doc = scalar keys %{$ret{$qid}};
    printf "%d : %d\n", $qid, $num_doc;

    for my $did(sort {$ret{$qid}{$b}<=>$ret{$qid}{$a}} 
      keys %{$ret{$qid}}){
      my $score = $ret{$qid}{$did};
      print SAVE "$qid $did $score\n";
    }
  }

  close SAVE;
}

