# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 16:07:19 2019

@author: NASHEED
"""

import numpy as np
from datetime import datetime
from PIL import Image
import logging

# Basic Logger
logging.basicConfig(filename = "./logfile.log", level = logging.INFO)

def NormalizeStaining(img, saveFile=None, Io=240, alpha=1, beta=0.15, SavePath= None): 
    ''' Normalize staining appearance of H&E stained images
            
        Input:
            I: RGB input image
            Io: (optional) transmitted light intensity
            
        Output:
            Inorm: normalized image
            H: hematoxylin image
            E: eosin image
        
        Reference: 
            A method for normalizing histology slides for quantitative analysis. M.
            Macenko et al., ISBI 2009
    '''
             
    HERef = np.array([[0.5626, 0.2159],
                      [0.7201, 0.8012],
                      [0.4062, 0.5581]])
        
    maxCRef = np.array([1.9705, 1.0308])
    try:
        # Define height and width of image
        h, w, c = img.shape
        
        # Reshape image
        rimg = np.reshape(img.astype(np.float), (-1,3))
        #logging.info(str(datetime.today()) + ' : Reshaped image')
        
        # Calculate optical density
        OD = -np.log((rimg+1)/Io)
        #logging.info(str(datetime.today()) + ' : Calculated optical density')
        
        # Remove transparent pixels
        ODhat = np.array([i for i in OD if not any(i<beta)])
        #logging.info(str(datetime.today()) + ' : Removed transparent pixels')
            
        # Compute eigenvectors
        eigvals, eigvecs = np.linalg.eigh(np.cov(ODhat.T))
        #logging.info(str(datetime.today()) + ' : Computed eigenvectors')
    
    except Exception as e:
        logging.exception(str(datetime.today()) + ' : Exception - ' + str(e.with_traceback))

    #eigvecs *= -1
    
    # Project on the plane spanned by the eigenvectors corresponding to the two 
    # Largest eigenvalues    
    That = ODhat.dot(eigvecs[:,1:3])
    
    phi = np.arctan2(That[:,1],That[:,0])
    
    minPhi = np.percentile(phi, alpha)
    maxPhi = np.percentile(phi, 100-alpha)
    
    vMin = eigvecs[:,1:3].dot(np.array([(np.cos(minPhi), np.sin(minPhi))]).T)
    vMax = eigvecs[:,1:3].dot(np.array([(np.cos(maxPhi), np.sin(maxPhi))]).T)
    
    # A heuristic to make the vector corresponding to hematoxylin first and the 
    # One corresponding to eosin second
    if vMin[0] > vMax[0]:
        HE = np.array((vMin[:,0], vMax[:,0])).T
    else:
        HE = np.array((vMax[:,0], vMin[:,0])).T
    
    # Rows correspond to channels (RGB), columns to OD values
    Y = np.reshape(OD, (-1, 3)).T
    
    # Determine concentrations of the individual stains
    C = np.linalg.lstsq(HE,Y, rcond=None)[0]
    
    # Normalize stain concentrations
    maxC = np.array([np.percentile(C[0,:], 99), np.percentile(C[1,:],99)])
    C2 = np.array([C[:,i]/maxC*maxCRef for i in range(C.shape[1])]).T
    
    # Recreate the image using reference mixing matrix
    Inorm = np.multiply(Io, np.exp(-HERef.dot(C2)))
    Inorm[Inorm>255] = 254
    Inorm = np.reshape(Inorm.T, (h, w, 3)).astype(np.uint8)  
    
    # Unmix hematoxylin and eosin, uncomment if nessessary
#    H = np.multiply(Io, np.exp(np.expand_dims(-HERef[:,0], axis=1).dot(np.expand_dims(C2[0,:], axis=0))))
#    H[H>255] = 254
#    H = np.reshape(H.T, (h, w, 3)).astype(np.uint8)
#    
#    E = np.multiply(Io, np.exp(np.expand_dims(-HERef[:,1], axis=1).dot(np.expand_dims(C2[1,:], axis=0))))
#    E[E>255] = 254
#    E = np.reshape(E.T, (h, w, 3)).astype(np.uint8)
    
    if saveFile is not None:
        Image.fromarray(Inorm).save(SavePath+saveFile) # Saving the normalized images
        
#        Use the two lines below if nessessary
#        Image.fromarray(H).save(cf.NormImagePath+saveFile+'_H')
#        Image.fromarray(E).save(cf.NormImagePath+saveFile+'_E')

#    return Inorm, H, E
        
    ''' This section resizes the above generated image 
        from 2048x1536 to 512×384 and saves it
        Alternatively 1024×768 can be used
    '''
    
    ResizedImg=Image.open(SavePath+saveFile)
    # Resizing using anti- aliasing filter
    ResizedImg=ResizedImg.resize((512,384),Image.ANTIALIAS) 
    ResizedImg.save(SavePath+saveFile,optimize=True,quality=95)

