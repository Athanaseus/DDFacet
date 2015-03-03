from multiprocessing import sharedctypes
import numpy as np
import numpy
import multiprocessing
import ctypes
import ClassTimeIt
from numpy import ctypeslib


def NumpyToShared(lA):
    Aout=[]
    for obj in lA:
        if type(obj)==np.ndarray:
            Aout.append(SingleNumpyToShared(obj))
        elif type(obj)==tuple:
            A0,A1=obj
            Aout.append([SingleNumpyToShared(A0),SingleNumpyToShared(A1)])

            
    return Aout

def SharedToNumpy(lA):
    Aout=[]
    for obj in lA:
        print
        print obj
        if hasattr(obj,"IS_SHARED_ARRAY"):
            B=SingleSharedToNumpy(obj)
            print "ARRAY"
            print B
        elif (type(obj)==np.ndarray):
            B=obj
        elif (type(obj)==tuple)|(type(obj)==list):
            A0,A1=obj
            B=[SingleSharedToNumpy(A0),SingleSharedToNumpy(A1)]
            print "TUPLE"
            print B
        elif obj==None:
            B=None
            print "None"
            print B
        Aout.append(B)

    return Aout


def SingleNumpyToShared(A):

    

    size = A.size
    shape = A.shape
    sizeTot=size
    dtype=A.dtype
    if dtype==np.float32:
        DicoType={"ctype":"f"}
    elif dtype==np.float64:
        DicoType={"ctype":"d"}
    elif dtype==np.complex128:
        DicoType={"ctype":"d"}
    elif dtype==np.complex64:
        DicoType={"ctype":"f"}
    elif dtype==np.bool:
        DicoType={"ctype":"i"}
    elif dtype==np.int32:
        DicoType={"ctype":"i"}
    
    DicoType["nptype"]=dtype
        
    DicoType["ComplexMode"]=False
    if "complex" in str(A.dtype):
        sizeTot*=2
        DicoType["ComplexMode"]=True

    S_ctypes = sharedctypes.RawArray(DicoType["ctype"], sizeTot)
    #As = numpy.frombuffer(S_ctypes, dtype=DicoType["nptype"], count=size)
    As = ctypeslib.as_array(S_ctypes)

    if DicoType["ComplexMode"]:
        As[0::2]=A.reshape((size,)).real[:]
        As[1::2]=A.reshape((size,)).imag[:]
        #As[0:size]=A.reshape((size,)).real[:]
        #As[size::]=A.reshape((size,)).imag[:]
    else:
        As[:]=A.reshape((size,))[:]

    S_ctypes.shape=shape
    S_ctypes.DicoType=DicoType
    S_ctypes.IS_SHARED_ARRAY=True

    return S_ctypes

def SingleSharedToNumpy(S_ctypes):
    if type(S_ctypes)==np.ndarray: return S_ctypes
    if S_ctypes==None: return None
    S = ctypeslib.as_array(S_ctypes)
    if S_ctypes.DicoType["ComplexMode"]:
        S = S.view(S_ctypes.DicoType["nptype"])
    S=S.reshape(S_ctypes.shape)
    #S.shape = S_ctypes.shape
    return S

def testComplex():
    At=np.random.randn(4,4)+1j*np.random.randn(4,4)

    #for dtype in [np.float32, np.float64, np.complex64, np.complex128]:
    for dtype in [np.float64, np.complex128, np.float32, np.complex64]:
        A=dtype(At)
        As=NumpyToShared(A)
        npAs=SharedToNumpy(As)
        print A-npAs