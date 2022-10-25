# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        модуль1
# Purpose:
#
# Author:      Администратор
#
# Created:     27.08.2014
# Copyright:   (c) Администратор 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import string
import sys
import csv
from rbmk import TroykaOut
from rbmk import Koor1884

class McuStandartReg:
    def parseOneString(self,pstr):
        ret = -1;
        try:
             num,value,errval = string.split(pstr)
             ret = float(value)
        except:
            print "Error while string unpack to 3 values (num,value,errval): ",pstr
            num = -1
            value = -1
            errval = -1

        return ret

    def get3DMCUstandartReg(self,rfile):
        #core3d = [(x,y) for x in xrange(1884) for y in xrange(14)]
        for i in xrange(1884):
            rfile.readline()
        core3d = []
        for layerNym in xrange(14):
            nlas = []
            for linChenNum in xrange(1884):

                nlas.append(self.parseOneString(rfile.readline()))
            core3d.append(nlas)
        return core3d

    def getOneGroupData(self,rfile):
        lEnergy = -1
        ok = False
        while not(ok):
            l = rfile.readline()
            if (l == ""):
                ok = True
                print "EOF"
            if "REACTION:           18" in l:
                lEnergy = string.split(l)[len(string.split(l))-1]
                rfile.readline()
                rfile.readline()
                ok = True
        groupdata = self.get3DMCUstandartReg(rfile)
        return lEnergy,groupdata

    def writeCsv(self,cfile,label,lBoundGroup, groupData):
        cwriter = csv.writer(cfile, dialect='excel',delimiter=';', quotechar='|',lineterminator='\n')
        cwriter.writerow([label,lBoundGroup,"Core UP"])
        layernumber = [x for x in xrange(1,15,1)]
        cwriter.writerow(["",""]+layernumber+["Integral"])
        lintooc = Koor1884()

        nnotzero = 0;
        srval = 0;
        maxval = 0;
        sumbylay=[0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        for chnum in xrange(1884):
            stfw = []
            integr=0

            for laynum in xrange(14):
                stfw.append(groupData[laynum][chnum])
                sumbylay[laynum] += groupData[laynum][chnum]
                integr+=groupData[laynum][chnum]
            #print chnum,lintooc[chnum]
            cwriter.writerow([chnum+1]+[lintooc[chnum]]+stfw+[integr])
            if (integr != 0):
                srval += integr
                nnotzero += 1
            if (integr > maxval):
                maxval = integr
                self._chCoMax = lintooc[chnum]
                self._powerMax = maxval;
        try:
            srval /= nnotzero
        except ZeroDivisionError:
            srval = -1
        cwriter.writerow(["","H"]+sumbylay)
        self._H = sumbylay
        aver = 0
        sumbl = sum(sumbylay)
        for i in xrange(14):
            try:
                sumbylay[i] = sumbylay[i] * 14 / sumbl
            except ZeroDivisionError:
                sumbylay[i] = -1
            aver +=sumbylay[i]
        aver /= 14
        cwriter.writerow(["","Hn14"]+sumbylay)
        self._H14 = sumbylay
        cwriter.writerow(["Kr = "]+[maxval/srval])
        self._kr = maxval/srval
        cwriter.writerow(["Kz = "]+[max(sumbylay)/aver])
        self._kz = max(sumbylay)/aver
        self._nLayMax = sumbylay.index(max(sumbylay)) + 1

    def getKeff(self, f):
        ok = False

        while (not(ok)):
            l = f.readline()
            if ('Beta Effective' in l):
                sp = l.split()
                self._bett = sp[2]
                #print self._bett,sp[4][:-1],float(sp[4][:-1])*3,'bet',sp
                self._dbett = float(sp[4][:-1])*3
            if ('Keff col.' in l):
                ok = True
                sp = l.split()
                self._keff = sp[3]
                self._dkeff = float(sp[4])*3


    def __init__(self,fname, power):

        self._kr  = 0
        self._kz  = 0
        self._H   = []
        self._H14 = []
        self._power = 1;
        self._powerMax = 1;
        self._nLayMax = 0;
        self._chCoMax = "";
        self._keff = -1;
        self._dkeff = -1;
        self._bett = -1;
        self._dbett = -1;

        f = open(fname,"r")
        power = float(power)
        self.getKeff(f)
        lBoundGroup, groupData1 = self.getOneGroupData(f)
        ref = open(fname+".csv","w")
        self.writeCsv(ref,"Low Energy Group",lBoundGroup, groupData1)

        lBoundGroup, groupData2 = self.getOneGroupData(f)
        self.writeCsv(ref,"Low Energy Group",lBoundGroup, groupData2)

        core3d = []
        summ = 0
        for layerNym in xrange(14):
            nlas = []
            for linChenNum in xrange(1884):
                val = groupData1[layerNym][linChenNum] + groupData2[layerNym][linChenNum]
                summ += val
                nlas.append(val)
            core3d.append(nlas)
        self.writeCsv(ref,"-","Integral by Energy", core3d)


        core3dnorm = []
        for layerNym in xrange(14):
            nlas = []
            for linChenNum in xrange(1884):
                val = groupData1[layerNym][linChenNum] + groupData2[layerNym][linChenNum]
                nlas.append(val/summ)
            core3dnorm.append(nlas)

        self.writeCsv(ref,"-","Integral by Energy, norm to 1", core3dnorm)

        try:
            troyka = TroykaOut.RePlugin(fil="trk.out")
            power = troyka.w()
            self._power = power
        except:
            print "No TROYKA output file"

        core3dpower = []
        summ = 0
        for layerNym in xrange(14):
            nlas = []
            for linChenNum in xrange(1884):
                val = core3dnorm[layerNym][linChenNum]
                summ += val*power
                nlas.append(val*power)
            core3dpower.append(nlas)
        self.writeCsv(ref,"-","Power Distrib", core3dpower)

        cwriter = csv.writer(ref, dialect='excel',delimiter=';', quotechar='|',lineterminator='\n')
        cwriter.writerow(["Integral Power by Core",summ])

        ref.close()
        f.close()

if __name__ == '__main__':
    br = sys.argv[1]
    try:
        power = sys.argv[2]
    except:
        print "No power in params, it sets to 3200, if TROYKA out file skiped"
        power = 3200.0

    McuStandartReg(br,power)
    #main(br,power)