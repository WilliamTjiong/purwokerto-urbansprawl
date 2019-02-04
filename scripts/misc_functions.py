
# coding: utf-8

# In[ ]:



"""Data acquisition module for retrieving Landsat products
    Functions:
    1. getFilePath
    2. listUrlFromDataframe
    3. clipRaster

"""

#libraries for reading files
import os
import rasterio
import numpy as np
import rasterio.mask 


def getFilePath(parent_dir,sub_dir,file_endswith):
    """Get the absolute path of a file
    Get the absolute path of a file in a certain directory or current directory. 


    Parameters
    ----------
    parent_dir: a string
    sub_dir: a string
    file_endswith: a file

    Returns
    -------

    String

    """
    #if sub_dir is not specified, search for file in parent_dir
    if sub_dir != None:
        product_dir = os.path.join(parent_dir,sub_dir)
        
        try:
            file_name = [file for file in os.listdir(product_dir) if file_endswith in file][0]
            file_path = os.path.join(product_dir,file_name)
            return file_path
        except IndexError:
            print('No such file')
    else:
        try:
            file_name = [file for file in os.listdir(parent_dir) if file_endswith in file][0]
            file_path=os.path.join(parent_dir,file_name)
            return file_path
        except IndexError:
            print('No such file')

def listUrlFromDataframe(selected_scenes_df):
    #create list with product url
    base_url='https://console.cloud.google.com/storage/browser/'
    product_url=[base_url+url[5:] for url in selected_scenes_df['BASE_URL']]

    return product_url

def clipRaster(image_file,clip_geometry,outputdir,output_file):
    
    with rasterio.open(image_file) as src:
        out_image,out_transform = rasterio.mask.mask(src,clip_geometry,crop=True,all_touched=True)
        out_profile=src.profile.copy()
        out_profile.update({"transform": out_transform,
                                   "driver": "GTiff",
                                 "height": out_image.shape[1],
                                 "width": out_image.shape[2]
                           })
        clip_imagename='{}'.format(output_file)
        clip_imagepath=os.path.join(outputdir,clip_imagename)
        with rasterio.open(clip_imagepath,'w',**out_profile) as dst:
            dst.write(out_image)
            print('Clipped image is saved in: ',clip_imagepath)

def normalize(image_array,bitrange=1):
    array_min, array_max = image_array.min(), image_array.max()
    normalized_image = (image_array - array_min)/(array_max - array_min)*bitrange
    return normalized_image