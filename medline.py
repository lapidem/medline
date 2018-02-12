#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
rev2
read *.txt 
menu: info, save, load, quit
rev3
color enhancement, optional limit
 bugfix: o)コマンドで重複, 3.2: command関数, 3.3: shortcut command
 3.4: associated words list, 3.5 history, 3.6 significantly associated words, 3.7 neural net search(単語の出現頻度算出）, 3.8 history stored, menu improved (.digit shortcut), 3.9 関数化　dispVocaDistr
3.10 loadでbaseVocaを計算しないバグをfix, .medline shelveに格納, 3.11 enhance, layerMatch
 rev4
 associated wordsによりmultiple search( layer1サーチ）
4.1: layerKeywordバグフィックス, 4.2 tooLongで長すぎる文を除外、layer1でのキーワードは' ' でwrapping
4.2: TreeTagger 4.3: verb  4.4 verb rank 4.5 adverb 4.6 load() at startup
4.7: getRank, 4.8: getPOS 4.9: adjective 4.10: multiple search, 4.11: capitalize keywords, 
4.12: associated keyword shortcut search, 4.13 num shortcut bug fix
4.14 regExCharを第一文字にするとhungするbugfix, 4.15 more page for multiple search
4.16 help追加、数字出力整形 4.17 clipboardへのコピー 4.18 kwic 
4.19 medlineでAB tagが存在しないレコードがあり、バグフィックス 
4.20 associated kywordsに正規表現文字が入るとhungするbugfix
4.21 flag(), toggle(), copy2Clipboard(), dispConBuf(), dispController()
4.22 dispController() enriched 
4.23 bug fix, abstractsからの改行を取り除く正規表現変更：行末が丁度\nの場合を考慮
    kwic表示変更時のdeltaがdispControllerで一部反映されていなかった。
To Do 

*********** neural network of words の構造
{'wrd1' : {'aw1' : n1, 'aw2' : n2, ...}, 'wrd2': {'aw1' : n2, ..}, ...}
あるいは
{   wrd1:                wrd2: ,            ...}
  { aw1-1:n1-1,    { aw2-1, n2-1,
   aw1-2:n1-1,      aw2-2: n2-2,
     ...                   ...
   aw1-?:n-1-?}     aw2-?: n2-?}

*********** kwic (keyword in context)
    keywordの位置positionを求める: index = line.find(keyword)
    語の前の文字列sPKeyを切り出し、文字数nPCharを求める
        nPCharがnLLenより長ければ、後ろnLLenを切り出す。
        短かければ、スペースで埋める(足りない分のスペース+sPKey)k
    語の前の文字列sPKeyTを求める
    語の後の文字列sAKeyについても同様の処理をしてsAKeyTを求める
    line = sPKeyT + enhance(keyword) + aAKeyT　を辞書に格納する。
    lineをsAKeyTでソート

*********** medlineTTE.lst 作成方法
cd pubmed/
cat *.txt | ./tteraw.awk > medlineTTE.lst
"""
revision = 'rev4.23'

import glob
import os
import re
import shelve
import pyperclip
#import readchar
#import treetaggerwrapper as ttw
###W TreeTagger
#tagger = ttw.TreeTagger(TAGLANG='en', TAGDIR='/Users/sirasawa/Linux/tt/')
# now incorporate trained data list instead of using TT in the code
# trained by tteverb.awk

pubmedDir ='/pubmed/'     #home dirからの相対path, ~/pubmed/を想定
####  global
files = []
pubmed = {}
docn = []
overlapped = 0
baseVoca = {} #全体のvocabulary
history = []
aWordArray = []
conBuf = [] #console buffer
conBufSort = [] 
## ttdic structure
## word \t POS \t infinitive \ count
## trained by tteraw.awk in pubmed folder from medline.txt data as stdin
## cat medline_format.txt | tteraw.awk >medlineTTE.lst
ttdic = [] #Tree Tag 
verb = {}
verbRaw = {}
adverb = {}
adjective = {}
adverbRank = {}
verbRawRank = {}
adjectiveRank = {}

#### constants
tagPattern = r'([A-Z]+)\s*\-s*'
contPattern = r'\s+([^\s].*$)'
titleTagPattern = r'^TI\s*\-s*'
oTagPattern = r'^OT\s+\-\s*([\w ]+)\n*'
regExChar = ['+', '*', '(', ')', '{', '}', '[', ']', '?', '<', '>']

def openMedline():
    #get medline txt files
    #Medline processing
    # version 3.0 function
    # version 2.0
    # pubmed was changed as dictionary
    #version 1.0
    #make arrays of Title, Abstract, and dictionary of keywords
    # generate 2 databases
    #            array abstracts for sentence database
    #            array pubmed for abstract database

    global files
    global overlapped
    global pubmed
    global docn
    global ttdic

    tagStr = ""
    recordN = 0
    abstracts = []
    journal = ''
    publish = ''
    tit = ""
    abst = ""
    id = ''
    pubmed = {}

    homeDir = os.environ['HOME']
    medlineTxt = homeDir+pubmedDir+'*.txt'
    print(medlineTxt)
    files =glob.glob(medlineTxt)

    #open medline txt files
    medline = []
    for fName in files:
        print("reading", fName, end='')
        f = open(fName)
        lines = f.readlines()
        f.close()
        print( ':',  len(lines), "lines")
        medline += lines
    
    #load Trained Tree Tag dic
    loadTtdic()

    print("processing medline format", end='')

    for line in range(len(medline)):
        m = re.match(tagPattern, medline[line])
        lineStr = medline[line]
        if m:
            tagStr = m.group(1)
            if tagStr == 'PMID':
                #store new record and reset
                if id in pubmed.keys():
                        #skip
                    overlapped += 1
                else:
                    if not id == '':
#                        data = tit+journal+publish+' PMID:'+id+abst
                        data = tit+journal+publish
                        abstracts.append(abst)
                        abst = ''  #bug fixed: ABの存在しないdataが多数あった。
                        pubmed[id] = data
                        recordN += 1
                        if recordN % 1000 == 0:
                            print('.', end='')
                #reset
                id = re.sub(tagPattern, '',  lineStr)
            if tagStr == 'JT': #Journal
                journal = re.sub(tagPattern, '', lineStr)[:-1]
            if tagStr == 'DP': #Date of Publishing?
                publish = re.sub(tagPattern, '', lineStr[:-1])
            if tagStr == 'TI':
                tit = re.sub(titleTagPattern, '', lineStr)
            if tagStr == 'AB': #new record
                lineStr = re.sub(tagPattern, '', lineStr)
                abst = lineStr
        else: #tag なし
            m = re.match(contPattern, medline[line])
            if m:
                lineStr = m.group(1) + ' '
                if tagStr == 'AB':
                    abst += lineStr
                if tagStr == 'TI':
                    tit += lineStr
            else:
                lineStr = medline[line]

    #docn: doc(abstractsのコピー)をsentenceに分割
    # \n\sを ' 'に置き換える
    docn = []
    for i in range(len(abstracts)):
        if abstracts[i] == '':    # AB無しレコード対策
            continue
#        abstracts[i] = re.sub(r'\n\s+', ' ', abstracts[i])    #rev4.22 
        abstracts[i] = re.sub(r'\n\s*', ' ', abstracts[i])
        lines = abstracts[i].split('. ')
        #'.'でsplitした時に、abstractの最後が'.\n'であるため、linesの最後の要素は空行となる
        for lineN in range(len(lines)-1):
            docn.append(lines[lineN] + '.')
            #全体の単語辞書
            words = lines[lineN].split()
            for wrd in range(len(words)):
                if words[wrd] in baseVoca.keys():
                    baseVoca[words[wrd]]  += 1
                else:
                    baseVoca[words[wrd]] = 1
    print()
    save()
    #### end of openMedline()
    
def ttdicMessage():
    global ttdic
    global verb
    global verbRaw
    
    if len(ttdic) >0:
        print( "{:,d} words Trained TTag dic loaded. ".format( len(ttdic)))
    if len(adverb) >0:
        print("{:,d} adverbs, ".format(len(adverb)), end="")
        print("{:,d} adverb ranks, ".format(len(adverbRank)), end="")
    if len(adjective) >0:
        print("{:,d} adjective, ".format(len(adjective)), end="")
        print("{:,d} adjective ranks, ".format(len(adjectiveRank)), end="")
    if len(verb) >0:
        print( "{:,d} verbs, ".format(len(verb)), end="")
        print( "{:,d} verb ranks, ".format(len(verbRawRank)), end="")
        print( "{:,d} raw verbs, trained dictionary loaded.".format(len(verbRaw)))

    
def loadTtdic():
    global ttdic

    # open TreeTag data
    print("loading Trained Tree Tag  dictionary...")
    homeDir = os.environ['HOME']
    TTdic = homeDir + '/py/pubmed/medlineTTE.lst'
    f = open(TTdic)
    ttdic = f.readlines()
    f.close()

    ttVerb()
    ttAdverb()
    ttAdjective()
    ttdicMessage()

## ttdic structure
## word \t POS \t infinitive \ count
##   0       1          2            3
def ttVerb():
    global ttdic
    global verb
    global verbRaw
    global verbRawRank

 #   verb = {}
    if len(ttdic) >0:
        print("making trained verb dictionary...")
#        for i in range(len(ttdic)):
#            tagArray = ttdic[i].split()
#            if len(tagArray) > 3:    #countが存在しないレコードを捨てる
#                if tagArray[1][0] == 'V':
#                #verb 原形(infinitive)
#                    if tagArray[2] in verb.keys():
#                        verb[tagArray[2]] += int(tagArray[3])
#                    else:
#                        verb[tagArray[2]] = int(tagArray[3])
#                #verbRaw 単語そのもの
#                    if tagArray[0] in verbRaw.keys():
#                        verbRaw[tagArray[0]] = int(tagArray[3])
#                    else:
#                        verbRaw[tagArray[0]] = int(tagArray[3])
        verb = {}
        verb = getPOS(verb, 'V', 2)
        verbRaw = {}
        verbRaw = getPOS(verbRaw, 'V', 0)
        verbRawRank = getRank(verbRaw)
#        count = 0
#        for k,v in sorted(verbRaw.items(), key=lambda x:-x [1]):
#            count += 1
#            verbRawRank[k] = count
    else:
        print("ttdic is not loaded.")

## ttdic structure
## word \t POS \t infinitive \ count
##   0       1          2            3
def ttAdverb():
    global ttdic
    global adverb
    global adverbRank

    if len(ttdic) >0:
        print("making trained adverb dictionary...")
        adverb = {}
        adverb = getPOS(adverb, 'RB', 2)
        adverbRank = getRank(adverb)
    else:
        print("ttdic is not loaded.")

def ttAdjective():
    global ttdic
    global adjective
    global adjectiveRank

    if len(ttdic) >0:
        print("making trained adjective dictionary...")
        adjective = {}
        adjective = getPOS(adjective, 'JJ', 0)
        adjectiveRank = getRank(adjective)
    else:
        print("ttdic is not loaded.")

''' get dictionary of POS
ttdicから品詞毎の辞書を作る
## ttdic structure
## word \t POS \t infinitive \ count
##   0       1          2            3
col=0: raw, col=2:infinitive
例）
副詞        getPOS(dic, 'RB', 0)
副詞raw   getPOS(dic, 'RB', 2)
形容詞　　　　　　getPOS(dic, 'JJ', 0)
動詞　　　　　　　　　　　　　getPOS(dic, 'V', 0)
動詞原型     getPOS(dic, 'V', 2)
'''
def getPOS(dic, POS, raw):
    global ttdic

    col = raw
    for i in range(len(ttdic)):
        tagArray = ttdic[i].split()
        if len(tagArray) > 3:
#            if tagArray[1][:2] == POS:
            m = re.match(POS, tagArray[1])
            if m:
                if tagArray[col] in dic.keys():
                    dic[tagArray[col]] += int(tagArray[3])
                else:
                    dic[tagArray[col]] = int(tagArray[3])
    return dic


''' make rank
dic={word: count} -> dicRank= {word: rank}
一番countの多いものから1, 2, 3とランク付けをする
dicRank = getRank(dic)
'''
def getRank(dic):
    rank = {}
    count = 0
    for k,v in sorted(dic.items(), key=lambda x:-x [1]):
            count += 1
            rank[k] = count    
    return rank

def saveEnv():
    global history
    global verb
    global verbRaw
    global adverb
    global adjective
    global verbRawRank
    global adverbRank
    global adjectiveRank

    print('saving trained TTag dictionary ...')
    if len(history) > 100:
        del history[100:]
    shelfFile = shelve.open('.medline')
    shelfFile['history'] = history
    shelfFile['verb'] = verb
    shelfFile['verbRaw'] = verbRaw
    shelfFile['adverb'] = adverb
    shelfFile['adjective'] = adjective
    shelfFile['verbRawRank'] = verbRawRank
    shelfFile['adverbRank'] = adverbRank
    shelfFile['adjectiveRank'] = adjectiveRank
    shelfFile.close

def loadEnv():
    global history
    global verb
    global verbRaw
    global adverb
    global adjective
    global verbRawRank
    global adverbRank
    global adjectiveRank

    print("loading trained TTag dictionary ...")
    shelfFile = shelve.open('.medline')
    if 'history' in shelfFile.keys():
        history = shelfFile['history'] 
    if 'verb' in shelfFile.keys():
        verb = shelfFile['verb']
    if 'verbRaw' in shelfFile.keys():
        verbRaw = shelfFile['verbRaw']
    if 'adverb' in shelfFile.keys():
        adverb = shelfFile['adverb']
    if 'adjective' in shelfFile.keys():
        adjective = shelfFile['adjective']
    if 'verbRawRank' in shelfFile.keys():
        verbRawRank = shelfFile['verbRawRank']
    if 'adverbRank' in shelfFile.keys():
        adverbRank = shelfFile['adverbRank']
    if 'adjectiveRank' in shelfFile.keys():
        adjectiveRank = shelfFile['adjectiveRank']
    shelfFile.close

def chop(str):
    return re.sub(r'\s+$', '', str)

def save():
    global files
    global docn
    global pubmed
    global baseVoca
#    global ttdic

    #write()を使った場合には、'\n'を追加する必要あり。
    file = open('.medline.txt', 'w')
    print('saving medline db ...')
    for i in range(len(docn)):
        file.write(docn[i]+'\n')
    file.close
    print('saving trained medline dictionary ...')
    shelfFile = shelve.open('.medline')
    shelfFile['files'] = files
    shelfFile['pubmed'] = pubmed
    shelfFile['baseVoca'] = baseVoca
    shelfFile.close

def load():
    #write + \nで書き出したものをreadlineで読み取り、改行を落とす。
    global docn
    global files
    global pubmed
    global baseVoca
#    global ttdic

    try:
        docn = []
        file =open('.medline.txt', 'r')
        if file:
            line = file.readline()
            print('loading medline db ...')
            while line:
                line= chop(line)
                docn.append(line)
                line = file.readline()
        file.close
    except:
        print('.medline.txt not fournd')
    #load Trained Tree Tag dictionary
    # loadEnvで品詞別辞書を読み込んでいるため、ttdicの再読込の必要はない
#    loadTtdic()
    #load environment data
    print('loading trained dictionary of medline ...')
    shelfFile = shelve.open('.medline')
    if 'baseVoca' in shelfFile.keys():
        baseVoca = shelfFile['baseVoca']
    if 'files' in shelfFile.keys():
        files = shelfFile['files']
    if 'pubmed' in shelfFile.keys():
        pubmed = shelfFile['pubmed']
    shelfFile.close()

def colorSelection():
    global color
    menuList = {'e': 'e)nhance', 'r': 'r)ed', 'g': 'g)reen', 'y': 'y)ellow', 'b': 'b)lue', 'm': 'm)agenta', 'c': 'c)yan'}
    for i in menuList:
        print('\t', end='')
        print(menuList[i])
    res = input('color>>>')
    if res == 'e':
        color = 'enhance'
    elif res == 'r':
        color = 'red'
    elif res == 'g':
        color = 'green'
    elif res == 'y':
        color = 'yellow'
    elif res == 'b':
        color = 'blue'
    elif res == 'm':
        color = 'magenta'
    elif res == 'c':
        color = 'cyan'
        
def numberSelection():
    global limit
    print('current limit to show:', limit)
    number = input('limit to show >>>')
    if number.isdigit():
        num = int(number)
        if num >0:
            limit = num

def info():
    global files
    if len(files) > 0:
        print("loaded database: ")
        for fNames in files:
            print(fNames, ', ')
    ttdicMessage()
    usage()

def usage():
    print( """ ********** Eliza HELP *************
Eliza does DEEP NEURAL NET SEARCH of words in Medline db.
Eliza already knows the words and the frequencies of their use.
MENU: . for invoking menu
Separating keywords with ':' makes Eliza report MULTIPLE searches
instead of DEEP NEURAL NET SEARCH.
DO NOT include  [+, *, (, ), {, }, [, ], ?, <, >] in keywords.
TIPs: one keyword followd by ':' makes the search SIMPLE SEARCH.
SHORTCUTS: 
the NUMBER of 'words associated' invokes the keywords.
e.g.) 1:2 invokes MULTIPLE SEARCH with 1st and 2nd keywords.
']'+ NUMBER allows Eliza copy the line to the clipboard.
'.h' for history, '.number' for invoking (number)history directly
    e.g.) '.0' for previous search
