#!/bin/sh
# https://politics.ld.admin.ch/political-rights/referendum/typ/NUMBER # returns sometimes a referendum type. Gotta catch them all !
echo "Until which number you want to check?"
read number

i=0
while [ "$i" -le "$number" ]
do
  curl "https://politics.ld.admin.ch/political-rights/referendum/typ/$i"
  i=$((i + 1))
done
