from skimage import io as skio
import matplotlib.pyplot as plt
from skimage import data
from skimage.color import rgb2hsv
import numpy as np
import platform
import tempfile
import os


def dark_channel(im, patch):
    """ 
    im : array de l'image
    patch : hauteur du patch
    """

    M,N,a = np.shape(im)

    if patch%2 == 0:
        raise ValueError("Should be an odd number to center x")
    
    darkchannel = np.zeros((M,N))
    for i in range(M):
        for j in range(N):
            up = i-int( (patch-1) /2)
            down = i + int( (patch-1) /2)
            left = j-int( (patch-1) /2)
            right = j + int( (patch-1) /2)
            value = im[max(up,0):min(down+1,M), max(left,0):min(right+1,N),:]
            darkchannel[i,j] = np.min(value)
    return darkchannel

def atmosphere_light(im, dc, p):
    """
    im : array de l'image
    dc : darkchannel de l'image
    p : pourcentage de pixel 
    """
    
    Liste = []
    
    M,N = dc.shape
    onedc = dc.flatten() ## put in one dimension
    onedim = im.reshape(M*N,3) 
    indices_sorted = onedc.argsort()[::-1][:int(M * N * p)]  ##take highest valued pixel in the darkchannel
    
    for k in indices_sorted:
        Liste.append(onedim[k])
    
    array_pixels = np.array(Liste)

    max_r = np.max(array_pixels[:, 0])
    max_g = np.max(array_pixels[:, 1])
    max_b = np.max(array_pixels[:, 2])
    
    return np.array([max_r, max_g, max_b])

def transmission(im, A, omega, patch):
    """
    im : array de l'image
    A : atmosphere_light 
    omega : coefficient 
    patch : hauteur du patch
    """
    
    return 1 - omega * dark_channel(im/A,patch)

def get_atmosphere(I, darkch, p):
    """Get the atmosphere light in the (RGB) image data.

    Parameters
    -----------
    I:      the M * N * 3 RGB image data ([0, L-1]) as numpy array
    darkch: the dark channel prior of the image as an M * N numpy array
    p:      percentage of pixels for estimating the atmosphere light

    Return
    -----------
    A 3-element array containing atmosphere light ([0, L-1]) for each channel
    """
    # reference CVPR09, 4.4
    M, N = darkch.shape
    flatI = I.reshape(M * N, 3)
    flatdark = darkch.ravel()
    searchidx = (-flatdark).argsort()[:int(M * N * p)]  # find top M * N * p indexes
    # return the highest intensity for each channel
    return np.max(flatI.take(searchidx, axis=0), axis=0)

def haze_remove(im, A, t, t0):
    reshaped_t = t[:, :, np.newaxis].repeat(3, axis=2)
    im = im/255
    A = A/255
    radiance= (im-A)/reshaped_t + A
    
    return radiance

def depth(t, beta):
    """
    im : image intensity
    beta : scattering coefficient of the atmosphere
    """
    depthmap = np.array(np.shape(t))
    depthmap = -(1/beta)*np.log2(t)
    return depthmap