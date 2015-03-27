#!/usr/bin/env python

#import matplotlib
#matplotlib.use('agg')

import time
import os
import numpy as np
import pyfits
import pylab
#import regrid

#from pyrap.images import image
import matplotlib.pyplot as mpl

import aplpy

import findrms
import rad2hmsdms

def convert(name,nameout="%s.png"):#,padding=1.4):


    a=pyfits.open(name)[0]
    rac,decc,npix,dpix=a.header["CRVAL1"],a.header["CRVAL2"],a.header["NAXIS1"],a.header["CDELT1"]


    H=a.header
    freq=H["CRVAL4"]

    # raobs,decobs,freq=a.header["OBSRA"],a.header['OBSDEC'],a.header['RESTFRQ']
    # raobs=H["CRVAL1"]
    # raobs=H["CRVAL2"]
    # strra=rad2hmsdms.rad2hmsdms(raobs,Type="ra",deg=True).replace(" ",":")
    # strdec=rad2hmsdms.rad2hmsdms(decobs,deg=True).replace(" ",".")

    try:
        bmaj,bmin=a.header["BMAJ"],a.header['BMIN']
        bmaj*=3600.
        bmin*=3600.
    except:
        bmaj,bmin=-1.,-1.

    date=a.header['DATE-OBS']


    # radius=abs(float(npix)*dpix)/2.
    # radius/=padding
    
    rms=findrms.findrms(a.data)
    print "rms=%f"%rms
    fig = mpl.figure(0,figsize=(17,17), dpi=200)
    #cmap='gist_gray'
    cmap='Greys'
    cmap='gray'


    D=a.data
    Np=1000
    nx,ny,_,_=a.data.shape
    indx=np.int64(np.random.rand(Np)*nx)
    indy=np.int64(np.random.rand(Np)*ny)
    rms=np.std(D[indx,indy,0,0])
    fig.clf()

    dx=0.#4
    dy=0.#85
    c=0.0#7
    dd=0.95-c
    subplot=[c,c,dd,dd]
    lmc = aplpy.FITSFigure(name, 
                           slices=[0,0], 
                           #subplot=subplot,
                           dimensions=[0,1], 
                           figure=fig , 
                           auto_refresh=False)#,downsample=1)
    lmc.show_colorscale(cmap='gray',stretch='linear',vmin=-3.*rms,vmax=np.max(D))#cmin,vmax=cmax)
    #lmc.recenter(rac,decc,radius)
    lmc.show_colorscale(cmap=cmap,stretch='linear',vmin=-3.*rms,vmax=np.max(D))#,vmin=-5*rms,vmax=50.*rms)#cmin,vmax=cmax)
    lmc.add_grid()
    lmc.grid.set_alpha(1)
    #lmc.grid.set_color('black')
    lmc.set_tick_labels_format(xformat='hh:mm',yformat='dd:mm')
    lmc.set_tick_color("black")
    mpl.draw() 
   #mpl.show()

    # if "%s" in nameout:
    #     nameout="%s.png"%name
    nameout=name+".pdf"
    #fig.savefig(nameout)
    lmc.save(nameout)#,dpi=100)
    #dico={"beam":(bmaj,bmin),"ra":strra,"dec":strdec,"freq":freq/1.e6,"date":date,"rms":rms}
    #return nameout,dico

if __name__=="__main__":
    import sys
    print sys.argv

    fin=sys.argv[1]
    if len(sys.argv)==3:
        pad=sys.argv[2]
    else:
        pad=1.4

    convert(fin,pad)
