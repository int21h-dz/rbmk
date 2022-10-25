# -*- coding: utf-8 -*-
##from parsers import *##
import string, cStringIO, shlex
import re
import types
from chenals import rbmk_chenals
from core import rbmkcore

class getMCUfinFile:
    def __init__(self,filename):
        '''Класс для получения информации из МЦУ ФИН-файла'''
        f=open(filename,'r')
        self.fl=f.readlines()
        f.close()
        self.fst=string.join(self.fl)

        self.CORE_REZ={}

        self.getRate()
        self.getKeff()
        self.getBegda()

    def getBegda(self):
        '''Получение данных для begda.sys'''
        re4f='([A-Z\d]{1,4}[ ]+(?:(?:H2OK)|(?:COHR)|[TG])[ ]+[024][ ]+[.\d]+[ ]+[.\d]+)'
        recomp=re.compile(re4f)
        result=recomp.findall(self.fst)
        if type(result)!=types.NoneType:
            self.CORE_REZ.setdefault('Begda.sys',{})
            for rez in result:
                begst=string.split(rez)
                self.CORE_REZ['Begda.sys'].setdefault(begst[0],{\
            'MODE':begst[1],\
            'BLOK':int(begst[2]),\
            'RES.BOUNDARY':float(begst[3]),\
            'DTEM':float(begst[4])\
            })

    def getKeff(self):
        '''Получение коэффициентов размножения'''
        ktype=[ 'Brissenden Estimator',\
                'Combined   Estimator',\
                'Collision  Estimator',\
                'Absorption Estimator']
        self.CORE_REZ.setdefault('Keff',{})
        for line in self.fl:
            for sk in ktype:
                if sk in line:
                    self.CORE_REZ['Keff'].setdefault(sk,float(string.split(line)[2][:-1]))

    def getRate(self):
        '''Получение скоростей реакций'''
        fst=self.fst
        re4f='(([A-Z\d ]{1,4})[ ]([-+.E\d]{10,10}[ ]?){3,3})'
        recomp=re.compile(re4f)
        result=recomp.findall(fst)
        if type(result)==types.ListType:
            self.CORE_REZ['REACTION_RATE']={}
            for rez in result:
                try:
                    self.CORE_REZ['REACTION_RATE'].setdefault(string.split(rez[0])[0],\
                {'003':float(string.split(rez[0])[1]),\
                '918':float(string.split(rez[0])[2]),\
                '018':float(string.split(rez[0])[3])})
                except IndexError:
                    None
    def getREG(self):
        '''Выдирание инфы из полномасштабного юзера ВНИИАЭС'''
        fst=self.fst
        sto=string.find(fst,'Bichkov')
        eto=string.find(fst,'End Bichkov')
        TOFP=fst[sto:eto]
        FDRESD='(?:Tally Region)(?#TR#)[ ]{0,}\d{1,}(?:\s{1,}\d{1,}(?:(?:[ ]{1,}[-+.eE\d]{12,12})(?:[ ]{1,}[-.\d]{5,6})){,4}){1,}'
        prog = re.compile(FDRESD)
        result = prog.findall(TOFP)
        if (result!=None):
            TallyR={}
            for rez in result:
                if ('Tally Region' in rez):
                    sprez=rez.split()
                    ckey=int(sprez[2])
                    TallyR[ckey]={}
                    del(sprez[:3])
                    for i in xrange(0,len(sprez),9):
                        TallyR[ckey][sprez[i]]={'FLUX':None,'ABS_RATE':None,'FIS_RATE':None,'SCAT_RATE':None}
                        TallyR[ckey][sprez[i]]['FLUX']     =[sprez[i+1],sprez[i+2]]
                        TallyR[ckey][sprez[i]]['ABS_RATE'] =[sprez[i+3],sprez[i+4]]
                        TallyR[ckey][sprez[i]]['FIS_RATE'] =[sprez[i+5],sprez[i+6]]
                        TallyR[ckey][sprez[i]]['SCAT_RATE']=[sprez[i+7],sprez[i+8]]
            self.TallyR=TallyR
            return TallyR
    def normalizeREGs(self,REG_CARD):
        '''"Нормализует" зарегестрированные функционалы в
        соответствии с количеством данных регистрационных зон в расчете.
        Использует картограмму юзера из класса getGuUserCard (аргумент)
        и данные о функционалах по регистрационным зонам self.TallyR'''
        COUNT_DIC={}
        for y in REG_CARD.keys():
            for x in REG_CARD[y].keys():
                for i in REG_CARD[y][x]:
                    if i in COUNT_DIC.keys():
                        COUNT_DIC[i]+=1
                    else:
                        COUNT_DIC[i]=1
        del(COUNT_DIC[0])
        for zone in COUNT_DIC.keys():
            for group in self.TallyR[zone].keys():
                for param in self.TallyR[zone][group].keys():
                    val=self.TallyR[zone][group][param]
                    val[0]=str(float(val[0])/COUNT_DIC[zone])
                    self.TallyR[zone][group][param]=val
        return self.TallyR
