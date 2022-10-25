# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
Плагин считывает данные из результирующего файла ПС ТРОЙКА и ТРОЙКА-МКУ.
Считываются следующие картограммы:
    -Картограмма загрузки;
    -Интегральные токи;
    -Токи в ВРД;
    -Выгорание в каналах с ВРД;
    -Мощности;
    -Мощности по показаниям датчиков ВРД;
    -Коэффициенты Кси-ТД для датчиков;
    -Коэффициенты Кси-Д для датчиков;
    -Калибровочные коэффициенты датчиков;
    -Энерговыработки;
    -Некий ченалИД ;)
Считываются следующие данные:
    -Эффективный коэффициент размножения;
    -Мощность р-ра;
    -Тип констант;
    -Станция;
    -Дата и время состояния, для которого проведен расчет;
    -Дата проведения расчета;
    -Номер блока.
"""
__name__   = 'TroykaOut'
__author__ = "Дмитрий З. expo154@online.ru"
__date__ = "11.2011"
__version__ = "$Revision: 1 $"
__credits__ = """Разработанно в ОАО 'ВНИИАЭС',
Центр научно-технической поддержки эксплуатации реакторов РБМК-1000
(Центр 360) (C).
"""

import string
from rbmk import rbmkcore
from PyQt4 import QtGui, QtCore
from io import open as ioopen

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

def __init__():
    __all__=['RePlugin']

class RePlugin():
    """Обязательное имя класса"""
    def __init__(self, dirr = None, fil = "samples/trk.out"):
        """Инициализация исходных данных плагина"""
        self.messageStr = ''
        f = open(fil, 'r')
        fl = f.readlines()
        f.close()
        fs = string.join(fl)
        ksp =string.find(fs,'KEFF= ')
        if ksp == -1:
            self.messageStr = 'Can not find KEFF= x.xxx, it TROYKA-MKY file?!'
            self._keff = '-'
            skipTroykaVRD = True
        else:
            kcp =string.find(fs,'\n',ksp)
            try:
                self._keff = float(fs[ksp+5:kcp])
                skipTroykaVRD = False
            except ValueError:
                self.messageStr = 'Wrong TROYKA out file, can not find KEFF= x.xxx'
        ss  = "  N  koord"

        self.parseVRD(ss,fs,skipTroykaVRD)
        self.TRREZ=ParseTROYKA(fil,skipTroykaVRD)
        self._W = self.TRREZ.TroykaW
        self._Wcard = self.TRREZ.powerCard
        self._LoadId = self.TRREZ.loadCard
        self._BurnUp = self.TRREZ.burnUpCard

#########################################################
    #######Картограммы ВРД
    def vrdwtk(self):
        return self._Wtk,[]
    def vrdtip(self):
        return self._tip,[]
    def vrdkgrad(self):
        return self._kGrad,[]
    def vrddisp(self):
        return self._Disp,[]
    def vrdinttok(self):
        return self._inttok,[]
    def vrdcd(self):
        return self._cd,[]
    def vrdetk(self):
        return self._Etk,[]
    def vrdctd(self):
        return self._ctd,[]
    def vrdtok(self):
        return self._tok,[]
    #################################
    #######Единичные значения тройки
    def keff(self):
        return self._keff
    def w(self):
        return self._W

    def station(self):
        return self.TRREZ._station

    def unit(self):
        return self.TRREZ._unit

    def unittime(self):
        return self.TRREZ._unitTime

    def consttype(self):
        return self.TRREZ._constType

    def calctime(self):
        return self.TRREZ._calcTime

    ################################
    #######Картограммы тройки
    def trvsmcupowercard2d(self):
        self.messageStr = self.TRREZ.powerCardMsg
        #print 'Tr Pr power'
        aw = []
        for k in self._Wcard:
            aaw = []
            for i in xrange(14):
                aaw.append(k)
            aw.append(aaw)
        return self._Wcard,aw
    def loadid(self):
        #print 'Tr Pr Load'
        return self._LoadId,[]
    def burnup(self):
        #print 'Tr Pr Burn'
        return self._BurnUp,[]
    ################################
    def message(self):
        """Процедура возвращающая диагностические сообщения"""
        return self.messageStr
################################################################################
    def parseVRD(self, st,fs, skip):
        """Чтение таблиц с данными датчиков ВРД"""
        def getVRDCOMPL(tik,c,VRDcores):
            OK = False
            while not(OK):
                tik += 1
                try:
                #if True:
                    N, koord, tip, TBK, kGrad, Disp, inttok,  cd,    Etk,    ctd,   tok,  Wtk = string.split(fl[tik])
                    vals = [tip,kGrad,Disp,inttok,cd,Etk,ctd,tok,Wtk]
                    yo = koord[:2]
                    xo = koord[2:]
                    yd=57 - (c.singleoct2des(yo)-3)
                    xd=c.singleoct2des(xo)-3
                    for i in xrange(9):
                        VRDcores[i] = c.setvalues({yd:{xd:float(vals[i])}},VRDcores[i])
                except ValueError:
                    OK = True
                except IndexError:
                    self._vrdmsg = 'Can not parse BPD data'
                    print self._vrdmsg
                    return
            return tik, VRDcores
        ########################################
        c = rbmkcore()
        if not(skip):
            cs = string.find(fs,st)
            fs=fs[cs:]
            fl = string.split(fs,"\n")
            del(fl[0])
            #VRDcore1 = c.dec48x48core()
            VRDcore1 = c.dec56x56core()
            VRDcores = []
            for i in xrange(9):
                VRDcores.append(c.dec56x56core())
            tik = -1
            tik, VRDcores = getVRDCOMPL(tik,c,VRDcores)
            tik +=2
            try:
                tik, VRDcores = getVRDCOMPL(tik,c,VRDcores)
            except TypeError:
                self._tip    = c.linCore(val=0)
                self._kGrad  = c.linCore(val=0)
                self._Disp   = c.linCore(val=0)
                self._inttok = c.linCore(val=0)
                self._cd     = c.linCore(val=0)
                self._Etk    = c.linCore(val=0)
                self._ctd    = c.linCore(val=0)
                self._tok    = c.linCore(val=0)
                self._Wtk    = c.linCore(val=0)
                return

        #tip,kGrad,Disp,inttok,cd,Etk,ctd,tok,Wtk
        #0   1     2    3      4  5   6   7   8
            self._tip    = c.core2l1884(VRDcores[0], [],0)
            self._kGrad  = c.core2l1884(VRDcores[1], [],0)
            self._Disp   = c.core2l1884(VRDcores[2], [],0)
            self._inttok = c.core2l1884(VRDcores[3], [],0)
            self._cd     = c.core2l1884(VRDcores[4], [],0)
            self._Etk    = c.core2l1884(VRDcores[5], [],0)
            self._ctd    = c.core2l1884(VRDcores[6], [],0)
            self._tok    = c.core2l1884(VRDcores[7], [],0)
            self._Wtk    = c.core2l1884(VRDcores[8], [],0)
        else:
            self._tip    = c.linCore(val=0)
            self._kGrad  = c.linCore(val=0)
            self._Disp   = c.linCore(val=0)
            self._inttok = c.linCore(val=0)
            self._cd     = c.linCore(val=0)
            self._Etk    = c.linCore(val=0)
            self._ctd    = c.linCore(val=0)
            self._tok    = c.linCore(val=0)
            self._Wtk    = c.linCore(val=0)
        #self._VRD1Wtk = c.core2l1884(VRDcores[], [],0)
################################################################################
##def codec_name(codec):
##    try:
##        # Python v3.
##        name = str(codec.name(), encoding='ascii')
##    except TypeError:
##        # Python v2.
##        name = str(codec.name())
##    return name

class IBM866FileDecoder():
    """Чтение файла финальной выдачи ТРОЙКА и декодирование (Содержит Русские символы из кодовой таблицы IBM866)"""
    def __init__(self,TROYKAfin):
        def getEndOf(fs,eb, sp = 0):
            sp = string.find(fs,eb,sp)
            if sp == -1: return '-'
            return fs[sp+len(eb):sp+string.find(fs[sp:],'\n')], sp+len(eb)

        try:
            f = ioopen(str(TROYKAfin.toAscii()),'r',encoding='IBM866')
        except:
            f = ioopen(str(TROYKAfin),'r',encoding='IBM866')

        fa = f.readlines()
        f.close()
        fs = string.join(fa)
        fs = fs[string.find(fs,u'Версия программы'):]

        try:
            self._unit      = int(getEndOf(fs,u'Энеpгоблок')[0])
        except ValueError:
            self._unitMSG = 'Cannot parse Unit name'
            print self._unitMSG
            self._unit ="-"
        try:
            self._constType,sp = getEndOf(fs,u'Расчет проведен с константами типа --->')
        except ValueError:
            self._constTypeMSG = 'Cannot parse Const Type name'
            print self._constTypeMSG
            self._constType ="-"
        self._unitTime  = getEndOf(fs,u'Исходные данные')[0]
        try:
            self._calcTime  = getEndOf(fs,u'Расчет проведен',sp)[0]
        except UnboundLocalError:
            self._calcTimeMsg ='Cannot parse Const Calculation time'
            self._calcTime = '-'
        fs = string.split(fs,'\n')
        try:
            self._station = fs[2]
        except IndexError:
            self._station = '-'


class ParseTROYKA():
    """Класс для обработки финальной выдачи ТРОЙКА"""
    def __init__(self, TROYKAfin, skipPower):
        """Инициализация исходных данных"""
        self.powerCardMsg = ''
        self.skipPower = skipPower
        dcd = IBM866FileDecoder(TROYKAfin)

        self._station   = dcd._station
        self._unit      = dcd._unit
        self._constType = dcd._constType
        self._unitTime  = dcd._unitTime
        self._calcTime  = dcd._calcTime

        try:
            f = open(TROYKAfin,'r')
        except:
            self.powerCardMsg = 'Can not open TROYKA fin file'
            return

        allfs = f.readlines()
        f.close()
        self.TroykaW     = self.GetTroykaW(allfs)
        self.loadCard,self.burnUpCard,self.powerCard = self.GetTroykaCards(allfs)

    def GetTroykaW    (self, allfs):
        '''Получает мощность р-ра из финальной выдачи ТРОЙКИ'''
        tic = -1
        for cl in allfs:
            tic += 1

            pr = "  ===>"
            poz = cl.find(pr)
            QtGui.QApplication.processEvents()
            if (poz != -1):
                ssp = string.split(cl[poz+len(pr):])
                if (len(ssp) == 3):
                    return float(ssp[0])
        self.powerCardMsg = 'Can not find Core Power in TROYKA output'
        self.REZALT = False

    def GetTroykaCards(self, allfs):
        """Чтение картограм ТРОЙКИ"""
        allfs = string.join(allfs)
        splitedTr = string.split(allfs,'(58)(57)(56)(55)(48)(47)(46)(45)(44)(43)(42)(41)(40)(39)(38)(37)(36)(35)(34)(33)(32)(31)(30)(29)(28)(27)(26)(25)')
        #0 - СУЗ +
        #1 - Типы левые
        #2 - Типы правые + мусор
        #3 - Выгорание левое
        #4 - Выгорание правое + мусор
        #5 - Мощность левое
        #6 - Мощность правое + мусор
        if not(self.skipPower):
            spamlist =[2,4,6]
        else:
            spamlist = [2,4]
        for num in spamlist:
            """Убрали мусор"""
            splitedTr[num]= string.split(splitedTr[num],"(24)(23)(22)(21)(20)(19)(18)(17)(16)(15)(14)(13)(12)(11)(10)( 9)( 8)( 7)( 6)( 5)( 4)( 3)( 2)( 1)(54)(53)(52)(51)")[1]
        _loadCard = self.clearLR(splitedTr[1],splitedTr[2])
        _burnUp   = self.clearLR(splitedTr[3],splitedTr[4])
        if not(self.skipPower):
            _power    = self.clearLR(splitedTr[5],splitedTr[6])
        else:
            c = rbmkcore()
            _power = c.linCore(val = 0)

        for ky in xrange(1884):
            _loadCard[ky]=int(_loadCard[ky])
            _burnUp[ky]=float(_burnUp[ky])*10.0
            _power[ky]=float(_power[ky])/100.0
        return _loadCard,_burnUp,_power

    def clearLR(self,left,right):
        """Зачистка мусора в считанных картограммах"""
        ll = string.split(left,'\n')
        rr = string.split(right,'\n')
        tic = -1
        lcore3136 = []
        for lll in ll:
            tic += 1
            for ak in string.split(lll[14:]):
                lcore3136.append(ak)
            for ak in string.split(rr[tic][:-11]):
                lcore3136.append(ak)
        C = rbmkcore()
        return C.core2l1884(C.l3136toD56x56(lcore3136))
################################################################################
def main():
    re = RePlugin()

if __name__ == '__main__':
    main()
