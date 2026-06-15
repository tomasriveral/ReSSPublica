#!/bin/sh
# https://politics.ld.admin.ch/political-rights/referendum/typ/NUMBER # returns sometimes a referendum type. Gotta catch them all !
echo "Until which number you want to check?"
read number
for i {0...number}
do
  curl "https://politics.ld.admin.ch/political-rights/referendum/typ/$i"
done
