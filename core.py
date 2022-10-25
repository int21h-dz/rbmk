# -*- coding: utf-8 -*-
import pickle
import types
from math import sqrt
def dc2oc(i):
        '''Конвертер из десятичной системы в восьмеричную с обрезанием лишних нулей'''
        i=str(i.__oct__())
        if len(i)==3:
            i=(str(i)[1:])
        return i
def mi2li(i):
        '''int2str с дополнением нулем'''
        i=str(i)
        if len(i)==1:
            i='0'+i
        return i

def singleoct2des(val):
        '''Переводит одно число в десятичную систему счисления'''
        nstr=str(val)
        j=-1
        rjad=0
        for i in xrange(len(nstr)-1,-1,-1):
            j+=1
            dig=nstr[i:i+1]
            rjad+=int(dig)*8**j
        return rjad

def Koor1884():
    '''Возвращает список из 1884 значений восьмиричных координат каналов'''
    koor = []
    K0 = [
  14,20,24,28,30,32,34,36,38,40,42,42,44,44,46,46,46,
  48,48,48,48,48,48,48,48,48,48,48,48,48,48,
  46,46,46,44,44,42,42,40,38,36,34,32,30,28,24,20,14]
    k = 0;
    for i in xrange(48):
        for j in xrange(48):
            if (j < (48 - K0[i]) / 2): continue
            if (j >= (48 + K0[i]) / 2):continue
                #else:
            yY = 55 - i
            xX = 8 + j
            koor.append("'"+str(oct(yY))[1:3]+"-" + str(oct(xX))[1:3]+"'");
    return koor
                    #Koor8[k] = Convert.ToInt16(koor);
                    #RefTpk[k] = (Int16)((yY - 8) * 48 + (xX - 8));
                    #k++;

class rbmkcore:
    def __init__(self):
        '''Класс содержит функции для создания картограмм АЗ реактора РБМК, преобразования их форматов и пр.'''
        None
    def dc2oc(self,i):
        '''Конвертер из десятичной системы в восьмеричную с обрезанием лишних нулей'''
        i=str(i.__oct__())
        if len(i)==3:
            i=(str(i)[1:])
        return i
    def mi2li(self,i):
        '''int2str с дополнением нулем'''
        i=str(i)
        if len(i)==1:
            i='0'+i
        return i
    def singleoct2des(self,val):
        '''Переводит одно число в десятичную систему счисления'''
        nstr=str(val)
        j=-1
        rjad=0
        for i in xrange(len(nstr)-1,-1,-1):
            j+=1
            dig=nstr[i:i+1]
            rjad+=int(dig)*8**j
        return rjad

    def linCore(self,size = 1884, val= []):
        '''Возвращает линейный массив указаного размера заполненый указаными значениями'''
        retc = []
        for tic in xrange(size):
            retc.append(val)
        return retc

    def __stcore__(self,startkv,colen,ntype):
        '''Дополнительная процедурка, собственно и формирующая словарь-картограмму
        startkv - циферка- номер от которого начинаем плясать- верхний левый угол по Y (зависит от системы координат)
        colen   - количество ячеек в стороне квадратика
        ntype   - Система счисления для координат OCT/DEC'''
