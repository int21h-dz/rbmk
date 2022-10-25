# -*- coding: utf-8 -*-
from rbmk import rbmkcore
from chenals import rbmk_chenals

import types, string
from win32com.client import Dispatch, constants

class printmap:
    def __init__(self,filename,form='CSV'):
        '''Печать картограмм в различных форматах'''
        self.form = form
        if form=='CSV':
            filename+='.csv'
            self.CreateTXTfile(filename)
        elif form=='TEXT':
            filename+='.txt'
            self.CreateTXTfile(filename)
        elif form=='XLS':
             # acquire application object, which may start application
            self.COMApplication = Dispatch("Excel.Application")
            # create new file ('Workbook' in Excel-vocabulary)
            self.XLSworkbook = self.COMApplication.Workbooks.Add()
            #self.COMApplication.Visible = True
            # store default worksheet object so we can delete it later
            #self.defaultWorksheet = workbook.Worksheets(1)

        else:
            print 'UNCNOWN FILE FORMAT'
            return None


    def __del__(self):
        try:
            self.f.close()
        except AttributeError:
            None

    # remove default worksheet
#    defaultWorksheet.Delete()
##        try:
        self.COMApplication.Visible = True
        #self.COMApplication.Save()
##         except AttributeError:
##            None
    # make stuff visible now.
    #    chart.Activate()
    #    application.Visible = True

    def WriteXLSData(self,wrt):
        '''Разбор строки с картограммой в формате csv и запись ее в файл экселя'''
################################################################################
        def genExcelName(row, col):
            """Translate (0,0) into "A1"."""
            if col < 26:
                colName = chr(col + ord('A'))
            else:
                colName = chr((col / 26)-1 + ord('A')) +\
                    chr((col % 26) + ord('A'))
            return "%s%s" % (colName, row + 1)

        def addDataColumn(worksheet, columnIdx, data):
            if type(data)==types.StringType:
                range = worksheet.Range("A1:A1")
            else:
                range = worksheet.Range("%s:%s" % (
                genExcelName(0, columnIdx),
                genExcelName(len(data) - 1, columnIdx),
                ))
            for idx, cell in enumerate(range):
                if type(data)==types.StringType:
                    cell.Value = data
                else:
                    cell.Value = data[idx]
            return range
        def addDataRow(worksheet, rowIdy,data):
            range = worksheet.Range(
                "%s:%s" %
                (
                genExcelName(rowIdy, 0),
                genExcelName(rowIdy,len(data) - 1),
                )
                )
            for idy,cell in enumerate(range):
                data[idy] = string.replace(data[idy],',','.')
                try:
                    cell.Value = float(data[idy])
                except ValueError:
                    cell.Value = data[idy]
            return range

