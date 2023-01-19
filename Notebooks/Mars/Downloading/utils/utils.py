#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: giacomo.nodjoumi@hyranet.info - g.nodjoumi@jacobs-university.de
"""
from affine import Affine
import geopandas as gpd
import holoviews as hv
from holoviews import opts
hv.extension('bokeh', logo=False)
from holoviews.plotting.links import RangeToolLink
import ipywidgets as widgets
import itertools
import math
import numpy as np
import numpy.ma as ma
import os
from owslib.wcs import WebCoverageService
import pandas as pd
import pathlib
from pathlib import Path
import pds4_tools
from PIL import Image
import psutil
from pyproj import CRS, Transformer
from rasterio.coords import BoundingBox as BB
import rasterio as rio
from rasterio.mask import mask
from rasterio.plot import reshape_as_image
import re
import rioxarray
import shapely
import shapely.geometry
from shapely.geometry import box, Polygon, Point
from shapely.geometry import mapping
from shapely import affinity
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
import urllib.request as ulr

# CRS Declaration

MARS2000 = CRS.from_wkt('GEOGCS["Mars 2000",DATUM["D_Mars_2000",SPHEROID["Mars_2000_IAU_IAG",3396190.0,169.89444722361179]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]]')
DST_CRS = CRS.from_wkt('PROJCS["Mars_Equidistant_Cylindrical",GEOGCS["Mars 2000",DATUM["D_Mars_2000",SPHEROID["Mars_2000_IAU_IAG",3396190.0,169.89444722361179]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Equidistant_Cylindrical"],PARAMETER["False_Easting",0],PARAMETER["False_Northing",0],PARAMETER["Central_Meridian",0],PARAMETER["Standard_Parallel_1",0],UNIT["Meter",1]]')
DST_CRS_S = CRS.from_wkt('PROJCS["Mars_South_Pole_Stereographic",GEOGCS["Mars 2000",DATUM["D_Mars_2000",SPHEROID["Mars_2000_IAU_IAG",3396190.0,169.89444722361179]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Stereographic"],PARAMETER["False_Easting",0],PARAMETER["False_Northing",0],PARAMETER["Central_Meridian",0],PARAMETER["Scale_Factor",1],PARAMETER["Latitude_Of_Origin",-90],UNIT["Meter",1]]')
DST_CRS_N = CRS.from_wkt('PROJCS["Mars_North_Pole_Stereographic",GEOGCS["Mars 2000",DATUM["D_Mars_2000",SPHEROID["Mars_2000_IAU_IAG",3396190.0,169.89444722361179]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Stereographic"],PARAMETER["False_Easting",0],PARAMETER["False_Northing",0],PARAMETER["Central_Meridian",0],PARAMETER["Scale_Factor",1],PARAMETER["Latitude_Of_Origin",90],UNIT["Meter",1]]')
                                 

def get_paths(PATH, ixt):
    import re
    import fnmatch
    # os.chdir(PATH)
    ext='*.'+ixt
    chkCase = re.compile(fnmatch.translate(ext), re.IGNORECASE)
    files = [PATH+'/'+f for f in os.listdir(PATH) if chkCase.match(f)]
    return(files)
    
    
    
def scs_converter(acquisition_folder, track):   
    sims = pds4_tools.read(f"./{acquisition_folder}{track}_sim.xml")
    comboSim = sims["Combined_Clutter_Simulation"].data

    # Log scale image
    comboScale = np.log10(comboSim + 1e-30)

    # Get valid (actually simulated) values
    comboValid = comboScale[comboSim != 0]

    # Make linear mapping from image values to 0 -255
    p10 = np.percentile(comboValid, 10)
    m = 255 / (comboValid.max() - p10)
    b = -p10 * m

    # Apply map, clip values below minimum
    comboMap = (m * comboScale) + b
    comboMap[comboMap < 0] = 0
    width = comboMap.shape[1]
    # Save browse image
    comboMap = comboMap.astype(np.uint8)
    comboImg = Image.fromarray(comboMap)
    comboImg.save(f"./{acquisition_folder}/s_{track}_sim.png")
    return(comboMap)

def track_footprint(acquisition, sharad_coverage, base_image):
    sharad_gdf = gpd.read_file(sharad_coverage)
    track_name, _ = Path(acquisition).name.split('_tiff')
    sub_gdf = sharad_gdf[sharad_gdf['ProductId'].str.contains(track_name, na=False, case=False)]
    geom = sub_gdf.iloc[0].geometry    
    bbox = box(geom.boundary.geoms[0].xy[0][0], geom.boundary.geoms[0].xy[1][0], geom.boundary.geoms[1].xy[0][0], geom.boundary.geoms[1].xy[1][0])
    if sub_gdf.iloc[0]['MinLat']<=-60:
        #sub_gdf = sub_gdf.to_crs(DST_CRS_S)
        dst_crs=DST_CRS_S
    elif sub_gdf.iloc[0]['MinLat']>=60:
        #sub_gdf = sub_gdf.to_crs(DST_CRS_N)
        dst_crs=DST_CRS_N
    else:        
        #sub_gdf = sub_gdf.to_crs(DST_CRS)
        dst_crs=DST_CRS
    #savename, out_image = basemap_extractor(base_image, track_name, acquisition, bbox, dst_crs)
    #gdf = gpd.GeoDataFrame([savename], geometry=geom,crs=rr.crs)
    #rr = rio.open(savename)
    gdf=gpd.GeoDataFrame([[os.path.basename(acquisition),geom]],columns=['Track','geometry'],crs=dst_crs)
    gdf.to_file(f'{acquisition}_.gpkg', driver='GPKG')

    #if gdf.iloc[0]['MinLat']<=-60:
    #    gdf = gdf.to_crs(DST_CRS_S)
    #elif gdf.iloc[0]['MinLat']>=60:
    #    gdf = gdf.to_crs(DST_CRS_N)
    #else:        
    #    gdf = gdf.to_crs(DST_CRS)

    return( geom, out_image,gdf)#.iloc[0]['geometry'].length)

def wcs_get(wcs_url, layer, bbox, savename, resx=0.03, resy=0.03):    
    wcs = WebCoverageService(wcs_url, version='1.0.0')
    layerid = f'Mars:{layer}'
    temp = wcs[layerid]
    format_wcs = 'GeoTIFF'
    crs_wcs = temp.boundingboxes[0]['nativeSrs'] # Coordinate system    
    #width = math.ceil(plot_size/((bbox.top-bbox.bottom)/(bbox.right-bbox.left)))
    output = wcs.getCoverage(identifier=layerid, crs=crs_wcs, bbox=bbox, format=format_wcs, resx=resx, resy=resy)#, width=width, height=plot_size)
    with open(savename, 'wb') as f:
        f.write(output.read())
    

def track_prep(sharad_gdf, acquisition, acquisition_folder, track, wcs_url, dem_layerid, bmap_layerid, plot_size):        
    track_name, _ = Path(acquisition).name.split('_tiff')
    sub_gdf = sharad_gdf[sharad_gdf['ProductId'].str.contains(track_name, na=False, case=False)]  
    geom = sub_gdf.iloc[0].geometry  
    sub_gdf.to_file(f'{acquisition_folder}/{track_name}_footprint.gpkg', driver='GPKG')
    bounding_box= BB(min(geom.xy[0]), min(geom.xy[1]), max(geom.xy[0]), max(geom.xy[1]))
    # define basemap and dem filename
    bmap_savename = f"{os.path.dirname(acquisition)}/{bmap_layerid}-crop_track-{track}.tiff"
    dem_savename = f"{os.path.dirname(acquisition)}/{dem_layerid}-crop_track-{track}.tiff"
    # check if already downloaded and download if missing
    map_error = None
    if not os.path.isfile(bmap_savename):        
        try:           
            wcs_get(wcs_url, bmap_layerid, bounding_box, bmap_savename, resx=0.03, resy=0.03)
        except Exception as e:
            map_error = e
            bmap_savename = None
            pass
    dem_error = None
    if not os.path.isfile(dem_savename):

        try:           
            wcs_get(wcs_url, dem_layerid, bounding_box, dem_savename, resx=0.05, resy=0.05)
        except Exception as e:
            dem_error = e
            dem_savename = None
            pass
    return (bmap_savename, dem_savename, geom, sub_gdf, map_error, dem_error)

def basemap_extractor(base_image_path, track_name, acquisition, bbox, dst_crs):
    #base_image_path =  f'./Data/Basemap/{base_image}'
    with rio.open(base_image_path) as src:
        out_image, out_transform = mask(src, [bbox], crop=True)
        out_meta = src.meta
        out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "crs":dst_crs,
                     "transform": out_transform})
        savename= f"{os.path.dirname(acquisition)}/{Path(base_image_path).name.split('.tif')[0]}_cropped_{track_name}.tiff"
        with rio.open(savename, "w", **out_meta) as dest:
            dest.write(out_image)
        return(savename, out_image)
    
    
    
    #rotated_geom = affinity.rotate(geom, 90)
def data_prep(acquisition, comboMap, basemap_image, geom):
    acq = Image.open(acquisition)
    #acquisition_bin = acquisition.split('_tiff')[0]+'_rgram.img'
    #basemap = reshape_as_image(out_image)
    width= comboMap.shape[1]
    #img = Image.open(savename)
    #img.thumbnail((width, width))
    #basemap_rot = np.rot90(img)
    #basemap_rot = reshape_as_image(basemap_rot)
    max_width = np.asarray(acq).shape[1]
    max_height = np.asarray(acq).shape[0]
    #acq_array=np.asarray(acq)
    #left=0
    #bottom=acq_array.shape[0]*-1
    #right=acq_array.shape[1]
    #top=0#acq_array.shape[0]
    #rdr_bounds = (left,bottom,right,top)
    #basemap_bounds = (0,basemap_rot.shape[0],basemap_rot.shape[1],0)
    #basemap_bounds = (0,basemap.shape[0],basemap.shape[1],0)
    er = None
    try:
        im = Image.open(basemap_image)
        im1 = im.rotate(90, expand=1)
        im1=im1.resize((math.ceil(geom.length//1000),int(im1.size[1]/im1.size[0]*math.ceil(geom.length//1000))))
        basemap_bounds = (0,im1.size[1],im1.size[0],0)
    except Exception as e:
        basemap_bounds = None
        im = None
        im1 = None
        er=e
        pass
    rdr_bounds = (0,max_height*-0.0375,geom.length//1000,0)
    return(im, im1, acq, rdr_bounds, basemap_bounds, max_width, max_height,er)


def roi_prep(roi_image, rect):
    im = Image.open(roi_image)
    im1 = im.rotate(90, expand=1)
    #im1=im1.resize((max_width,int(im1.size[1]/im1.size[0]*max_width)))
    max_width = rect[0][2]-rect[0][0]
    max_height = rect[0][3]-rect[0][1] 
    #print(max_width, max_height)
    im1=im1.resize((max_width,int(im1.size[1]/im1.size[0]*max_width)))
    return(im1)
    
    
    
def coord_label_prep(basemap_rot, geom, xamount, yamount):
    max_width, max_height = basemap_rot.size
    #xtick = list(np.arange(0,float(max_width),1))
    xtick = [int(a) for a in (list(np.arange(0,float(max_width),1)))]
    #ytick = list(np.arange(0,max_height,1))
    ytick = [int(a) for a in (list(np.arange(0,float(max_height),1)))]
    coord_xtick = np.linspace(geom.xy[1][0],geom.xy[1][-1], xtick[-1])
    coord_xtick = [round(x,5) for x in coord_xtick]
    coord_ytick = np.linspace(geom.xy[0][0],geom.xy[0][-1], ytick[-1])
    coord_ytick = [round(y,5) for y in coord_ytick]
    mapped_x = dict(list(zip(xtick,coord_xtick)))
    mapped_y = dict(list(zip(ytick,coord_ytick)))
    red_xtick = list(np.arange(0,max_width,int(max_width/xamount)-1))
    red_ytick = list(np.arange(0,max_height,int(max_height/yamount)-1))
    new_xticks = [(int(k),str(mapped_x[k])) for k in red_xtick]
    new_yticks = [(int(k),str(mapped_y[k])) for k in red_ytick]
    return(new_xticks,new_yticks)

def rdr_label_prep(image_width, image_height, max_x, max_y, geom, xamount, yamount):
    max_x=max_x//1000
    xtick = [int(a) for a in (list(np.arange(0,float(image_width),1)))]
    ytick = [int(a) for a in (list(np.arange(0,float(image_height),1)))]
    rdr_xtick = np.linspace(0,max_x,xtick[-1])
    rdr_xtick = [int(x)for x in rdr_xtick]
    rdr_ytick = np.linspace(0,max_y,ytick[-1])
    rdr_ytick = [int(y) for y in rdr_ytick]
    mapped_x = dict(list(zip(xtick,rdr_xtick)))
    mapped_y = dict(list(zip(ytick,rdr_ytick)))
    red_xtick = list(np.arange(0,image_width, int(image_width/xamount)-1))
    red_ytick = list(np.arange(0,image_height, int(image_height/yamount-1)))
    new_xticks = [(int(k),str(mapped_x[k])) for k in red_xtick]
    new_yticks = [(int(-1*k),str(round(mapped_y[k]*0.0375,3))) for k in red_ytick[0:len(red_ytick)-1]]

    return(new_xticks,new_yticks, mapped_y, rdr_ytick, red_ytick)

def PowyFormatter(value):    
    #return str((value*0.137))# +' μs')
    return(f'{value*0.137:.2f}')

def yFormatter(value):
    return str(value*-1)# +' μs')



def plot_prep(track, plot_size, acq, comboMap, basemap_rot, coord_new_xticks, coord_new_yticks, rdr_bounds, basemap_bounds, foot_points_df, rect, dem_profile, scs_pow_profile, acq_pow_profile, geom_gdf, show_roi, roi_image):
    xdim = hv.Dimension('Distance along track (Km)', range=(0, math.ceil(geom_gdf.to_crs(DST_CRS).iloc[0]['geometry'].length//1000)))
    grid_style = {'grid_line_color': 'black', 'grid_line_width': 1.5,
                  'minor_xgrid_line_color': 'lightgray',}
    plot_rgram = hv.Image(np.asarray(acq), bounds=rdr_bounds).opts(yformatter=yFormatter,xrotation=90,yrotation=0,xlabel='Distance along track (Km)',ylabel='TWT (μs)',
                                                                    cmap='viridis',width=plot_size, height=int((acq.size[1]*plot_size/acq.size[0])//2),
                                                                    gridstyle=grid_style, show_grid=True, title=f'Acquisition: {track}')
    plot_acq_db = hv.Image(np.asarray(acq)*0.137, bounds=rdr_bounds).opts(yformatter=yFormatter,xrotation=90,yrotation=0,xlabel='Distance along track (Km)',ylabel='TWT (μs)',
                                                                    cmap='viridis',width=plot_size, height=int((acq.size[1]*plot_size/acq.size[0])//2),
                                                                    gridstyle=grid_style, show_grid=True, title=f'Acquisition: {track}')
        
    plot_scs = hv.Image(np.asarray(comboMap), bounds=rdr_bounds).opts(yformatter=yFormatter,xrotation=90,yrotation=0,xlabel='Distance along track (Km)',ylabel='TWT (μs)',
                                                                        cmap='viridis', width=plot_size, height=int((acq.size[1]*plot_size/acq.size[0])//2),
                                                                        gridstyle=grid_style, show_grid=True, title=f'Clutter Simulation for track: {track}')    
    plot_scs_db = hv.Image(np.asarray(comboMap)*0.137, bounds=rdr_bounds).opts(yformatter=yFormatter,xrotation=90,yrotation=0,xlabel='Distance along track (Km)',ylabel='TWT (μs)',
                                                                        cmap='viridis', width=plot_size, height=int((acq.size[1]*plot_size/acq.size[0])//2),
                                                                        gridstyle=grid_style, show_grid=True, title=f'Clutter Simulation for track: {track}')
    
    plot_map = hv.Image(np.asarray(basemap_rot), bounds=basemap_bounds).opts(xticks=coord_new_xticks,yticks=coord_new_yticks,xrotation=45,yrotation=0,xlabel='Latitude',ylabel='Longitude',
                                                                 cmap='viridis',axiswise=True,width=plot_size*3, height=(basemap_rot.size[1]*plot_size//basemap_rot.size[0])*3,
                                                                 gridstyle=grid_style, show_grid=True, title='Track footprint and area of interest')
    plot_foot = hv.Curve(foot_points_df, 'lon','lat').opts(color='red',width=plot_size*2, height=(basemap_rot.size[1]*plot_size//basemap_rot.size[0])*2)
    plot_acq_pow = hv.Curve(acq_pow_profile, xdim,'Backscatter Power (dB)',label='Acqusition').opts(yformatter=PowyFormatter,title=f'Max Backscatter Power for track: {track}',color='red',width=plot_size, line_width=1)#, height=basemap_rot.size[1]*plot_size//basemap_rot.size[0])
    plot_scs_pow = hv.Curve(scs_pow_profile, xdim,'Backscatter Power (dB)', label='SCS').opts(yformatter=PowyFormatter,color='blue',width=plot_size, line_width=1)
    dem_profile = [float(x) for x in dem_profile[1::]]
    plot_dem_profile = hv.Curve(dem_profile,xdim,'Elevation (m)').opts(color='green',width=plot_size, title='MOLA HRSC DEM Profile', line_width=1)
    if show_roi in ['y','Y']:
        try:
            plot_rect = hv.Rectangles(rect).opts(alpha=0.2,color='red',axiswise=False)
        except Exception as e:
            print(e)
            plot_rect=None
            pass
    else:
        plot_rect = None
    plot_roi = None #temporary WIP
    return(plot_rgram, plot_scs, plot_map, plot_foot, plot_rect, plot_roi, plot_dem_profile, plot_scs_pow, plot_acq_pow, plot_acq_db, plot_scs_db)

def get_poi_geom(geom_file,ID):
    import geopandas as gpd
    poi_geom = gpd.read_file(geom_file)
    return(poi_geom[poi_geom['id']==ID].iloc[0]['geometry'])
#xticks=coord_new_xticks,yticks=coord_new_yticks,    



def foot_plot(savename, geom, basemap_rot):
    rr = rio.open(savename)
    gt = rr.transform
    a, b, c, d, e, f = gt[0:6]
    geo_points = list(geom.coords)
    points = [(((x - c) / a),((y - f) / e)) for x,y in geo_points]
    dst_width, dst_height = basemap_rot.size
    height, width = rr.shape
    x0,y0 = points[0]
    x1,y1 = points[-1]
    new_x0 = int(x0*dst_height/width)
    new_x1 = int(x1*dst_height/width)
    new_y0 = int(y0*dst_width/height)
    new_y1 = int(y1*dst_width/height)
    #foot = hv.Curve([(new_y0,new_x0),(new_y1,new_x1)])
    new_points = [(int(x*dst_height/width),int(y*dst_width/height)) for x,y in points]    
    #[(new_y0,new_x0),(new_y1,new_x1)]
    
    return(pd.DataFrame(new_points,columns=['lat','lon']))

#foot_points_df, points = foot_plot(savename, geom, basemap_rot)

def foot_plot2(savename, geom, basemap_rot):
    rr = rio.open(savename)
    gt = rr.transform
    a, b, c, d, e, f = gt[0:6]
    geo_points = list(geom.exterior.coords)
    points = [(((x - c) / a),((y - f) / e)) for x,y in geo_points]
    dst_height, dst_width = basemap_rot.size
    height, width = rr.shape
    x0,y0 = points[0]
    x1,y1 = points[-1]
    #new_x0 = (x0*dst_height/width)
    #new_x1 = (x1*dst_height/width)
    #new_y0 = (y0*dst_width/height)
    #new_y1 = (y1*dst_width/height)
    #foot = hv.Curve([(new_y0,new_x0),(new_y1,new_x1)])
    new_points = [(round(x*dst_width/width),round(y*dst_height/height)) for x,y in points]    
    return(pd.DataFrame(new_points,columns=['lat','lon']))

def coord_transformer(src_crs, dst_crs, x,y):    
    transformer = Transformer.from_crs(src_crs,dst_crs)
    return(transformer.transform(x,y))    

def rect_calc(bounding_box, savename, basemap_rot):    
    box_geom = box(*bounding_box)
    #geom_rot = shapely.affinity.rotate(box_geom, 90, origin='centroid')
    roi_df = foot_plot2(savename, box_geom, basemap_rot)
    #rect = [(roi_df.iloc[1]['lon'],roi_df.iloc[3]['lat'],roi_df.iloc[3]['lon'],roi_df.iloc[1]['lat'])]
    return( [(roi_df.iloc[1]['lon'],roi_df.iloc[3]['lat'],roi_df.iloc[3]['lon'],roi_df.iloc[1]['lat'])])



# derived from https://stackoverflow.com/questions/62283718/how-to-extract-a-profile-of-value-from-a-raster-along-a-given-line
def dem_profiler(xarr, line, n_samples):
    profile = []

    for i in range(n_samples):
        # get next point on the line
        point = line.interpolate(i / n_samples - 1., normalized=True)
        # access the nearest pixel in the xarray
        value = xarr.sel(x=point.x, y=point.y, method="nearest").data
        profile.append(value)
        
    return(np.where(np.isnan(profile), ma.array(profile, mask=np.isnan(profile)).mean(axis=0), profile))


def power_profiler(radargram):
    pow_prof = []
    try:
        rdrg_width = radargram.shape[1]
    except:
        rdrg_width =radargram.size[0]
        radargram = np.array(radargram)
    for i in range(rdrg_width):
        pow_prof.append(radargram[:,i].max())
    return(pow_prof)

def get_poly(bounding_box):
    min_Lon, min_Lat, max_Lon, max_Lat = bounding_box
    pointList = [Point(min_Lon, min_Lat),Point(max_Lon,min_Lat),Point(max_Lon, max_Lat),Point(min_Lon, max_Lat)]
    return(Polygon([[p.x, p.y] for p in pointList]))