class getGuUserCard:
    def __init__(self,filename):
        '''Класс для получения картограммы для Юзера Гуревича М.И.'''
        f=open(filename,'r')
        fs=f.readlines()
        f.close()
        NGR=fs[0] #число энергетических групп
        del(fs[0])
        EGB=fs[0] #границы энергетических групп
        del(fs[0])
        #TODO: Доделать читалку\возвращалку по количеству энергетических групп
        aol=''
        for lin in fs:
            aol+=lin
        spaol=aol.split()
        tic=-1
        for sv in spaol:
            tic+=1
            spaol[tic]=int(sv)
        spvorz=[]
        for n in xrange(56*56):
            spvorz.append(spaol[:16])
            del(spaol[:16])
        gc=rbmkcore()
        retcore=gc.l3136toD56x56(spvorz)
        self.REG_CARD=retcore

class getcore:
    def __init__(self,fname):
        '''Получение картограмм из различных источников'''
        self.GC_ERRORS=\
        {
        1 : 'FILE NOT FOUND',
        2 : 'CAN NOT DETECT FILE FORMAT',
        3 : 'CAN NOT CLEAR CARDS FROM SPAM'
        }
        try:
            f=open(fname,'r')
        except IOError:
            return {self.GC_ERRORS[1]:None}
        flist=f.readlines()
        fstr=''
        for l in flist:
            fstr+=l
        F_FORMAT,NOT_PREPDIC =self.FormatDetector(fstr)
        CLEAR_DIC=self.ClearCard(F_FORMAT,NOT_PREPDIC)
        FORM_CLEAR_DIC=self.CardsFulling(F_FORMAT,CLEAR_DIC)
        self.FILE_FORMAT   = F_FORMAT
        self.CARDS_DIC = FORM_CLEAR_DIC

    def CardsFulling(self,F_FORMAT,CLEAR_DIC):
        '''Приведение линейных картограмм из различных источников к единообразию'''
        if (F_FORMAT=='SADCO_IN'):
            S2BC=rbmk_chenals()
            i_suz=-1
            i_chenal=-1
            SUZ_DELPH=[]
            #print CLEAR_DIC.keys()
            for par in CLEAR_DIC['LOAD_CARD']:
                i_chenal+=1
                CLEAR_DIC['LOAD_CARD'][i_chenal]=S2BC.SADCO2BOKR(int(par))
                if (int(par)>20): #преобразуем 300 садковских положений стержней в картограмму 2488
                    i_suz+=1
                    SUZ_DELPH.append(abs(float(CLEAR_DIC['SUZ_DELPH'][i_suz])*100))
                else:
                    SUZ_DELPH.append(None)
            CLEAR_DIC['SUZ_DELPH']=SUZ_DELPH
            CoreOperation=rbmkcore()
            CLEAR_DIC['LOAD_CARD']  =CoreOperation.st2dec(CoreOperation.  l3d2488tocore(CLEAR_DIC['LOAD_CARD'  ])[0])
            #print CLEAR_DIC['LOAD_CARD']
            CLEAR_DIC['SUZ_DELPH']  =CoreOperation.st2dec(CoreOperation.  l3d2488tocore(CLEAR_DIC['SUZ_DELPH'  ])[0])
            CLEAR_DIC['BURN_CARD2D']=CoreOperation.st2dec(CoreOperation.  l3d2488tocore(CLEAR_DIC['BURN_CARD2D'])[0])
            CLEAR_DIC['WATER_FLOW'] =CoreOperation.st2dec(CoreOperation.  l3d2488tocore(CLEAR_DIC['WATER_FLOW' ])[0])
            #CLEAR_DIC['BURN_CARD3D']=CoreOperation.st3d2dec(CoreOperation.l3d2488tocore(CLEAR_DIC['BURN_CARD3D']))

            print '*'*50
            print 'SETSS BAN FOR 3D CORE! IN GETCORE.PY'
            #print 'BURN CARD AND WATER_FLOW'
            print '*'*50
        elif (F_FORMAT=='MCU_FC'):
            S2BC=rbmk_chenals()
            CoreOperation=rbmkcore()
            print CLEAR_DIC.keys()

            CLEAR_DIC['LOAD_CARD']=[]
            CLEAR_DIC['SUZ_DELPH']=[]
            CLEAR_DIC['MATERYALS']=[]
            CLEAR_DIC['TEMPR']=[]
            LLOADCARD = []
            CARD_LINE_N = -1
           # print CLEAR_DIC['A_LOAD_CARD']
            KDMK = True
            if CLEAR_DIC['MATZONES_CARD'] == {}: KDMK = False
            for par in CLEAR_DIC['A_LOAD_CARD']:
                CARD_LINE_N += 1
                CARD_COL_N = -1
                for nam in par:
                    CARD_COL_N += 1
                    CHMAN = S2BC.MCU2BOKR(nam, KDMK)
                    CLEAR_DIC['LOAD_CARD'].append(CHMAN) #Расставили картогрмму загрузки
                    tic = -1
                    if KDMK: ok = False
                    else:    ok = True
                    while not(ok): #Раставляем глубины стержнейvvvvvv
                        tic+=1
                        if ((CHMAN[0]==2) and (CLEAR_DIC['CELL_PROTOS'][tic]['CNAME'] == ' '+nam)):
                            CLEAR_DIC['SUZ_DELPH'].append(CLEAR_DIC['CELL_PROTOS'][tic]['RODBOT'])
                            ok = True
                        elif CHMAN[0]!=2:
                            CLEAR_DIC['SUZ_DELPH'].append(None)
                            ok = True

                    tic = -1
                    ok = False
                    while not(ok): #Раставляем материалы
                        tic+=1
                        #string.lstrip()
                        #print tic,string.lstrip(CLEAR_DIC['CELL_PROTOS'][tic]['CNAME']),string.lstrip(nam)
                        if (string.lstrip(CLEAR_DIC['CELL_PROTOS'][tic]['CNAME']) == string.lstrip(nam)):
                            ok = True
                            mlist = []
                            tlist = []
                            for m in CLEAR_DIC['CELL_PROTOS'][tic]['MATER']:
                                if m>0:
                                    CLEAR_DIC['FZONE'][m]['MN'] = m
                                    mlist.append(CLEAR_DIC['FZONE'][m])
                                    tlist.append(CLEAR_DIC['FZONE'][m]['T'])
                                else:
                                    mm = int(CLEAR_DIC['MATZONES_CARD'][abs(m)][self.nx-CARD_LINE_N][CARD_COL_N])
                                    if mm != 0:
                                        CLEAR_DIC['FZONE'][mm]['MN'] = mm
                                        mlist.append(CLEAR_DIC['FZONE'][mm])
                                        tlist.append(CLEAR_DIC['FZONE'][mm]['T'])
                            CLEAR_DIC['MATERYALS'].append(mlist)
                            CLEAR_DIC['TEMPR'].append(tlist)

            CLEAR_DIC['LOAD_CARD'] = CoreOperation.l3136toD56x56(CLEAR_DIC['LOAD_CARD'])
            CLEAR_DIC['SUZ_DELPH'] = CoreOperation.l3136toD56x56(CLEAR_DIC['SUZ_DELPH'])
            CLEAR_DIC['MATERYALS'] = CoreOperation.l3136toD56x56(CLEAR_DIC['MATERYALS'])
            CLEAR_DIC['TEMPR'] = CoreOperation.l3136toD56x56(CLEAR_DIC['TEMPR'])
            del(CLEAR_DIC['FZONE'])
            del(CLEAR_DIC['CELL_PROTOS'])
            del(CLEAR_DIC['A_LOAD_CARD'])
            del(CLEAR_DIC['MATZONES_CARD'])
        elif (F_FORMAT=='NEW FORMAT'):
            None
        return CLEAR_DIC

    def ClearCard(self,F_FORMAT,NOT_PREPDIC):
        '''
        Зачистка от мусора прочитанных картограм.
        F_FORMAT    - формат файла из которого взяты картограммы
        NOT_PREPDIC - словарь с линейными картограммами
        '''
        def oper_cor(sp,char):
            ts=string.split(sp,char)
            sp=''
            for dd in ts:
                sp+=dd+' '+char+' '
            sp=sp[:-2]
            return sp+'\n'
        def sp_oper_cor(sp):
            if string.find(sp,'+')!=-1:
                sp=oper_cor(sp,'+')
            if string.find(sp,'-')!=-1:
                sp=oper_cor(sp,'-')
            if string.find(sp,'*')!=-1:
                sp=oper_cor(sp,'*')
            if string.find(sp,'/')!=-1:
                sp=oper_cor(sp,'/')
            return sp+'\n'

        if (F_FORMAT=='SADCO_IN'):
            R_CLEAR_DIC={}
            for lcard in NOT_PREPDIC.keys():
                R_CLEAR_DIC[lcard]=NOT_PREPDIC[lcard].split()
        elif (F_FORMAT=='MCU_FC'):
            R_CLEAR_DIC = {}
            FZONE = self.sp_MCU_MATsec(NOT_PREPDIC['MATERYAL'])
            CELLSp,LOADCARD,RZCARD  = self.sp_HEAD_MCUsec(NOT_PREPDIC['HEAD'])
            R_CLEAR_DIC['FZONE'] = FZONE #self.join_MCU_CARDS(FZONE,CELLSp,LOADCARD,RZCARD)
            R_CLEAR_DIC['CELL_PROTOS'] = CELLSp
            R_CLEAR_DIC['A_LOAD_CARD'] = LOADCARD
            R_CLEAR_DIC['MATZONES_CARD'] = RZCARD
        else:
            print 'Do not know how clear %s cards from spam' %(F_FORMAT)
            return {self.GC_ERRORS[3]:None}
        return R_CLEAR_DIC

    def FormatDetector(self,fstr):
        '''Детектор форматов файлов
        fstr- файл слепленый в строку
        Доступные форматы:
        1. Входной файл САДКО
        2. ...
        '''
        FDRESD={} #для чтения других файлов нужно дополнить словарь ключом-наименованием типа файла со значением-регулярным выражением для чтения файла
        FDRESD=\
        {
        'MCU_FC':'((?P<MATERYAL>(?:FZONE)[\s\S]*?(?:FINISH))[\s\S]*?)(?P<HEAD>((?:HEAD)[\s\S]*?)(?P<NET>((?:NET )[\s\S]*?(?:FINISH)+)))',
        'SADCO_IN':'[-\.E+\d]{1,}[ ]{1,}[\d][\s]{0,}'\
        +'(?P<LOAD_CARD>(([\d]{1,2}[ ]{,4}){8,20}[\s]{1,}){125,125})'\
        +'(?P<BURN_CARD2D>((([+\.E\d]{,11}[ ]{,2}){6,6}[\s]{0,}){414,414})(([+\.E\d]{,11}[ ]{,2}){4,4}[\s]{0,}))'
        +'(?P<BURN_CARD3D>((([+\.E\d]{,11}[ ]{,2}){6,6}[\s]{0,}){29026,29026})(([+\.E\d]{,11}[ ]{,2}){4,4}[\s]{0,}))'
        +'(?P<SUZ_DELPH>((([+-\.E\d]{,11}[ ]{,2}){6,6}[\s]{0,}){50,50}))'
        +'(?P<WATER_FLOW>((([+-\.E\d]{,11}[ ]{,2}){6,6}[\s]{0,}){414,414})(([+-\.E\d]{,11}[ ]{,2}){4,4}[\s]{0,}))'
        }
        for F_TYPE_TEST in FDRESD.keys():
            prog = re.compile(FDRESD[F_TYPE_TEST])
            fsfdff=string.split(fstr[:string.find(fstr,'\n')])
            mbs=False
            if len(fsfdff)==2:
                '''May be it is sadko format file'''
                try:
                    t=float(fsfdff[0])
                    t=float(fsfdff[1])
                    mbs=True
                except:
                    '''Except while str->float convertion- it is not sadko file format'''
                    mbs=False
            if ((F_TYPE_TEST=='SADCO_IN') and mbs):
                result = prog.search(fstr)
            else:
                result=None
            if (F_TYPE_TEST!='SADCO_IN'):
                result = prog.search(fstr)
            if (result!=None):
                print 'File format detected: %s' %(F_TYPE_TEST)
                return F_TYPE_TEST,result.groupdict()
        return 'UNKNOWN',{self.GC_ERRORS[2]:None}