################################################################################
        # create data worksheet
        worksheet = self.XLSworkbook.Worksheets.Add()
        wshn = wrt[1:wrt.find(';')]
        xColumn = addDataColumn(worksheet, 0, wshn)
        #print xColumn
        if len(wshn) > 31:
            wshn = wshn[:31]
        worksheet.Name = wshn
        chart = self.XLSworkbook.Charts.Add()
        chart.ChartType = constants.xlCylinderCol
        chart.Name = 'P_'+wshn[:29]
        pwrt = wrt[wrt.find('*;'):]
        RowsSTR = pwrt.split('\n')

        for i in xrange(len(RowsSTR)-2):
            RowsV = RowsSTR[i].split(';')
            yRow = addDataRow(worksheet,1+i,RowsV)
            series = chart.SeriesCollection().NewSeries()
            series.Values =worksheet.Range("%s:%s" %
            (genExcelName(2, 1+i),genExcelName(57, 1+i),))
        chart.Activate()

    def CreateTXTfile(self,filename):
        '''Создает текстовый файл'''
        try:
            self.f = open(filename,'w')
        except IOError:
            self.f = self.MAINDnewFName(filename)

    def KDMK_SUZ_DELPH(self,filnam,KDMK_SUZ_DELPH):
        '''Печать положения стержней в файл для КДМК
        filnam        - имя файла для записи
        KDMK_SUZ_DELP - картограмма положения стержней в десятичном формате 56х56
        '''
        coreconv=rbmkcore()
        stCor=coreconv.dec2st(KDMK_SUZ_DELPH)
        strr=''
        for y in stCor.keys():
            for x in stCor[y].keys():
                if stCor[y][x]!=None:
                    strr+='%3i %s %s \n'%(stCor[y][x],y,x)
        #f=open(filnam,'w')
        self.f.write(strr)
        #f.close()

    def KDMK_LOAD_CARD(self,filnam,KDMK_LOAD):
        '''Печать картограммы загрузки для КДМК, размер картограммы 60х60'''
        CONVERT=rbmk_chenals()
        CONVERT_DIC=CONVERT.BOKR2KDMK
        yd=KDMK_LOAD.keys()
        yd.sort()
        xd=KDMK_LOAD[yd[0]].keys()
        xd.sort()
        strr=''
        for y in yd:
            for x in xd:
                if KDMK_LOAD[y][x]==None:
                    '''Если Нонэ значит эт у нас вакуум...'''
                    strr+='%2i '%(CONVERT_DIC[KDMK_LOAD[y][x]][0])
                else:
                    '''В противном случае нуна определьть какому номеру в Бокре соответствует
                    текущее имя канала и выдернуть из словаря соответствующий номер прототипа КДМК'''
                    BOKRNAME=KDMK_LOAD[y][x][1]
                    for BOKRTYPE in CONVERT.ROKR_CH_DIC:
                        if CONVERT.ROKR_CH_DIC[BOKRTYPE][1]==BOKRNAME:
                            try:
                                strr+='%2i '%(CONVERT_DIC[BOKRTYPE][0])
                            except KeyError:
                                print 'Can not find type conversion... BOKR TYPE:',BOKRTYPE
                                print CONVERT_DIC[BOKRTYPE]
            strr+='\n'
        #f=open(filnam,'w')
        self.f.write(strr)
        #f.close()

    def KDMK2Dto3D_CARDS(self,file,CARD,LOAD):
        '''Печать картограмм для КДМК со средними параметрами по высоте и каналам
        file- имя файла для сохранения картограммы
        CARD- словарь {'KMPC':значение для записи в ячейки соответствующие каналам КМПЦ,'KoSuZ':значение для записи в ячейки соответствующие каналам КоСУЗ}
        LOAD- картограмма загрузки АЗ в десятичном формате 56х56 и значениями вида: [0/1/2 (Отражатель/КМПЦ/КоСУЗ),'Имя','Коментарий'] '''

        yd=LOAD.keys()
        yd.sort()
        xd=LOAD[yd[0]].keys()
        xd.sort()
        tic=0
        strr=''
        LAYERS=14
        for l in xrange(LAYERS):
            for y in yd:
                for x in xd:
                    if (LOAD[y][x]!=None):
                        if LOAD[y][x][0]!=0:
                            tic+=1
                            if LOAD[y][x][0]==1:
                                strr+=str(CARD['KMPC'])+' '
                            elif LOAD[y][x][0]==2:
                                strr+=str(CARD['KoSUZ'])+' '
                            if (tic%5==0):
                                strr+='\n'
        #f=open(file,'w')
        self.f.write(strr)
        #f.close()
        #print file,CARD,LOAD.keys()
    def GurFullCoreN(self,GCOR,FNAME,GROUPS=[],LOAD=None):
        '''Печать в файл картограммы для юзера Гуревича М.И. (Новая версия)
        GCOR   - картограмма регистрации в формате {y:{x:[layers]}},
        где layers состоит из N записей-номеров регистрационных зон
        LOAD   - картограмма загрузки АЗ в формате {y:{x:[принадлежность канала, имя, коментарий]}}
        GROUPS - список с граничными энергиями
        FNAME  - имя файла для записи
        '''
        Y=GCOR.keys()
        Y.sort()
        ws=str(len(GROUPS)+1)+'\n'
        for gr in GROUPS:
            ws+=str(gr)+' '
        ws+='\n'

        cfwt=ws
        for y in Y:
            X=GCOR[y].keys()
            X.sort()
            for x in X:
                for regn in GCOR[y][x]:
                    cfwt+='%3i '%regn
                cfwt+='\n'
        #f=open(FNAME,'w')
        self.f.write(cfwt)
        #f.close()

        if LOAD!=None:
            info={}
            cc=rbmkcore()
            for y in LOAD.keys():
                for x in LOAD[y].keys():
                    if LOAD[y][x]!=None:
                        if LOAD[y][x][1] not in info.keys():
                            info[LOAD[y][x][1]]={str(GCOR[y][x]):[cc.dc2oc(abs(y-57)+3),cc.dc2oc(x+3)]}
                        else:
                            if str(GCOR[y][x]) not in info[LOAD[y][x][1]].keys():
                                info[LOAD[y][x][1]][str(GCOR[y][x])]=[[cc.dc2oc(abs(y-57)+3),cc.dc2oc(x+3)],]
                            else:
                                info[LOAD[y][x][1]][str(GCOR[y][x])].append([cc.dc2oc(abs(y-57)+3),cc.dc2oc(x+3)])
            ws=''
            for CHNAME in info.keys():
                ws+=CHNAME+'\n'
                for RZONES in info[CHNAME].keys():
                    ws+=RZONES+'\n'
                    tic=-1
                    for COOR in info[CHNAME][RZONES]:
                        tic+=1
                        ws+=str(COOR)
                        if tic%10==0:
                            ws+='\n'
                    if tic%10!=0:
                        ws+='\n'
	    try:
            	f=open(FNAME+'.info','w')
            	f.encoding='koi8r'
            	f.write(ws)
            	f.close()
	    except:
		print 'Warning can not write information file for GURcard'

    def GurFullCore(self,GCOR,GROUPS,FNAME,FCOOR='tally-coor.txt'):
        '''Печать в файл для использования в юзере Гуревича М.И.
        GCOR  - 3д картограмма из 16 слоев
        GROUPS- [] список с границными энергиями (0 и бесконечность не указываются)
        FNAME - имя файла для записи (не более 8 символов)
        FCOOR - распечатка соответствий координат/слоев- регистрационных зон
        '''
        if len(GCOR)!=16:
            print 'Wrong z dimenshen of 3d core!'
            return None
        if len(FNAME)>8:
            print 'FILE NAME for save user card to long!'
            return None
        yd=GCOR[0].keys()
        yd.sort()
        yd.reverse()
        xd=GCOR[0][yd[0]].keys()
        xd.sort()
        ws=str(len(GROUPS)+1)+'\n'
        for gr in GROUPS:
            ws+=str(gr)+' '
        ws+='\n'
        for yv in yd:
            for xv in xd:
                for z in xrange(len(GCOR)):
                    ws+=str(GCOR[z][yv][xv])+' '
                ws+='\n'
        f=open(FNAME,'w')
        f.write(ws)
        f.close()

        fcp='Y :X \Z'
        for z in xrange(len(GCOR)):
            fcp+='%3i|'%(z+1)   #str(z+1)+'   '
        fcp+='\n'
        fcp+='-'*len(fcp)+'\n'
        for yv in yd:
            for xv in xd:
                fcp+='%2s:%2s |'%(yv,xv)
                for z in xrange(len(GCOR)):
                    fcp+='%3i|'%(GCOR[z][yv][xv])
                fcp+='\n'
        #f=open(FCOOR,'w')
        self.f.write(fcp)
        #f.close()

    def CorePrint(self,core,comment='',point=','):
        '''Запись в файл картограмы core, если значения в картограмме заданы не все,
        они будут заполнены 0
		!!!!!!!!!!!!Не реализованно!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        если значения представляют собой [список], картограммы будут записаны по слоям
		!!!!!!!!!!!!Не реализованно!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        если значения представляют собой списки разной длинны то в те слои где длинны
        не хватит будут записаны -1
        core  - картограмма словарь
        form  - форма записи
            TEXT   - разделение пробелами            !!!!!!!!!!!!Не реализованно!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            CSV    - разделение ;                    !!!!!!!!!!!!Не реализованно!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            PICKLE - формат Pickle                   !!!!!!!!!!!!Не реализованно!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            XLS    - формат электронных таблиц Excel !!!!!!!!!!!!Не реализованно!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        fname - имя файла без расширения, оно зависит от формата
        point - разделитель целой и дробной части'''
        def chenpo(st,point):
            '''Процедурка замены разделителя целой и дробной части в строке'''
            pp=st.find('.')
            if pp==-1:
                return st
            return st[:pp]+point+st[pp+1:]

        def testformval(core):
            '''Определение формата значений'''
			# TODO: доделать
            for y in core.keys():
                for x in core[y].keys():
                    try:
                        core[y][x].keys()
                        return 'DICT'
                    except:
                        None
			return 'FLOAT'

        testformval(core)
        form = self.form
		# TODO: со списками нужно будет что-то придумать
		# пока просто забьем нулями..
        tmpcore=rbmkcore()
        core=tmpcore.fbznv(core)
        #поколдуем с ключами словаря что бы выяснить формат картограммы
        yd=core.keys()
        yd.sort()
        yd.reverse()
        if yd[0] not in ['73','67']:
            yd.reverse() #десятичный
        xd=core[yd[0]].keys()
        xd.sort()
        if form in ['CSV','XLS']:
            #fname+='.csv'
            wst=comment+';\n'
            wst+='*;' #первый символ- пропуск чтоб получилась вменяемая таблица
            for i in xd:
                try:
                    if i == None:
                        wst += ' ;'
                    else:
                        wst+=i+';'
                except TypeError:
                    if i==None:
                        wst+=' ;'
                    else:
                        wst+=str(i)+';'
            wst+='\n'
            for j in yd:
                try:
                    if j == None:
                        wst+=' ;'
                    else:
                        wst+=j+';'
                except TypeError:
                    if j == None:
                        wst+=' ;'
                    else:
                        wst+=str(j)+';'
                for i in xd:
                    if core[j][i] == None:
                        wst+=chenpo(' ',point)+';'
                    else:
                        wst+=chenpo(str(core[j][i]),point)+';'
                wst+='\n'
        elif form=='TEXT':
            fname+='.txt'
            #выясним максимальную длинну записи
            print 'You select text format for save map of core'
            print 'please check len of data!'
            print '*'*50
            print 'Module not complited!'
            print '*'*50
            return
        elif form=='PICKLE':
            fname+='.dump'
            #f=open(fname,'w')
            pickle.dump(core,self.f)
            #f.close()
        else:
            print 'Wrong file format'
        if form in ['CSV','TEXT']:
            #try:
            #    f=open(fname,'w')
            #except IOError:
            #    f=self.MAINDnewFName(fname)
            self.f.write(wst)
            #f.close()
        elif form == 'XLS':
            self.WriteXLSData(wst)

    def MAINDnewFName(self,ofname, stn=None, ras= None):
        '''Если нет доступа к файлу для записи пытается дополнить имя файла постфиксом и возвращает соответствующий файловый объект'''
        if stn==None:
            stn = ofname[:ofname.rfind('.')]
            ras = ofname[ofname.rfind('.'):]
            nfn = stn+'~1'+ras
            try:
                f = open(nfn,'w')
                return f
            except IOError:
                return self.MAINDnewFName(nfn,stn,ras)
        else:
            #print ofname, stn, ras
            stn = ofname[:ofname.find('~')]
            ras = ofname[ofname.rfind('.'):]
            npos = int(ofname[ofname.find('~')+1:ofname.rfind('.')])+1
            nfn = stn+'~'+str(npos)+ras
            try:
                f = open(nfn,'w')
                return f
            except IOError:
                return self.MAINDnewFName(nfn,stn,ras)


if __name__=='__main__':
    br=printmap()
    br.coreprint(core)
    br.coreprint(core,form='PICKLE')
    br.coreprint(core,form='TEXT')