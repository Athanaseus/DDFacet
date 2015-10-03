#!/usr/bin/env python

import numpy as np
from PSourceExtract import Gaussian
import pylab
import scipy.optimize
import time
from PSourceExtract import ClassIslands
from Other import ModColor
import pickle
import optparse
#from PSourceExtract.ClassPointFit2 import ClassPointFit as ClassFit
from PSourceExtract.ClassGaussFit import ClassGaussFit as ClassFit
#import ClassPointFit as ClassPointFit

from pyrap.images import image
from Other.progressbar import ProgressBar
from Other import reformat
from Sky import ClassSM
from Other import rad2hmsdms

from DDFacet.Other import MyLogger
log=MyLogger.getLogger("Gaussify")

def read_options():
    desc="""Questions and suggestions: cyril.tasse@obspm.fr"""
    global options
    opt = optparse.OptionParser(usage='Usage: %prog --ms=somename.MS <options>',version='%prog version 1.0',description=desc)
    group = optparse.OptionGroup(opt, "* Data-related options", "Won't work if not specified.")

    group.add_option('--RestoredImage',help='',type="str",default="")
    group.add_option('--MaskName',help='',type="str",default="")

    group.add_option('--Osm',help='Output Sky model [no default]',default='')
    group.add_option('--PSF',help='PSF (Majax,Minax,PA) in (arcsec,arcsec,deg). Default is %default',default="")
    group.add_option('--Pfact',help='PSF size multiplying factor. Default is %default',default="1")
    group.add_option('--DoPlot',help=' Default is %default',default="1")
    group.add_option('--DoPrint',help=' Default is %default',default="0")

    opt.add_option_group(group)
    options, arguments = opt.parse_args()
    f = open("last_MakePModel.obj","wb")
    pickle.dump(options,f)


from pyrap.images import image
from DDFacet.Imager.ClassModelMachine import ClassModelMachine
from DDFacet.Imager import ClassCasaImage



    
def main(options=None):
    if options==None:
        f = open("last_MakePModel.obj",'rb')
        options = pickle.load(f)

    
    
    
    
    Osm=options.Osm
    Pfact=float(options.Pfact)
    DoPlot=(options.DoPlot=="1")
    imname=options.RestoredImage


    if Osm=="":
        Osm=reformat.reformat(imname,LastSlash=False)

    im=image(imname)
    PMaj=None
    try:
        PMaj=(im.imageinfo()["restoringbeam"]["major"]["value"])
        PMin=(im.imageinfo()["restoringbeam"]["minor"]["value"])
        PPA=(im.imageinfo()["restoringbeam"]["positionangle"]["value"])
        PMaj*=Pfact
        PMin*=Pfact
    except:
        print>>log, ModColor.Str("   No psf seen in header")
        pass

    if options.PSF!="":
        m0,m1,pa=options.PSF.split(',')
        PMaj,PMin,PPA=float(m0),float(m1),float(pa)
        PMaj*=Pfact
        PMin*=Pfact


    if PMaj!=None:
        print>>log, ModColor.Str("Using psf (maj,min,pa)=(%6.2f, %6.2f, %6.2f) (mult. fact.=%6.2f)"
                           %(PMaj,PMin,PPA,Pfact),col='green',Bold=False)
    else:
        print>>log, ModColor.Str("No psf info could be gotten from anywhere")
        print>>log, ModColor.Str("  use PSF keyword to tell what the psf is or is not")
        exit()


    ToSig=(1./3600.)*(np.pi/180.)/(2.*np.sqrt(2.*np.log(2)))
    PMaj*=ToSig
    PMin*=ToSig
    


    PPA*=np.pi/180

    b=im.getdata()[0,0,:,:]
    #b=b[3000:4000,3000:4000]#[120:170,300:370]
    c=im.coordinates()
    incr=np.abs(c.dict()["direction0"]["cdelt"][0])
    print>>log, ModColor.Str("Psf Size Sigma_(Maj,Min) = (%5.1f,%5.1f) pixels"%(PMaj/incr,PMin/incr),col="green",Bold=False)
    
    nx,_=b.shape
    Nr=10000
    indx,indy=np.int64(np.random.rand(Nr)*nx),np.int64(np.random.rand(Nr)*nx)
    StdResidual=np.std(b[indx,indy])

    
    MaskName=options.MaskName
    CasaMaskImage=image(MaskName)
    MaskImage=CasaMaskImage.getdata()[0,0,:,:]
    

    snr=None
    Boost=None
    Islands=ClassIslands.ClassIslands(b,T=snr,Boost=Boost,DoPlot=DoPlot,MaskImage=MaskImage)
    Islands.FindAllIslands()
    Islands.Noise=StdResidual

    ImOut=np.zeros_like(b)
    pBAR = ProgressBar('white', block='=', empty=' ',Title="Fit islands")

    #print "ion"
    #import pylab
    #pylab.ion()
    sourceList=[]
    for i in range(len(Islands.ListX)):
        comment='Isl %i/%i' % (i+1,len(Islands.ListX))
        pBAR.render(int(100* float(i+1) / len(Islands.ListX)), comment)

        xin,yin,zin=np.array(Islands.ListX[i]),np.array(Islands.ListY[i]),np.array(Islands.ListS[i])
        xm=int(np.sum(xin*zin)/np.sum(zin))
        ym=int(np.sum(yin*zin)/np.sum(zin))
        #Fit=ClassFit(xin,yin,zin,psf=(PMaj/incr,PMin/incr,PPA),noise=Islands.Noise[xm,ym])
        Fit=ClassFit(xin,yin,zin,psf=(PMaj/incr,PMin/incr,PPA+np.pi/2))#,FreePars=["l", "m","s"])
        sourceList.append(Fit.DoAllFit())
        Fit.PutFittedArray(ImOut)

    Islands.FitIm=ImOut
    xlist=[]
    ylist=[]
    slist=[]

    Cat=np.zeros((50000,),dtype=[('ra',np.float),('dec',np.float),('I',np.float),('Gmaj',np.float),('Gmin',np.float),('Gangle',np.float)])
    Cat=Cat.view(np.recarray)

    isource=0

    for Dico in sourceList:
        for iCompDico in sorted(Dico.keys()):
            CompDico=Dico[iCompDico]
            i=CompDico["l"]
            j=CompDico["m"]
            s=CompDico["s"]
            xlist.append(i)
            ylist.append(j)
            slist.append(s)
            f,d,dec,ra=im.toworld((0,0,i,j))
            Cat.ra[isource]=ra
            Cat.dec[isource]=dec
            Cat.I[isource]=s

            Cat.Gmin[isource]=CompDico["Sm"]*(incr/ToSig/3600.)*np.pi/180/(2.*np.sqrt(2.*np.log(2)))
            Cat.Gmaj[isource]=CompDico["SM"]*(incr/ToSig/3600.)*np.pi/180/(2.*np.sqrt(2.*np.log(2)))
            Cat.Gangle[isource]=-CompDico["PA"]+np.pi/2
            #
            isource +=1

    Cat=Cat[Cat.ra!=0].copy()
    Islands.FittedComps=(xlist,ylist,slist)
    Islands.plot()

    SM=ClassSM.ClassSM(Osm,ReName=True,DoREG=True,SaveNp=True,FromExt=Cat)#,NCluster=NCluster,DoPlot=DoPlot,ClusterMethod=CMethod)
    #SM=ClassSM.ClassSM(Osm,ReName=True,SaveNp=True,DoPlot=DoPlot,FromExt=Cat)
    SM.MakeREG()
    SM.Save()





if __name__=="__main__":
    read_options()
    main()
