# -*- coding: utf-8 -*-
import string
from rbmk import rbmkcore
def kdmkparser(rfile):
    '''Получение картограмм из файлов КДМК
    ЧУТКА НЕДОДЕЛАННО ВОЗВРАЩАЕТ СПИСОК ПО СЛОЯМ СВЕРХУ В НИЗ, А НЕ ВМЕНЯЕМЫЙ СЛОВАРЬ КАК ВЕЗДЕ'''
    #print u'ЧУТКА НЕДОДЕЛАННО ВОЗВРАЩАЕТ СПИСОК ПО СЛОЯМ, А НЕ ВМЕНЯЕМЫЙ СЛОВАРЬ КАК ВЕЗДЕ'
    f=open(rfile,'r')
    fl=f.readlines()
    f.close()
    fl=string.join(fl)
    kdsf=fl.split()
    if len(kdsf)%14!=0: #проверка на 14 слоев
        print 'You file ',rfile,' not look as KDMK file'
        print '*'*50
        print 'Chutka ne dodelanno'
        print '*'*50
    if (len(kdsf)/14==1884):
        #картограмма состоит из 14 слоев по 1884 элемента
        nelem=1884
        listcore=[]
        for i in xrange(14):
            listcore.append(kdsf[i*nelem:(i+1)*nelem])
        for i in xrange(len(listcore)):
            for j in xrange(len(listcore[i])):
                listcore[i][j]=float(listcore[i][j])
        return listcore