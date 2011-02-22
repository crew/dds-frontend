#!/bin/bash
origdir=`pwd`
newdir=`dirname $0`
host=`hostname -f`

cd $newdir
while true
do
logfile=`mktemp`
dds.py &> $logfile
cat $logfile|mail -s "DDS Crash on $host" ddscrashes@compbrain.net
rm $logfile
done