################################################################################
    def sp_MCU_MATsec(self,MAT_SEC):
        '''Clear from spam MCU fzone section and return dict{#:{'T':300,'ISO':{'U235':2.55e-04, ...}}}'''
        FZONE = {}
        tic=-1
        for ss in string.split(MAT_SEC,'FZONE*'):
            tic+=1
            tic2=-1
            for ss2 in string.split(ss,'\n'):
                if len(ss2)!=0 and string.split(ss2,',')[0][0]!='*':
                    tic2+=1
                    if tic2==0:
                        if   len(string.split(ss2,','))==1:
                            CUR = string.split(ss2,',')[0]
                            CUR = int(string.split(CUR)[0])
                            FZONE[CUR]={'T':'300.0'}
                        elif len(string.split(ss2,','))==2:
                            CUR = string.split(ss2,',')[0]
                            CUR = int(string.split(CUR)[0])
                            FZONE[CUR]={'T':string.split(ss2,',')[1]}
                        else:
                            return NONE
                    else:
                        try:
                            FZONE[CUR]['ISO'].setdefault(string.split(ss2,':')[0],string.split(ss2,':')[1])
                        except:
                            try:
                                FZONE[CUR]['ISO']={string.split(ss2,':')[0]:string.split(ss2,':')[1]}
                            except:
                                if string.split(ss2,':')!=['FINISH']: return None
        return FZONE