##        def singleoct2des(val):
##            '''Переводит одно число в десятичную систему счисления'''
##            nstr=str(val)
##            j=-1
##            rjad=0
##            for i in xrange(len(nstr)-1,-1,-1):
##                j+=1
##                dig=nstr[i:i+1]
##                rjad+=int(dig)*8**j
##            return rjad

        def octcore(st,cl):
            '''Вспомагательная процедурка формирования картограммы в восьмеричной системе'''
            y=[]
            x=[]
            for deccoor in xrange(self.singleoct2des(st),self.singleoct2des(st)-cl,-1):
                y.append(deccoor)
            for i in xrange(len(y)-1,-1,-1):
                x.append(y[i])
            dcore={}
            for i in y:
                li=self.dc2oc(i)
                dcore[li]={}
                for j in y:
                    lj=self.dc2oc(j)
                    dcore[li][lj]=[]
            return dcore

        def deccore(startkv,colen):
            '''Вспомагательная процедурка формирования картограммы в десятичной системе'''
            dcore={}
            for i in xrange(startkv,startkv+colen):
                li=i
                dcore[li]={}
                for j in xrange(startkv,startkv+colen):
                    lj=j
                    dcore[li][lj]=[]
            return dcore

        if ntype=='OCT':
            return octcore(startkv,colen)
        elif ntype=='DEC':
            return deccore(startkv,colen)
        else:
            print 'Strange ERROR from CoreMap Creator!'
            return None
    def l3d2488tocore(self,linm3d):
        '''Запись линейного массива размером Х*2488 в квадратные картограммы по слоям
        в возвращаемом массиве индекс 0 соответствует первой части поданного линейного массива'''
        if (len(linm3d)%2488!=0):
            print 'Error: Can not split linear array to the linear arrays with dimentions=2488'
            print 'LEN of array=',len(linm3d)
            return None
        zdim=len(linm3d)/2488
        l3dcor=[]
        for i in xrange(zdim):
            l3dcor.append(linm3d[i*2488:(i+1)*2488])
        tic=-1
        for k in l3dcor:
            tic+=1
            l3dcor[tic]=self.l2488tocore(k)
        return l3dcor

    def l2488tocore(self,linm):
        '''Запись данных из линейного массива 2488 в квадратную
        картограмму-словарь размером 56х56 в стандартном восьмеричном формате
        linm - линейный массив АЗ 2488 записи'''
        if len(linm)!=2488:
            print 'Error from l2488tocore converter- check lin. array leght!'
            return None
        core=self.st56x56core()
        dcore=self.dec56x56core()
##     data ik/10,20,24,28,32,34,36,38,40,42,44,46,48,48,50,50,52,52,
##     *54,54,54,54,54,56,56,56,56,56,56,56,56,56,56,54,54,54,54,54,52,
##     *52,50,50,48,48,46,44,42,40,38,36,34,32,28,24,20,10/
        ik=[10,20,24,28,32,34,36,38,40,42,44,46,48,48,50,50,52,52,\
        54,54,54,54,54,56,56,56,56,56,56,56,56,56,56,54,54,54,54,54,52,\
        52,50,50,48,48,46,44,42,40,38,36,34,32,28,24,20,10]
        #Всего в ряду 56 каналов ik указывает сколько каналов из линейного массива 2488 находится в текущем ряду
        y=0
        tic=-1
        for k in ik:
            y+=1
            for x in xrange(56):
                if ((x<(56/2-k/2))or(x>(56/2+k/2-1))):
                    dcore[y][x+1]=None #ГРАФИТ
                else:
                    tic+=1
                    dcore[y][x+1]=linm[tic]
        core=self.dec2st(dcore)
        return core

    def l1884to48x48(self, lCore1884):
        '''Запись данных из линейного массива 1884 в квадратную
        картограмму-словарь размером 48х48 в стандартном восьмеричном формате
        lCore1884 - линейный массив АЗ 1884 записи'''
################################################################################
        if len(lCore1884)!=1884:
            print 'Error from l1884to48x48 converter- check lin. array leght!'
            return None
        core=self.st48x48core()
        dcore=self.dec48x48core()
        ik=[14,\
            20,\
            24,\
            28,\
            30,\
            32,\
            34,\
            36,\
            38,\
            40,\
            42, 42,\
            44, 44,\
            46, 46, 46, \
            48, 48, 48, 48, 48, 48, 48, 48, 48, 48, 48, 48, 48, 48,
            46, 46, 46, \
            44, 44,\
            42, 42,\
            40,\
            38,\
            36,\
            34,\
            32,\
            30,\
            28,\
            24,\
            20,\
            14
            ]
        #Всего в ряду 48 каналов ik указывает сколько каналов из линейного массива 2488 находится в текущем ряду
        ChInRow = 48
        y=0
        tic=-1
        for k in ik:
            y+=1
            for x in xrange(ChInRow):
                if ((x<(ChInRow/2-k/2))or(x>(ChInRow/2+k/2-1))):
                    dcore[y][x+1]=None #ГРАФИТ
                else:
                    tic+=1
                    dcore[y][x+1]=lCore1884[tic]
        core=self.dec2st(dcore)
        return core
