#!/usr/bin/env perl
use strict;
use warnings;
use IO::Socket::INET;
use IO::Select;

my ($listen_port, $target_host, $target_port, $bind_addr) = @ARGV;
$bind_addr = '127.0.0.1' unless defined $bind_addr;
die "usage: tcp-proxy.pl LISTEN_PORT TARGET_HOST TARGET_PORT [BIND_ADDR]\n"
  unless $listen_port && $target_host && $target_port;

my $server = IO::Socket::INET->new(
  LocalAddr => $bind_addr,
  LocalPort => $listen_port,
  Proto     => 'tcp',
  Listen    => 20,
  ReuseAddr => 1,
) or die "listen failed on $bind_addr:$listen_port: $!\n";

$SIG{CHLD} = 'IGNORE';

while (my $client = $server->accept()) {
  my $pid = fork();
  if (!defined $pid) {
    close $client;
    next;
  }
  if ($pid == 0) {
    close $server;
    my $target = IO::Socket::INET->new(
      PeerHost => $target_host,
      PeerPort => $target_port,
      Proto    => 'tcp',
    );
    exit 1 unless $target;
    $client->autoflush(1);
    $target->autoflush(1);
    my $sel = IO::Select->new($client, $target);
    while (1) {
      my @ready = $sel->can_read(300);
      last unless @ready;
      for my $fh (@ready) {
        my $buf = '';
        my $n = sysread($fh, $buf, 16384);
        exit 0 unless $n;
        my $out = ($fh == $client) ? $target : $client;
        my $off = 0;
        while ($off < length($buf)) {
          my $w = syswrite($out, $buf, length($buf) - $off, $off);
          exit 0 unless $w;
          $off += $w;
        }
      }
    }
    exit 0;
  }
  close $client;
}