################################################################################
    def sp_HEAD_MCUsec(self,HEAD_SEC):
        '''Eject cells data from HEAD section of MCU input data'''
        SplitedHS = string.split(HEAD_SEC,'NET')
        if len(SplitedHS) == 2:
            CELLS = SplitedHS[0]
            LMRM  = SplitedHS[1]
        elif len(SplitedHS) == 3:
            CELLS = SplitedHS[0]
            LMRM  = SplitedHS[2]
        EjCELLS = []
        sCELLS = string.split(CELLS,'\n')
        nsC = []
        for sC in sCELLS:
            if ((len(sC)!=0) and (sC[0]!='*') and (sC[:2]!='C=')):
                nsC.append(sC)
        CELLS = string.join(nsC,'\n')
        sCELLS = string.split(CELLS,'CELL')
        tic=-1
        for sC in sCELLS:
            tic+=1
            if tic!=0:
                EjCELLS.append(self.sp_CELL_Eject(sC)) #Ejected data!
        spLMRM = string.split(LMRM,'*  Map Reg',1)
        if len(spLMRM) == 1:
            MR = spLMRM[0]
            MZ = ''
        elif len(spLMRM) == 2:
            [MR,MZ] = spLMRM
        LOADCARD = self.sp_LOAD_Eject(MR)              #Ejected data!
        RZCARD = self.sp_Map_Eject(MZ)                 #Ejected data!
        return EjCELLS,LOADCARD,RZCARD
