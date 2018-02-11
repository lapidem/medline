#!/bin/bash
# tag2rank.awk POS
# noun 		N
# adjective 	JJ
# adverb	RB
# verb		VB

awk '
BEGIN{
    nWord = 0
    maxLen = 0
}
    $2 ~ /^ARGV[1]/ {
    adj[$1]++
    nWord++
    if (length($1) > maxLen) {maxLen = length($1)}
}
END{
#    format = "%-"maxLen"s\t%.1d\t%.1f\n"
    format = "%-20s\t%.1d\t%.1f\n"
    print(format)
    for (k in adj){
	if( adj[k] > 1 ){ 
	        freq = adj[k]*10000/nWord
       		printf(format, k, adj[k], freq )
	}
    }
}'|
sort -nr -k2|
awk '
BEGIN {
    count = 0
}
{
    count++
    printf("%5d)%s\n",count,$0)
}
'

