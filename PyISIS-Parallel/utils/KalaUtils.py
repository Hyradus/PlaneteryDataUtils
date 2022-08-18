#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Title: 
@author: @author: Giacomo Nodjoumi g.nodjoumi@jacobs-unversity.de



Created on Mon Sep 28 18:45:02 2020
@author: @author: Giacomo Nodjoumi g.nodjoumi@jacobs-unversity.de
"""
import os
os.environ["ISISROOT"]="/opt/conda/envs/isis/"
os.environ["ISISDATA"]="/isis/data"
from kalasiris import lronac2isis, lrowac2isis, lronaccal, lrowaccal, chan1m32isis, cam2map, spiceinit, lronacecho, stretch
from osgeo import gdal
from osgeo.gdal import gdalconst
import rasterio as rio
import time
import subprocess

def RAWtoL0(inst, src, L0):
    inst(src, to=L0)    

def L0toL1(inst, dst_basename, L0, L1):
    inst(L0,to=L1)
    os.remove(L0)

def L1toL1nacecho(L1,L1echo):
    lronacecho(L1, to=L1echo)
    os.remove(L1)
    
def L1toL2(maptemplate, L1, L2):
    #res=GetRes(maptemplate)
    cam2map(L1, to=L2, PIXRES='MAP', map=maptemplate)
    os.remove(L1)

    
def L2toStd(L2cub, L2std, byte):
    opts = f' -mask none'
    
    nodata=rio.open(L2cub).nodata #using rio since src_map.GetMetadata() return empty
    if byte.lower() in ['yes','y','ye']:
        nodata=0
        opts = opts+f' -ot Byte  -scale -a_nodata {nodata}'            

    try:
        src_map = gdal.Open(L2cub)
        
        gdal.Translate(L2std, src_map, options=opts)#,scaleParams=[])
        return 'Done'
        #os.remove(dst_lev2)
    except Exception as e:
        return(e)     




def lro(src, dst_basename, maptemplate, oxt, cam, byte):
    L0 = dst_basename+'_lev0.cub'        
    L1 = dst_basename+'_lev1.cub'                
    L1echo = dst_basename+'_lev1echo.cub'
    L2 = dst_basename+'_lev2.cub'
    L2std = dst_basename+'_lev2.'+oxt
    try:
        if os.path.isfile(L2std):
            print('File exists')
        else:
            L2 = L2std.split(oxt)[0]+'cub'
            if os.path.isfile(L2):
                L2toStd(L2, L2std, byte)
            else:      
                if os.path.isfile(L1echo):                
                    L1toL2(maptemplate, L1echo, L2)
                    L2toStd(L2, L2std, byte)
                else:                
                    if os.path.isfile(L1):
                        if cam in ['nac']:
                            L1toL1nacecho(L1, L1echo)
                            L1toL2(maptemplate, L1echo, L2)
                        else:
                            L1toL2(maptemplate, L1, L2)
                        L2toStd(L2, L2std, byte)
                    else:                                           
                        if os.path.isfile(L0):
                            if cam in ['nac']:
                                L0toL1(lronaccal, dst_basename, L0, L1)
                                L1toL1nacecho(L1, L1echo)
                                L1toL2(maptemplate, L1echo, L2)
                            else:
                                L0toL1(lrowaccal, dst_basename, L0, L1)                            
                                L1toL2(maptemplate, L1, L2)                                                
                            L2toStd(L2, L2std, byte)
                        else:
                            if cam in ['nac']:
                                RAWtoL0(lronac2isis, src, L0)
                            else:
                                RAWtoL0(lrowac2isis,src, L0)
                            init = None
                            while init == None:
                                try:
                                    print('Spiceinit')
                                    spiceinit(L0)#, web='yes')
                                    init = 'Done'
                                    print(init)
                                except subprocess.CalledProcessError as err:
                                    print('Had an ISIS error:')
                                    print(' '.join(err.cmd))
                                    print(err.stdout)
                                    print(err.stderr)
                                    raise err

                            if cam in ['nac']:
                                L0toL1(lronaccal, dst_basename, L0, L1)
                            else:
                                L0toL1(lrowaccal, dst_basename, L0, L1)                        
                            if cam in ['nac']:
                                L1toL1nacecho(L1, L1echo)
                                L1toL2(maptemplate, L1echo, L2)
                            else:
                                L1toL2(maptemplate, L1, L2)                                                
                            L2toStd(L2, L2std, byte)
    except subprocess.CalledProcessError as err:
                        print('Had an ISIS error:')
                        print(' '.join(err.cmd))
                        print(err.stdout)
                        print(err.stderr)
                        raise err
        
                        



def m3L1(src, dst_basename,maptemplate, oxt, cam, byte):
    src_basename=src.split('_L1B.LBL')[0]
    L1_L1B=src_basename+'_L1B.LBL'
    L1_LOC=src_basename+'_LOC.IMG'
    L1_OBS=src_basename+'_OBS.IMG'
    L1 = dst_basename+'_lev1.cub'                        
    L2str = dst_basename+'_lev2stretch.cub'        
    L2 = dst_basename+'_lev2.cub'
    L2std = dst_basename+'_lev2.'+oxt
    
    try:
        if os.path.isfile(L2std):
            print('File exists')
        else:
            L2 = L2std.split(oxt)[0]+'cub'
            #if os.path.isfile(L2str):
                #L2toStd(L2str, L2std, byte)
            #else:            
            if os.path.isfile(L2):
                #null=rio.open(L2).nodata
                #if byte.lower() in ['y','yes','ye']:
                #    null=0
                #stretch(L2, to=L2str, NULL=null)
                L2toStd(L2, L2std, byte)               
            else:
                if os.path.isfile(L1):                    
                    L1toL2(maptemplate, L1, L2)
                    #null=rio.open(L2).nodata
            #        if byte.lower() in ['y','yes','ye']:
            #            null=0
            #        stretch(L2, to=L2str, NULL=null)
                    L2toStd(L2, L2std, byte)

                else:                                            
                    chan1m32isis(L1_L1B, loc=L1_LOC, obs=L1_OBS, to=L1)
                    init = None
                    while init == None:
                        print('Spiceinit')
                        spiceinit(L1)#, web='yes')
                        init = 'Done'
                        print(init)
                    print('Mapping')                        
                    L1toL2(maptemplate, L1, L2)                    
                    #null=rio.open(L2).nodata
                    #if byte.lower() in ['y','yes','ye']:
                    #    null=0
                    #stretch(L2, to=L2str, NULL=null)
                    print('Exporting')
                    L2toStd(L2, L2std, byte)
    except subprocess.CalledProcessError as err:
                                print('Had an ISIS error:')
                                print(' '.join(err.cmd))
                                print(err.stdout)
                                print(err.stderr)
                                raise err
    

        
def equalizer(L2list):
    L2equ = [cub.split('.cub')[0]+'_equ.cub' for cub in L2list]
    isis.equalizer(L2list, to=L2equ)
    return(L2equ)


def GetRes(maptemplate):
    line=check_if_string_in_file(maptemplate,'PixelResolution')
    for val in line.split(' '):
        try:
            float(val)
            return(float(val))
            break
        except:        
            continue
            
            
def check_if_string_in_file(file_name, string_to_search):
    ### source https://thispointer.com/python-search-strings-in-a-file-and-get-line-numbers-of-lines-containing-the-string/
    """ Check if any line in the file contains given string """
    # Open the file in read only mode
    with open(file_name, 'r') as read_obj:
        # Read all lines in the file one by one
        for line in read_obj:
            # For each line, check if line contains the string
            if string_to_search in line:
                return line
    return False            