##        for lin in EjCELLS:
##            print lin
##        for lin in LOADCARD:
##            print lin
##        for lin in RZCARD:
##            print lin
################################################################################
    def sp_Map_Eject(self,MMZ):
        '''Rerurn dict of materyals pointers {PointerNum:{LoadCardLineNum:[mat #,mat #,]}}'''
        LS = '*  Map Reg and Mat zones'
        MMZ = MMZ.split(LS)
        NMMZ = []
        tic = -1
        for mmz in MMZ:
            tic += 1
            if tic == 0:
                mmz = mmz[mmz.find('\n'):]
            NMMZ.append(mmz)
        MMZ = string.join(NMMZ)
        MMZ = MMZ.split('\nP')
        del(MMZ[0])
        NMMZd = {}
        for mmz in MMZ:
            spmmz = self.MCUcOP(mmz.split())
            if not(int(spmmz[0][:2]) in NMMZd.keys()):
                NMMZd[int(spmmz[0][:2])] = {}
            NMMZd[int(spmmz[0][:2])][int(spmmz[0][2:])] = spmmz[1:]
        return NMMZd
################################################################################
    def sp_LOAD_Eject(self,MRL):
        '''Eject core load map from mcu map'''
        MRL = self.cl_Comments(MRL)
        MRL = MRL.split('\nT')
        LC = []
        LCC = []
        sSize = MRL[0].split()
        sSize = sSize[-2:]
        [nx,ny] = sSize
        try:
            self.nx = int(nx); ny = int(ny)
        except:
            sSize = MRL[0].split(',')
            sSize = sSize[-1]
            self.nx = int(sSize)
        del(MRL[0])
        for m in MRL:
            sm = m.split()
            del(sm[0])
            if len(sm)!=self.nx:
                sm = self.MCUcOP(sm)
            LC.append(sm)
        return LC #C