'.k' for KWIC toggle, defaut ON
'.r'+keyword for REGULAR EXPRESSION for experts
    example: '.rThis.+study' matches 'This is the first study', etc.
'.v', '.a', '.j' for invoking lists of verb, adverb, adjective, respectively.
'.o' for open and intake the Medline.txt databases in "pumed folder".
'.l' for load data, manually.
'.s' save data, manually.
'.q' for quit
Eliza makes '~/.medline.db' and '~/.medline.txt'
********** Have a fun! *************""")

def command(cmd):
        if cmd in ['i', 'I']:
            preMessage()
            info()
        elif cmd in ['c', 'C']:
            colorSelection()
        elif cmd in ['h', 'H']:
            return getHistory()
        elif cmd in ['v', 'V']:
            return getVerb()
        elif cmd in ['a', 'A']:
            return getAdverb()
        elif cmd in ['j', 'J']:
            return getAdjective()
        elif cmd in ['n', 'N']:
            numberSelection()
        elif cmd in ['o', 'O']:
            openMedline()
            preMessage()
        elif cmd in ['l', 'L']:
            load()
            preMessage()
        elif cmd in ['s', 'S' ]:
            save()
            preMessage()
        elif cmd in ['r', 'R', '' ]:
            return 'return'
        elif cmd in ['q', 'Q' ]:
            return 'quit'

def menu():
    menuList = {'i': '\tI)nfo', 'c': 'C)olor', 'h': '\tH)istory', 'v': '\tV)erb list', 'a': '\tA)dverb list','j': '\tJ)adJective list','n': '\tN)umber shown', 'o': '\tO)pen Medline text data', 'l': '\tL)oad saved db', 's': '\tS)ave db', 'r': '\tR)eturn', 'q': '\tQ)uit' }
    while True:
        for i in menuList:
            if i == 'c':
                print('\t', end='')
                print(colorS[color], end='')
                print(menuList[i])
                print(enhanceE, end='')
            elif i == 'n':
                print(menuList[i], ': ', limit)
            else:
                print(menuList[i])
        cmd = input('menu>>>')
        res = command(cmd)
        if cmd in ['h', 'H', 'v', 'V', 'a', 'A']:
             return res
        if res in [ 'quit']:
            return res
        return '.'

def preMessage():
    print("I have learned {:,d} medline data,".format( len(pubmed)),  "{:,d} sentences,".format(len(docn)), "{:,d} words.".format(len(baseVoca)), "{:,d} overlapped.".format(overlapped))
    print("Eliza console verison medline.py", revision, "(c) sirasawa")

'''
## readkey
## 未使用 import readcharは必要ない
def readkeyboard():
    str = ''
    while True:
        c = readchar.readchar()
        print(c, end='')
        if (c == '\r'):
            break
        str += c
    return str
'''

def dispHistory(hLimit=10):
    global history
    print(enhance('history:'), end='')
    for i in range(len(history)):
        print( ' (' + str(i) + ')' + history[i], end='')
        if i > hLimit:
            break
    print()
    
def getHistory():
    global history
    hLimit = 10
    dispHistory(hLimit)
    res = input('select number: ')
    if res.isdigit():
        if int(res) in range(len(history)):
            return history[int(res)]
        else:
             return ''
    else:
        return ''

def dispDicRank(dic):
    nDisp = limit * 10
    nBegin = 0
    nEnd = nBegin + nDisp
    length = 0
 
    while True:
        count = 0
        command={}
        for k,v in sorted(dic.items(), key=lambda x:-x[1]):
            count += 1 
            if count < nBegin:
                continue
            elif count > nEnd:
                break
            command[str(count)]=k
            item ='('+str(count)+')'+ enhance(k)+ '\t'
            length += len(item)
            if length >80:
                length = 0
                print()
            print( item  , end='')
        print()
        cmd = input("(<-:p n:->)select number:")
        if cmd == 'p': 
            nBegin -= nDisp
            nEnd -= nDisp
            if nBegin <0 :
                nBegin = 0
                nEnd = nDisp
        elif cmd == 'n':
            nBegin += nDisp
            nEnd += nDisp
        elif cmd == '':
            return ''
        else:
            if cmd in command.keys():
                return command[cmd]

def getVerb():
    global verbRaw
    global verb

    return dispDicRank(verbRaw)
    
def getAdverb():
    global adverb
    return dispDicRank(adverb)
    
def getAdjective():
    global adjective
    return dispDicRank(adjective)
   
def dispVocaDistr(vocaDistr):
    #### 　有意に頻度の高い単語を表示(vocaDistrの降順表示：poissonまで）
    #### constants: poisson
    #### globals: aWordArray
    #### locals: vocaDistr
    global aWordArray
    count=0
    aWordArray = []
    for k, v in sorted(vocaDistr.items(), key=lambda x:-x[1]):
        count +=1
        aWordArray.append(k)
        print(enhance(str(count)+')'), end='')
        print(enhance(k), end = '')
        print (getWordRank(k), end='')
        print("({0:.4})".format(v), end='')
        if v < poisson:
            break

def getWordRank(keyword):
    global verbRawRank
    global adverbRank
    global adjectiveRank
    if keyword in verbRawRank.keys():
        rank = '[v' + str(verbRawRank[keyword]) + ']'
    elif keyword in adverbRank.keys():
        rank = '[av' + str(adverbRank[keyword]) + ']'
    elif keyword in adjectiveRank.keys():
        rank = '[aj' + str(adjectiveRank[keyword]) + ']'
    else:
        rank = ''
    return rank

######## multiple search (layer search) 実装 <=未実装。　sarchMatchで実装なので使わない？
    #### layerKeyword[layer][index] : 各layerのkeyword, layer=0は、docnであり、keywordは''とする。
    #### layerCount[layer][index]: 各layerのindexed keywordによるmatch数配列
    #### layerMatch[layer=i+1][index][] = findMatch(layerMatch[layer=i][index][])　
    ####       ：各layerでindexed keywordにマッチした文の配列
    #### layerVoca[layer][{},{},...{}]: 各layerのindexed keywordによる単語辞書
    #### layerVocaDistr[layer][{},{},...{}]: 各layerのindexed keywordによる単語辞書の出現頻度度数辞書
#layer = 1 からサーチはスタート
    #              layer  0       1              2                    3
    #layerKeyword=['', ['keyword'], ['key1', 'key2',...], ['key1-1
def findMatch(layer, index):
    global layerMatch
    global layerCount
    print(layerMatch[0][0])
    layerMatch.append([])
    layerCount.append([0])

    for i in range(len(layerMatch[layer][index])):
        keyword = layerKeyword[layer][index]
        sentence = layerMatch[layer -1 ][index][i]
        m = re.search(keyword.lower(), sentence.lower())
        if m:
            enh = colorS[color]+m.group(0)+enhanceE
            sb = re.sub(keyword, enh, sentence)
            #### マッチした文のbuild vocabulary
            words = sentence.split()
            for w in range(len(words)):
                if words[w] in layerVoca[layer][index].keys():
                    layerVoca[layer][index][words[w]] += 1
                else:
                    layerVvoca[layer][index][words[w]] = 1
            layerCount[layer][index] += 1   

def enhance(str):
    str =colorS[color]+str+ enhanceE
    return str

def searchMatch(keyword, docArray, matchArray, voca={}):
    #### nFound = searchMatch[keyword, docArray, matchArray]
    #### docArrayをkeywordでサーチして、マッチした文をmatchArrayに収納する。
    #### searched = searchMatch(keywords, docn, LayerMatch[0], layerVoca[0])
    nFound = 0 
    for i in range(len(docArray)):
        #### 長過ぎる文は除外 constant: tooLong
        if len(docArray[i]) > tooLong:
            continue
        if keyword[0]  in regExChar:
            continue
        if keyword[-1]  in regExChar:
            continue
        m = re.search(keyword.lower(), docArray[i].lower())
        if m:
#            print(i,keyword,docArray[i]) #debug
            matchArray.append(docArray[i]) 
            nFound += 1   
            #### 全データベース中でマッチした文のbuild vocabulary
            words = docArray[i].split()
            for w in range(len(words)):
                if words[w][0] in regExChar:
                    continue
                if words[w][-1] in regExChar:
                    continue
                if words[w] in voca.keys():
                    voca[words[w]] += 1
                else:
                    voca[words[w]] = 1
    return nFound
 
"""
*********** kwic (keyword in context)
    keywordの位置positionを求める: index = line.find(keyword)
    語の前の文字列sPKeyを切り出し、文字数nPCharを求める
        nPCharがnLLenより長ければ、後ろnLLenを切り出す。
        短かければ、スペースで埋める(足りない分のスペース+sPKey)k
    語の前の文字列sPKeyTを求める
    語の後の文字列sAKeyについても同様の処理をしてsAKeyTを求める
    line = sPKeyT + enhance(keyword) + aAKeyT　を辞書に格納する。
    lineをsAKeyTでソート
                             |   index        |
        |    leftSpace      | leftStr        |<index
        |                      nLLen         |
                            |    | nLLen      |