################################################################################

    def l3136toD56x56(self,lcor3136):
        '''Преобразование из линейного массива в квадратную картограмму с координатой верхнего левого угла [1,1]'''
        if len(lcor3136)%56==0:
            size=int(sqrt(len(lcor3136)))
            retcore={}
            tic=-1
            for y in xrange(size):
                retcore[y+1]={}
                for x in xrange(size):
                    tic+=1
                    retcore[y+1][x+1]=lcor3136[tic]
            return retcore
        else:
            print 'WRONG size of LINEAR ARRAY'
            return None

    def l3136toSt56x56(self,lcor3136):
        '''Преобразование из линейного массива размером 3136 в стандартную картограмму 56х56
        считывание и элементов идет построчно от верхнего левого угла АЗ'''
        if len(lcor3136)!=3136:
            print 'WRONG len of linear array, it mast be 3136!'
            return None
        stcor=self.st56x56core()
        yd=stcor.keys()
        yd.sort()
        yd.reverse()
        xd=stcor[yd[0]].keys()
        xd.sort()
        i=-1
        for yv in yd:
            for xv in xd:
                i+=1
                stcor[yv][xv]=lcor3136[i]
        return stcor

    def l2304to48x48(self,lcor2034):
        '''Преобразование из линейного массива размером 2034 в картограмму 48х48
        считывание и элементов идет построчно от верхнего левого угла АЗ'''
        print 'NOT WORK YET!'
        None

    def st56x56to3136(self,st56):
        '''Преобразование картограммы размером 56х56 в линейный массив размером 3136'''
        print 'NOT WORK YET!'
        None

    def st48x48to2304(self,st56):
        '''Преобразование картограммы размером 48х48 в линейный массив размером 2304'''
        print 'NOT WORK YET!'
        None

    def core2l1884(self,core, VFZ = None, VZ = None):
        '''Извлечение данных из картограммы core (десятичные координаты), размером 56*56
         в стандартный линейный массив размером 1884
         VFZ - значение которое требуется заменить на VZ'''
        lincor=[]
        #print core.keys()
        #gg = range(1883,0,-1)
        #print gg
        for i in xrange(1884): #,-1,-1):
            px,py = self.CSourceDataNumToMCU(i)
            #print i, px,'-',self.dc2oc(px),py,'-',self.dc2oc(py)
            try:
                av = core[py+1][px+1]
                if (av == VFZ):
                    av = VZ
                lincor.append(av) #core[self.dc2oc(py)][self.dc2oc(px)])
            except KeyError:
                print 'Error from rbmk core module: Sub core2l1884: KeyError'
                print 'Len(linCore)=',len(lincor)
                print 'Current Keys Y:X',py+1,':',px+1
                print '-----------------------------------------------------'
        return lincor

    def CSourceDataNumToMCU(self,num, refl = 4): #, px, py):
        """Конвертирование из линейного номера [0:1883] в координаты в десятичном формате
        refl = 0 - для зоны 48*48
        refl = 4 - для зоны 56 * 56?"""
        szaz = 48 #;        // size of core
        szrf = refl # 4 #;     // size of reflector
        skip = [\
      17, 14, 12, 10,  9,  8,  7,  6,  5,  4,  3,  3,
       2,  2,  1,  1,  1,  0,  0,  0,  0,  0,  0,  0,
       0,  0,  0,  0,  0,  0,  0,  1,  1,  1,  2,  2,
       3,  3,  4,  5,  6,  7,  8,  9, 10, 12, 14, 17]

        if((num < 0) or (num > 1883)):
            QtCore.qDebug(QtCore.QString('Ilegal number is %1').arg(num))
            exit
        r = num
        for j in xrange(szaz):
            #for (j=0; j<szaz; j++) {
            s = r-szaz+2*skip[j]
            if (s < 0): break
            r = s
        px = szrf+skip[j]+r
        py = szrf+szaz-j-1
        return px, py

    def st2dec(self,stcore):
        '''Конвертирование из стандартной восьмеричной картограммы в десятичную с
        координатой верхней левой ячейки [1,1]'''
        deccor={}
        if stcore==None:
            print 'ERORR: None is a wrong type for dict convertion...'
            return None
        for yval in stcore.keys():
            ydv=abs(self.singleoct2des(yval)-60)
            deccor[ydv]={}
            for xval in stcore[yval].keys():
                xdv=self.singleoct2des(xval)-3
                deccor[ydv][xdv]=stcore[yval][xval]
        return deccor

    def st3d2dec(self,st3dcore):
        '''Конвертирование стандартной, восьмеричной, 3Д картограммы в десятичную с координатой верхней левой ячейки (1:1)'''
        dec3dcore=[]
        for k in st3dcore:
            dec3dcore.append(self.st2dec(k))
        return dec3dcore

    def dec2st(self,deccor):
        '''Конвертирование из десятичной картограммы с координатой верхнего левого угла [1,1]
        в стандартную восьмеричную'''
        xddir=[]
        yddir=[]
        corsize=len(deccor.keys())
        if corsize==48:
            print 'WARNING FROM dec2st CHECK CURRENT PLUS!!!!!!! plus=8'
            plus=8
        elif corsize==56:
            plus=4
        else:
            print 'Unknown input core size!'
            return None

        for i in xrange(corsize):
            xddir.append(self.mi2li(i+1))
            yddir.append(self.mi2li(i+1))
        stcore=self.st56x56core()
        for dy in yddir:
            oy=self.dc2oc(corsize-int(dy)+plus)
            for dx in xddir:
                ox=self.dc2oc(int(dx)+plus-1)
                try:
                    stcore[oy][ox]=deccor[dy][dx]
                except KeyError:
                    stcore[oy][ox]=deccor[int(dy)][int(dx)]
                    #print KeyError.args
                    #print '-'*20
                    #print 'oy,ox:',oy,ox
                    #print 'dy,dx:',dy,dx
                    #print '-'*20
                    #print deccor[dy][dx]
        return stcore

    def suzmap(self):
        '''Создает картограмму положения стержней'''
        suzmap=[]
        print 'NOT WORK YET!'
        return suzmap

    def corSsuzmap(self,chen,suzmap):
        '''Изменение положения стержней СУЗ suzmap в соответствии
        со словарем chen (одиночные перемещения)
        Либо изменения в группе стержней в соответствии с...'''
        print 'NOT WORK YET!'
        return suzmap

    def st56x56core(self):
        '''Возвращает картограмму-словарь формата {y:{x:[]}} активной зоны реактора РБМК
        размером 56х56 с общепринятой нумирацией ячеек- в восьмиричной нумирации'''
        return self.__stcore__(73,56,'OCT')
    def st3d56x56core(self,layers):
        '''Возвращает список картограмм-словарей -=(3D)=- формата {y:{x:[]}} активной зоны реактора РБМК
        размером 56х56 с общепринятой нумирацией ячеек- в восьмиричной нумирации'''
        print 'NOT WORK YET!'
    def st48x48core(self):
        '''Возвращает картограмму-словарь формата {y:{x:[]}} активной зоны реактора РБМК
        без отражателя
        размером 48х48 с общепринятой нумирацией ячеек- в восьмиричной нумирации'''
        return self.__stcore__(67,48,'OCT')
    def dec56x56core(self):
        '''Возвращает картограмму-словарь формата {y:{x:[]}} активной зоны реактора РБМК
        размером 56х56 нумирация начинается от верхнего левого угла имеющего координату [1,1]'''
        return self.__stcore__(1,56,'DEC')
    def dec48x48core(self):
        '''Возвращает картограмму-словарь формата {y:{x:[]}} активной зоны реактора РБМК
        размером 48х48 нумирация начинается от верхнего левого угла имеющего координату [1,1]'''
        return self.__stcore__(1,48,'DEC')
    def dec56x56todec60x60(self,decor):
        '''Преобразование десятичной картограммы размером 56х56 в десятичную картограмму 60х60'''
        yd=decor.keys()
        yd.sort()
        xd=decor[yd[0]].keys()
        xd.sort()
        yn=[]
        xn=[]
        ncore={}
        for i in xrange(60):
            yn.append(i+1)
            xn.append(i+1)
        for y in yn:
            ncore[y]={}
            for x in xn:
                try:
                    ncore[y][x]=decor[y-2][x-2]
                except KeyError:
                    ncore[y][x]=None
        return ncore

    def DiffCores(self,core1,core2,persent=True, Check = [], ABS = False):
        '''Сравнение значений в двух картограммах в процентах (persent=True) или по абсолютной величине (persent=False)'''
        if (core1.keys() != core2.keys()):
            return self.printE('Different keys in the cores DICT in y dirrection')
        t1 = core1.keys()[0]
        if (core1[t1].keys() != core2[t1].keys()):
            return self.printE('Different keys in the cores DICT in x dirrection')
        rc = {}
        for y in core1.keys():
            if not(y in rc.keys()): rc[y] = {}
            for x in core1[y].keys():
                if not(x in rc[y].keys()):
                    #TODO: Сделать детектирование типов значений в картограмме
                    V1 = core1[y][x]
                    V2 = core2[y][x]
                    if (((V1 in Check) and (V2 in Check)) or (not(V1 in Check) and not(V2 in Check))):
                        if persent:
                            try:
                                rc[y][x] = (1.0-core1[y][x]/core2[y][x])*100.0
                                if ABS: rc[y][x] = abs(rc[y][x])
                            except ZeroDivisionError:
                                rc[y][x] = 0
                        else:
                            rc[y][x] = (core1[y][x]-core2[y][x])
                            if ABS: rc[y][x] = abs(rc[y][x])
                    else:
                        msg = 'Cores for diff not pass Check values\n'
                        msg +='may be it too different.\n'
                        msg +='CORE1['+str(y)+']['+str(x)+'] = '+str(core1[y][x])+'\n'
                        msg +='CORE2['+str(y)+']['+str(x)+'] = '+str(core2[y][x])
                        return self.printE(msg)
        return rc

    def printE(self, sfp):
        '''Печать ошибок в одном формате'''
        print '-'*len(sfp)
        print 'Error from RBMKCORE CLASS'
        print sfp
        print '-'*len(sfp)
        return None

    def setvalues(self,incore,core=None):
        '''Устанавливает значения из incore в картограмму core
        incore - картограмма словарь в формате {y:{x:value}}
        core   - картограмма словарь в формате {y:{x:value}} по умолчанию используется АЗ 56х56 в восьмеричном формате'''
        if core==None:
            core=self.st56x56core()
        for y in incore.keys():
            for x in incore[y].keys():
                core[y][x]=incore[y][x]
        return core

    def fbznv(self,core,dval=0):
        '''Заполнение значениями dval незанятых значениями ячеек из core'''
        for y in core.keys():
            for x in core[y].keys():
                if core[y][x]==[]:
                    core[y][x]=dval
        return core

    def l1884forReQt(self,l1884):
        """Преобразует линейный массив 1884 в линейный массив корректно отображающийся в ReQt"""
        c = rbmkcore()
        l1884.reverse()
        st48 = c.l1884to48x48(l1884)

        yd = st48.keys()
        yd.sort()
        yd.reverse()
        xd = st48[yd[1]].keys()
        xd.sort()
        xd.reverse()
        tc = []
        for y in yd:
            for x in xd:
                if ((st48[y][x]!=[]) and (st48[y][x]!=None)):
                    tc.append(st48[y][x])
        return tc

    def l1884ToMCU(self, num):
        """Преобразование линейного номера 0-1883 в координаты с началом в нижнем левом углу и концом в верхнем правом"""
        szaz = 48;     #// size of core
        szrf =  4;     #// size of reflector
        skip = [\
        17, 14, 12, 10,  9,  8,  7,  6,  5,  4,  3,  3,
        2 ,  2,  1,  1,  1,  0,  0,  0,  0,  0,  0,  0,
        0 ,  0,  0,  0,  0,  0,  0,  1,  1,  1,  2,  2,
        3 ,  3,  4,  5,  6,  7,  8,  9, 10, 12, 14, 17];

        if( (num < 0) or (num > 1883) ):
            print " Ilegal number is  ", num

        r = num;
        for j in xrange(szaz):
            s = r-szaz+2*skip[j]
            if (s < 0): break
            r = s
        px = szrf+skip[j]+r;
        py = szrf+szaz-j-1;
        return px, py

if __name__=='__main__':
    br=rbmkcore()
    core=br.st56x56core()
    dcore=br.dec56x56core()
    stfde=br.dec2st(dcore)

    lm=[]
    for i in xrange(2488):
        lm.append(i+1)
    oc=br.l2488tocore(lm)
    print oc['04']