################################################################################
    def cl_Comments(self,MRL):
        '''Clearing from coment mcu text'''
        comm = ['\n*','\nC=']
        for c in comm:
            cp = MRL.find(c)
            if cp != -1:
                ce = MRL[cp+len(c):].find('\n')
                MRL=MRL[:cp]+'\n'+self.cl_Comments(MRL[ce+cp+len(c):])
        return MRL
################################################################################
    def MCUcOP(self,st):
        tic = -1
        rst = []
        for cv in st:
            tic += 1
            if cv.find('*') != -1:
                cv = (cv.split('*')[1]+' ')*int(cv.split('*')[0])
                cv = cv.split()
            if type(cv) == types.StringType: rst.append(cv)
            else:
                for pcv in cv:
                    rst.append(pcv)
        return rst
################################################################################
    def sp_CELL_Eject(self,PROTOS):
        '''Eject mat from cell prototype'''
        pn = PROTOS[0: string.find(PROTOS,'\n')]
        pn = string.ljust(pn,0)
        sff = 'RODBOT '
        sp = string.find(PROTOS,sff) #+ len(sff)
        if sp != -1:
            ep = sp + string.find(PROTOS[sp:],'\n')
            rb = PROTOS[sp:ep]
            RODBOT = rb[string.find(rb,'=') + 1:]
        else:
            RODBOT = '-1'
        mnum = []
        PROTOS = PROTOS.split('END')[1]
        tic = -1
        kPs = PROTOS.split('/')
        for k in kPs:
            tic+=1
            podd = k.find(':')
            if ((tic != 0) and (podd != -1)):
                mnum.append(int(k[0:podd]))
        CELLD={'CNAME':pn,'RODBOT':int(RODBOT),'MATER':mnum}
        return CELLD

