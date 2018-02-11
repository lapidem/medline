#!/bin/bash
### make sorted dictionary from tte tags raw data
# word  POStag infinitive count
# dictionary words = {word\tPOStag\tinfinitive: count}

~/bin/tte |
awk '
BEGIN{
    nWord = 0
    maxLen = 0
}
$1 !~ /^[0-9\-\:]+$/
{
    if( $3 !~ /\<unknown\>/ && $2 !~ /CD/){
        words[$0]++
    }
}
END{
    format = "%s\t%d\n"
    for (k in words){
        if( words[k] > 0 ){
            printf(format, k, words[k])
        }
    }
}'|
sort -nr -k4


