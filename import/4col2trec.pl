#!/usr/bin/env perl

#
# Transform 4 column output to standarf TREC format
#
# Version: 1.0.
#
# Usage: 4col2trec.pl [-v] <input_dir> <save_dir>\n";
#        -v: verbose mode (default: no)
#
# HISTORY
#
# 1.0  original release

use strict;
use POSIX;
use Getopt::Long;

my $script = "4col2trec.pl";
my $usage = "$script [-v] <input_dir> <save_dir>\n";
my $verbose = 0;

GetOptions('verbose!' => \$verbose,
    ) or die $usage;

# allow qrels and runfiles to be compressed with gzip
#@ARGV = map { /.gz$/ ? "gzip -dc $_ |" : $_ } @ARGV;

my $input_dir = shift or die $usage;
my $save_dir = shift or die $usage;

# global variables

# main routine

main();

sub main {
  process();
}

sub process {
  # open the directory of retrieval results generated from students
  opendir(my $dh, $input_dir) or die "Can not opendir `$input_dir': $!\n";
  my @files = grep { !/^\./ && -f "$input_dir/$_" } readdir($dh);
  closedir $dh;
  print @files . " files in total in $input_dir\n";

  my $so_far = 0;
  for my $file (sort {$a cmp $b} @files){
    my $input_ret_file = "$input_dir/$file";
    my $save_ret_file = "$save_dir/$file";
    if(-f $save_ret_file){
      die "$save_ret_file exists!\n";
    }
    my %ret = %{load_4col($input_ret_file)};
    save_trec($save_ret_file, \%ret);
  }
}

sub load_4col {
  my $usage = "Usage: load_4col(\$ret_file)\n";
  my $ret_file = shift;
  
  unless(defined $ret_file){
    die $usage;
  }

  my %ret;
  open RET, $ret_file or die "Can not open `$ret_file': $!\n";
  print "Loading $ret_file\n";

  while(<RET>){
    chomp;
    next if /^$/;

    my($qid, $did, $rank, $score) = split;
    $ret{$qid}{$rank} = $_;
  }

  close RET;
  return \%ret;
}

sub save_trec(){
  my $usage = "Usage: save_trec(\$ret_file, \%ret)";
  my $ret_file = shift;
  my $ret_ref = shift;

  unless(defined $ret_file and defined $ret_ref){
    die $usage;
  }

  my %ret = %{$ret_ref};
  open SAVE, ">" . $ret_file or die "Can not open `$ret_file': $!\n";
  print "Saving $ret_file\n";

  for my $qid(sort {$a<=>$b} keys %ret){
    for my $rank(sort {$a<=>$b} keys %{$ret{$qid}}){
      my $record = $ret{$qid}{$rank};
      my(undef, $did, undef, $score) = split /\t/, $record;
      print SAVE "$qid Q0 $did $rank $score STU\n";
    }
  }

  close SAVE;
}

