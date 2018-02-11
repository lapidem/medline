#!/bin/bash
### ttenoun.awk
### using TreeTag, extract nouns
~/bin/tte |
awk '
BEGIN{
    nWord = 0
    maxLen = 0
}
    $2 ~ /^[N]/ {
    verb[$3]++
    verbRaw[$1]++
    inf[$1] = $3
    nWord++
    if (length($1) > maxLen) {maxLen = length($1)}
}
END{
    format = "%-"maxLen"s\t%.1f\t%.1d%% of %s\n"
    print(format)
    for (k in verbRaw){
        infinitive = inf[k]
        freq = verbRaw[k]*10000/nWord
        rate=verbRaw[k]*100/verb[infinitive]
        printf(format, k, freq, rate, infinitive)

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

