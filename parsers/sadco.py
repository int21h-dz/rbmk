# -*- coding: utf-8 -*-
import string
from rbmk import rbmkcore
def splitsadco(spfile):
    '''раздирание садковского файла на запчасти'''
    nf=2        #лажа
    nl=2488     #картограмма
    nb=2488     #выгорание
    nb3d=174160 #3д выгорание (70 слоев АЗ по 2488)
    ns=300      #положение стержней (тип> 20)
    nr=2488     #расходы
    return spfile[nf:nf+nl],\
        spfile[nf+nl:nf+nl+nb],\
        spfile[nf+nl+nb:nf+nl+nb+nb3d],\
        spfile[nf+nl+nb+nb3d:nf+nl+nb+nb3d+ns],\
        spfile[nf+nl+nb+nb3d+ns:nf+nl+nb+nb3d+ns+nr]

def sadko_in(fname):
    '''Парсер входных файлов в формате САДКО'''
    def setSadcoRodBot(card,hcard,hsuz):
        '''В соответствии с поданой картограммой размером 56х56,
        записывает в картограмму hcard 56х56 глубины погружения стержней
        из линейного массива hsuz и возвращает hcard'''
        yd=card.keys()
        yd.sort()
        yd.reverse()
        xd=card[yd[0]].keys()
        xd.sort()
        tic=-1

        for y in yd:
            for x in xd:
                if card[y][x]!=None:
                    if (int(card[y][x])>20):
                        tic+=1
                        hcard[y][x]=hsuz[tic]
        return hcard
    tipname={'2':'CTVS',\
             '3':'CTVS',\
             '4':'CTVS',\
             '5':'CTVS',\
             '6':'CTVS',\
             '12':'CGRAPH',\
             '13':'CGRAPW',\
             '18':'C2641',\
             '19':'C2641m',\
             '16':'CWATDP',\
             '26':'C505',\
             '29':'C399',\
             '25':'C093'}
    # TODO: Быть может, в переспективе, отдаленном светлом будующем зделать чтение соответствий из откуданить...
    print 'ATENTION! Be cerifool with ID of chenals!!!!'
    f=open(fname,'r')
    fstr=f.readlines()
    allfilinline=''
    for line in fstr:
	   allfilinline+=line[:-1]
    f.close()
    spfile=string.split(allfilinline)
    del(fstr)
    del(allfilinline)
    load,burnup,burnup3d,msuz,water=splitsadco(spfile)
    del(spfile)
    cl_core=rbmkcore()
    card_load=cl_core.l2488tocore(load)
    card_burnup=cl_core.l2488tocore(burnup)
    card_burnup3d=cl_core.l3d2488tocore(burnup3d)
    card_rodbot=cl_core.st56x56core()
    card_rodbot=setSadcoRodBot(card_load,card_rodbot,msuz)
    card_water=cl_core.l2488tocore(water)
    return {'LOAD':card_load,'BURNUP':card_burnup,'BURNUP3D':card_burnup3d,'RODBOT':card_rodbot,'RASHOD':card_water}

def sadko_out(fname):
    '''Парсер выходных файлов в формате САДКО'''
    print 'None'
if __name__ == "__main__":
    sadko_in("reload0.fin")