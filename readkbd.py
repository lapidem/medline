#!/usr/bin/env python
#-*- coding: utf-8 -*-
'''
readkbd rev3 (c)2018 sirasawa
module readkbd
Emacs like keybind input method.
readkbd.kbdInput()
is equivalent ot input()

requires readchar
install by 'pip install readchar'
'''
import readchar
import subprocess
import sys
import re

CSI ='\033['

def pr(str):
    sys.stdout.write(str)

def csi():    #begin CSI sequence
    pr(CSI)

def cuf(n):    #cursor forward 
    csi()
    pr(str(n))
    pr('C')

def cub(n):   #back
    csi()
    pr(str(n))
    pr('D')

def ed():   #右＋下を消去
    csi()
    pr('J')

def cr():
    pr('\r')

def flush():
    sys.stdout.flush()

def fs():     #forward 
    global pos
    if pos < len(lnbuf):
        pos += 1
        cuf(1)
    flush()

def bs():    #backward
    global pos
    if pos > 0:
        cub(1)
    pos = max(0, pos -1)
    flush()

def bol():    #begin of line
    global pos, lnbuf
    if pos >0:
        cub(len(lnbuf[:pos]))
        flush()
        pos=0

def eol():    #end of line
    global pos, lnbuf
    if pos < len(lnbuf):
        cuf(len(lnbuf) - pos)
        pos = len(lnbuf) 
        flush()

def bsdel():    #BS with Delete char
    global pos, lnbuf, session, history
    if pos >0: 
        pos -= 1
        lnbuf.pop(pos)
        cub(1)
        refresh()
        history[session] = lnbuf

def refresh():
    global pos, lnbuf
    ed()
    pr(''.join(lnbuf[pos:]))
    if pos < len(lnbuf):
        cub(len(lnbuf[pos:]))
    flush()

def psession():    #previous session
    global session, index, history, lnbuf
    if session >0 and index >0:
        index -= 1
        bol()
        lnbuf = history[index]
        refresh()
        eol()

def nsession():    #next session
    global session, index, history, lnbuf
    if index <session :
        index += 1
        bol()
        lnbuf = history[index]
        refresh()
        eol()

def wheel(num):
    figure = ['-', '\\', '|', '/']
    sign = num % 4
    pr(figure[sign])
    cub(1)
    flush()

def ringHistory(word):
    global history, index
    index -= 1
    if index < 0:
        index = len(history)
    if index not in range(len(history)):
        return ''
    cycle = 0
    while True:
        if index in range(len(history)):
            string =''.join(history[index])
#            m = re.match(word, string)
            if word in string:
#            if m:
                return string
        index -= 1
        if index < 1:
            index = len(history)
            cycle += 1
        if cycle > 1:
            return ''
    return ''

def parser():
    global session, index, pos, lnbuf, history, compFlg, compSeed
#    kb = readchar.readkey()
    kb = readchar.readchar()

    code = ord(kb)
    if code == 1:    #^A
        bol()
    elif code == 2:    #^B
        bs()
    elif code == 4:    #^D
        if pos < len(lnbuf):
            lnbuf.pop(pos)
            refresh()
            history[session] = lnbuf
    elif code == 5:    #^E
        eol()
    elif code == 6:    #^F
        fs()
    elif code == 8:    #^H
        bsdel()
    elif code == 9:    #^I, Tab
        word = ''.join(lnbuf)
        if not compFlg:
            compSeed = word
            compFlg = True
#        completion = ringHistory(word)
        completion = ringHistory(compSeed)
        if completion:
            bol()
            lnbuf = list(completion)
            refresh()
            eol()
    elif code == 11:    #^K
        ed()
        tmp = lnbuf[:pos]
        lnbuf = tmp
        flush()
        history[session] = lnbuf
    elif code == 14:    #^N
        nsession()
    elif code == 16:    #^P
        psession()
    elif code == 21:    #^U
        if pos >0:
            tmp = lnbuf[pos:]
            lnbuf = tmp
            cub(pos)
            pos = 0
            refresh()
            history[session]=lnbuf
    elif code == 26:    #^Z for shell
        pr(kb)
    elif code == 27:    #Esc
        kbd = readchar.readchar()
        if kbd == '[':
            kbd = readchar.readchar()
            if kbd == 'D':
                bs()
            elif kbd == 'C':
                fs()
            elif kbd == 'A':
                psession()
            elif kbd == 'B':
                nsession()
    elif code == 13:   #\r
        print()
        history[session] = lnbuf
        return False
    elif code == 127:    #DEL
        bsdel()
    elif code > 31:   #文字入力 insertモード
        pr(kb)
        if pos >= len(lnbuf):
            lnbuf.append(kb)
        else:
            lnbuf.insert(pos, kb)
            pr(''.join(lnbuf[pos+1:]))
            cub(len(lnbuf[pos+1:]))
        pos += 1
        flush()
        history[session] = lnbuf
    if code != 9:
        compFlg = False
    return True

def initParser():
    global lnbuf, history, session, index, pos
    lnbuf = []
    history.append(lnbuf)
    session += 1
    index = session
    pos = 0

def kbdInput(message=''):
    global signal
    initParser()
    pr(message)
    flush()
    while True:
        if not parser():
            return ''.join(lnbuf)
#        if signal:
#            signal = False
#            return chr(26)

session = 0
index = 0
pos=0
lnbuf = []
history = [lnbuf]
compFlg = False
compSeed =''

'''
demonstration of readkbd.kbdInput()
'''
if __name__=='__main__':
    while True:
        print("{}>>".format(session), end='') 
        flush()
        res = kbdInput()
        if not res:
            for i in range(len(history)):
                print("{}:{}".format(i, ''.join(history[i])))
            break