################################################################################
##        def parse_obj(lex,mesh):
##            '''Парсер описания тел'''
##            n_lex=''
##            while not(n_lex=='END'):
##                obj=[]
##                while n_lex=='/':
##                    n_lex=lex.read_token()
##                    obj.append(n_lex)
##                print obj
##            print '*'*50
##################################################################################
##        cSIO=cStringIO.StringIO(HEAD_SEC)
##        self.MCU_GLOBALS= {}
##        self.MCU_LOCALS = {}
##        self.MCU_GL_mesh= {}
##        self.MCU_LC_mesh= {}
##        lex=shlex.shlex(cSIO)
##        lex.commenters=''
##        lex.wordchars+='./'
##        lex.whitespace+=','
##        ok=False
##        Glo=False
##        body=False
##        while not(ok):
##            n_lex=lex.get_token()
##            #################
##            if n_lex=='':
##                nuls+=1
##            else:
##                nuls=0
##            if nuls==20:
##                ok=True
##            if n_lex=='NET':
##                ok=True
##                body=False
##            #################
##            if n_lex=='HEAD':
##                Glo=True
##                body=False
##            elif n_lex=='CELL':
##                Glo=False
##                body=False
##                n_lex=lex.get_token()
##                CurrentLocals=n_lex
##                self.MCU_LOCALS.setdefault(CurrentLocals,{})
##                self.MCU_LC_mesh.setdefault(CurrentLocals,{})
##                print 'NEW LOCALS:',CurrentLocals
##            elif (body and (n_lex=='END')):
##                if Glo and self.MCU_GL_mesh.keys()!=[]:
##                    parse_obj(lex,self.MCU_GL_mesh)
##
##
##                #elif
##            #################
##            if n_lex=='EQU':
##                body=False
##                if Glo:
##                    self.mcu_EQU(lex,self.MCU_GLOBALS)
##                else:
##                    self.mcu_EQU(lex,self.MCU_GLOBALS,self.MCU_LOCALS[CurrentLocals])
##            if n_lex in ['PLZ','SPH','RCC','ELL','BOX','WED','RPP','HEX','RCZ','SLA','SLB','REC','TRC','ARB','TRANSF']:
##                body=True
##                if Glo:
##                    lex.push_token(n_lex)
##                    self.mcu_mesh(lex,self.MCU_GL_mesh,self.MCU_GLOBALS) # n_lex,' in HEAD'
##                else:
##                    lex.push_token(n_lex)
##                    self.mcu_mesh(lex,self.MCU_LC_mesh[CurrentLocals],self.MCU_GLOBALS,self.MCU_LOCALS[CurrentLocals])
##
##        #print self.MCU_GL_mesh
##        #print self.MCU_LC_mesh

    def mcu_mesh(self,lex,mesh,GlobVars,Vars=None):
        '''Расшифровка поверхностей'''
        def get_params(lex,n,rezerv):
            '''Разбор описания поверхности по параметрам с учетом мат операций'''
            ok=False
            tic=-1
            abstic=-1
            expr=[]
            oper=[]
            while not(ok):
                tic+=1
                abstic+=1
                if tic==n:
                    ok=True
                if not(ok):
                    nl=lex.read_token()
                    if nl in ['+','-','*','/','sqrt']:
                        sv=lex.read_token()
                        if sv in rezerv:
                            '''Если следующая добавляемая лексема относится к зарезервированным словам- значит все плохо'''
                            print 'BUG! Can not resolve values with operator prefix, for example: -VALUE'
                            raise BugError
                        else:
                            expr[len(expr)-1]=expr[len(expr)-1]+' '+nl+' '+sv
                        tic-=1
                    elif nl in rezerv:
                        '''Если следующая добавляемая лексема относится к зарезервированным словам- значит все плохо'''
                        print 'BUG! Can not resolve values with operator prefix, for example: -VALUE'
                        print 'String:',expr
                        print 'bug lexema:',nl
                        raise NameError
                    else:
                        expr.append(nl)
            return expr
            ###################################################################
        def evalute(fe,glo,loc):
            globals().update(glo)
            locals().update(loc)
            for i in xrange(len(fe)):
                try:
                    fe[i]=eval(fe[i],globals(),locals())
                except NameError:
                    print 'Can not evalute string>>',fe[i],'<< it have undefined variable'
                    raise NameError
            return fe
            ##################################################################
        PRIM={'PLZ':2,'SPH':None,'RCC':None,'ELL':None,'BOX':None,'WED':13,'RPP':7,'HEX':None,'RCZ':6,'SLA':None,'SLB':None,'REC':None,'TRC':None,'ARB':None,'TRANSF':6}
        nm=lex.get_token()
        if Vars==None:
            Vars=GlobVars
        if nm in PRIM.keys() and PRIM[nm]!=None:
            FOR_EVAL=get_params(lex,PRIM[nm],PRIM.keys())
            meshname=FOR_EVAL[0]
            del(FOR_EVAL[0])
            if nm!='TRANSF':
                evals=evalute(FOR_EVAL,GlobVars,Vars)
            else:
                newname=FOR_EVAL[0]
                del(FOR_EVAL[0])
                tr_type=FOR_EVAL[0]
                del(FOR_EVAL[0])
                evals=evalute(FOR_EVAL,GlobVars,Vars)
                evals=newname,tr_type,evals
            if nm in mesh.keys():
                mesh[nm][meshname]=evals
            else:
                mesh[nm]={meshname:evals}

    def mcu_EQU(self,lex,GLOBVARS,VARS=None):
        '''Разбор полетов с присвоением переменных'''
        def get_equ_value(lex,GLOBVARS,VARS):
            ##############################################
            ok=False
            tos=[]
            while not(ok):
                n_lex=lex.get_token()
                if n_lex=='START_EQU':
                    ok=True
                else:
                    tos.append(n_lex)
            tos.reverse()
            if tos!=[] and tos[0]!='*':
                globals().update(GLOBVARS)
                locals().update(VARS)
                try:
                    VARS[tos[0]]=eval(string.join(tos[2:]), globals(), locals())
                    locals().update(VARS)
                except SyntaxError:
                    print 'SyntaxError:',string.join(tos[2:])
                except NameError:
                    print 'Globals:',GLOBVARS.keys()
                    print 'Locals :',VARS.keys()
                    print string.join(tos[2:])
                    raise NameError
################################################################################
        if VARS==None:
            VARS=GLOBVARS
        ok=False
        tic=0
        while not(ok):
            tic+=1
            n_lex=lex.read_token()
            if n_lex in ['EQU']:
                ok=True
                get_equ_value(lex,GLOBVARS,VARS)
                tic=0
                #print GLOBVARS.keys()
                self.mcu_EQU(lex,GLOBVARS,VARS)
                return
            if n_lex in ['RPP','END','FINISH','CELL','WED','PLZ']:
                #lex.push_token(n_lex)
                ok=True
                get_equ_value(lex,GLOBVARS,VARS)
                lex.push_token(n_lex)
                return
            else:
                if tic==1:
                    lex.push_token('START_EQU')
                lex.push_token(n_lex)

if __name__ == "__main__":
    try:
        import psyco
        from psyco.classes import *
    except:
        print 'WARNING: can not find PSYCO module, accseleration disabled'
    gc = getcore('k5scold1')
    #gc=getcore('cvar')
    #gcc=getcore('reload0.fin')
    #gc=getGuUserCard('gucard')
    #gc=getMCUfinFile('cvar.fin')
#    print gc.CORE_REZ['Begda.sys']
#    gc.getRate()
#    print gc.getREG().keys()