"""
def kwic(line, keyword):
    index = line.find(keyword)
    if index <0:
        index = line.find(keyword.capitalize())
        if index < 0:
            index = line.find(keyword.lower())
            if index <0:
                return line[:nLLen]
    leftStr = line[:index]
    rightStr = line[index:]
    leftSpace = nLLen - index
    rightSpace = len(line) - index
    if leftSpace > 0:
        leftStr = ' ' * leftSpace + leftStr
    else:
        pos = index - nLLen
        leftStr = leftStr[pos:]
    if rightSpace > 0:
        rightStr = rightStr[:nLLen]
    return leftStr + rightStr

def rightStr(line, keyword):
    index = line.find(keyword)
    if index <0:
        index = line.find(keyword.capitalize())
        if index <0:
            return line
    return line[index:]

def enhanceKwd(line, kwd):
    line = line.replace(kwd, enhance(kwd))     
    KWD = kwd.capitalize()
    line = line.replace(KWD, enhance(KWD))   
    return line

def dispConBuf(start, end, keyw):
#    print(start,end,keyw, len(conBuf))
    if start <0:
        start = 0
    if end > len(conBuf):
#        end = len(conBuf) -1
        end = len(conBuf) 
    for i in range(start, end):
        if isSort:
            line = conBufSort[i]
        else:
            line = conBuf[i]
        if isKWIC:
            line = kwic(line, keyw ) 
        line = enhanceKwd(line, keyw)
        line = enhance(str(i+1)+')')+line       
        print(line)

def flag(flagName):
    if flagName == 'KWIC':
        if isKWIC:
            return 'KWIC'
    if flagName == 'sort':
        if isSort:
            return 'sort'
    return ''

def toggle(flag):
    if flag:
        return False
    else:
        return True

def copy2Clipboard(command):
    global conBuf
    global conBufSort

    if command[0] == ']':
        strNum = str(command[ 1:])
        if strNum.isdigit():
            nLine = int(strNum) -1
            if nLine in range(len(conBuf)):
                if isSort and isMulti :
                    line = conBufSort[nLine]
                else:
                    line = conBuf[nLine]
                pyperclip.copy(line)
                print(enhance(str(nLine+1)+')'), line, "\n has been copied to clipboard ...")
                return True
    return False

def copyAll2Clipboard(buf, kwd):
    doc = ''
    nTitle = len(buf)
    for i in range(nTitle):
        line = kwic( buf[i], kwd )
#        line = enhanceKwd(line, kwd)
        doc += line+'\n'
    pyperclip.copy(doc)
    print("{:,d} kwic expressions have been copied to clipboard ...".format(nTitle))

def promptHelp():
    print (''''a':jump to the start point     'b':back to previous list
'e':jump to the end             'CR':return for next list
's':toggle sort mode           '.k':toggle KWIC mode
'C':copy all lists to clipboard  'h':invoke this page
']number':copy numbered list to clipboard
any other key to quit''')

def dispController():
    global isKWIC
    global isSort
    global conBuf
    global conBufSort

    start = 0
    isSkip = False
    if isKWIC:
        delta = limit * poisson
    else:
        delta = limit
    while True:
        if not isSkip:
            dispConBuf(start, start+ delta, keywordArray[0])
        else:
            isSkip = toggle(isSkip)
#        message = "<<-a<-b:CR->e->>, 's':sort tgl, any other:quit "+flag('sort')+flag('KWIC')+">>>"
        message = "<<-a<-b:CR->e->>, typ h for help "+flag('sort')+flag('KWIC')+">>>"
        message = "/{:,d})".format(found) + message
        prompt = input(enhance(message))
        if prompt == '':
#            start += limit * poisson
            start += delta
            start = min(start, len(conBuf))
        elif prompt == 'b':
#            start -= limit * poisson
            start -= delta
            start = max(0, start)
        elif prompt == 'a':
            start = 0
        elif prompt == 'e':
            start = len(conBuf) - limit * poisson
        elif prompt.isdigit():
            start = min(len(conBuf)+1, int(prompt)-1)
        elif prompt == 'C':
            copyAll2Clipboard(conBufSort, keywordArray[0])
            isSkip = True
        elif prompt == '.k':
            isKWIC  = toggle(isKWIC)
            if isKWIC:
                delta = limit*poisson
            else:
                delta = limit
        elif prompt == 's':
            isSort = toggle(isSort)
        elif prompt == 'h':
            promptHelp()
            isSkip = True
        elif copy2Clipboard(prompt):
            isSkip = True
            continue
        else:
            return


##### keyword matching search
layerKeyword=[[]]
layerMatch=[[]]
layerFound=[[]]
layerVoca=[{}]

keywords = ''
searched = 1
underline ='\033[04m\033[01m'
red = '\033[31m\033[01m'
green = '\033[32m\033[01m'
yellow = '\033[33m\033[01m'
blue = '\033[34m\033[01m'
magenta = '\033[35m\033[01m'
cyan = '\033[36m\033[01m'
colorS =  {'enhance':underline, 'red': '\033[31m', 'green':  '\033[32m',  'yellow' : '\033[33m', 'blue' : '\033[34m', 'magenta' : '\033[35m', 'cyan' : '\033[36m'}
color = 'enhance'
enhanceS = colorS[color]
enhanceE = '\033[0m'
limit = 10
poisson = 2
tooLong = 500
isKWIC = True
isSort = True
nLLen = 36
res='' #bug?

######################## main routine
load()
loadEnv()
preMessage()
while True:
    if isKWIC:
        print("keyword(. for menu)KWIC>>>", end='')
    else:
        print("keyword(. for menu)>>>", end='')
    regex = False
    pKeywords = keywords
    keywords = ""
    vocaDistr = {}
    useHistory = False

    keywords = input()    
    if keywords == '':
        continue
    elif copy2Clipboard(keywords):
        continue
    elif keywords[0] in regExChar:
        continue
    elif keywords == '.':
        ans = menu()
        if ans == 'quit':
            break
        if not ans == '.':
            keywords = ans
            useHistory = True
        else:
            continue
    elif keywords in ['.i', '.c', '.h', '.v', '.a', '.j', '.k',  '.n', '.o', '.l', '.s', '.q' ]:
        res = command(keywords[1])
        if res == 'quit':
            break
        if keywords in ['.h', '.v', '.a', '.j'] and not res=='' :
            keywords = res
            useHistory = True
        elif keywords in ['.k']:
            isKWIC = toggle(isKWIC)
            continue
        else:
            continue
    #### history shortcut
    elif keywords[0] == '.' and keywords[1:].isdigit():
        keywords = history[int(keywords[1:])]
        useHistory = True
    if useHistory:
        print("keyword(. for menu, shortcuts)>>>", keywords, end='')
        additionalKeywords = input()
        keywords += additionalKeywords
    #### regular expression search
    if keywords[:2] in ['.r'] and not res=='':
        regex = True
        keywords = keywords[2:]

    #### multiple search入力処理
    isMulti = False
    rank=[]
    keywordArray = keywords.split(':')
    if len(keywordArray) > 1:
        isMulti = True  #debug
    #### 空文字があるなら配列より削除だが、multiSearchとして扱う
    for i in range(len(keywordArray)):
        if keywordArray[i] == '':
            keywordArray.pop(i)
#   for i in range(len(keywordArray)):
#        rank.append( getWordRank(keywordArray[i]))

    ### associated wordsを番号で呼び出し、associated keywordで置き換え
    if keywordArray[0].isdigit():
        nAWord = len(aWordArray)
        number = int(keywordArray[0])
        if number > nAWord or number <=0:    #debug
            continue
        keywords = "" #keywords再構築
        for i in range(len(keywordArray)):
            number = int(keywordArray[i])
            if number > nAWord or number <= 0:
                break
            keywordArray[i] = aWordArray[number-1]
            keywords += aWordArray[number-1]
            if isMulti:
                keywords += ":"
    #### rank 表示
    for i in range(len(keywordArray)):
        rank.append( getWordRank(keywordArray[i]))

    history.insert(0, keywords)

    layerKeyword =[[keywords]]

    #### search 結果 headline 表示
    print()
    print('='*10, 'search for ', end="")
    for i in range(len(keywordArray)):
        print(enhance(keywordArray[i]), end="")
        print(rank[i], end="")
        print(' =>', end="")
    if isMulti:
        print("multiple key search")
    else:
        print("neural deep search")

    #### layer 0 : 1-layered neural deep searchの 第０層
    #### nSearch = searchMatch[keyword, docArray, matchArray]
    #### docArrayをkeywordでサーチして、マッチした文をmatchArrayに収納する。
    #### searched = searchMatch[keywords, docn, LayerMatch[0], layerVoca[0])
    #found = 0 #countより変更（rev4) global変数
    layerMatch=[[]] 
#    layerMatch=[[[]]] 
    layerVoca = [{}] 
    found = searchMatch(keywords, docn, layerMatch[0], layerVoca[0])
    searched = len(docn) ####サーチした文数

    #### multilple keyword search
    #### multiMatch =[ docn, array of matched by 1st key, array... by 2nd key, ... ]
    multiMatch = [docn]
    multiplicity = len(keywordArray) 
    if isMulti:
        for i in range(multiplicity):
            if keywordArray[i] == '':    #おそらくこれは必要ないrev4.20
                continue
            multiMatch.append([])
            found = searchMatch(keywordArray[i],multiMatch[i], multiMatch[i+1], layerVoca[0])
            print("{}({}) ".format(keywordArray[i], found), end="")
        print()
    if found == 0:
        print("no match")
        continue

    #### neural network 構築： keywordが接続するnodesの構築
    #### matchした文中の高頻度出現単語（limit*poissonまで）の頻度計算 => vocaDist辞書
    #### 全ての単語の頻度計算を行うと精度が下がる（過学習？）
    #### constants:  limit, poisson
    #### globals: layerVoca[{}, ...], baseVoca{}, layerFound[count,...], VaocaDistr{}
    #### locals: foundRate, expectRate, found
    vocN = 0
    for k, v in sorted(layerVoca[0].items(), key=lambda x:-x[1]):
        foundRate = v / found
        if k in baseVoca.keys():
            expectRate = baseVoca[k]/ searched 
            vocaDistr[k] = foundRate / expectRate
        vocN += 1
        if vocN > limit*poisson:
            break
    #### layer0 後処理
    layerFound[0] = found

    if not isMulti:
        #### ####     layer 1 ##########
        layerMatch.append([])
        layerKeyword.append([])
        layerFound.append([])
        layerVoca.append([{}])
        nAssociated = 0
        for k, v in sorted(vocaDistr.items(), key=lambda x:-x[1]):
            pattern = ' ' + k + ' ' # wrapping by space 単語の一部としての検索を抑止
            layerKeyword[1].append(k)
            layerFound[1].append(0)
            layerMatch[1].append([])
            #各associated keywordについてサーチ
            layerFound[1][nAssociated] = searchMatch(pattern, layerMatch[0], layerMatch[1][nAssociated])
            nAssociated += 1
            if v < poisson:
                break

        #### 文例表示：各キーワード毎に nFor個　合計limitまで
        nKeyword = len(layerKeyword[1])
        if nKeyword == 0:
            continue
        nFor = int(limit / nKeyword)
        if nFor <1:
            nFor = 1
        nLine = 0
        #### 強調表示 for deep nueral search
        conBuf = []    #for clipboard
        for i in range(len(layerKeyword[1])):
            for j in range(len(layerMatch[1][i])):
                if j >= nFor:
                    break
                kwd= layerKeyword[1][i]
                line = layerMatch[1][i][j]
                conBuf.append(line)
                line = enhanceKwd(line, kwd)
                kwd = layerKeyword[0][0]
                line = enhanceKwd(line, kwd)
                nLine += 1
                line =enhance(str(nLine)+'-'+str(i+1)+')')+line
                print(line)

    else: #multi keyword search
        nextLimit = limit
        if isKWIC:
            nextLimit = limit*poisson
            delta = limit*poisson
        conBuf = []
        conBufSort = []

        #### console Buffer routine new
        sortedMM = sorted(multiMatch[multiplicity], key=lambda str: rightStr(str, keywordArray[0]))
        for i in range(len(multiMatch[multiplicity])):
            line = multiMatch[multiplicity][i]
            lineSort = sortedMM[i]
            conBuf.append(line)
            conBufSort.append(lineSort)
        dispController()

    #####  Associated words list
    print('='*10, 'words associated with ', end='')
    for i in range(len(keywordArray)):
        print(enhance(keywordArray[i]), end="")
        print(' '+'='*5, end="")
    print()
    dispVocaDistr(vocaDistr)
    print()

   #### summary
    if  len(docn) > 0:
        print("{:,d} found out of".format(found), "{:,d} sentences ({:.3}%).".format(searched, found*100/searched))
    else:
        print("No database loaded")
    dispHistory()
saveEnv()