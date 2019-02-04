
# coding: utf-8

"""Data acquisition module for retrieving Landsat products\

    Functions:
    1. getProductsUrls_Google

"""

#general libraries
import pandas as pd
import os
import time

#web scraping libraries
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

def getProductUrls_Google(landsat_archive,datadir,path,row,spacecraft_id='LANDSAT_5',data_level='L1TP',sensor_id='TM',collection='T1',cloud_cover=30):
    
    #ignore warning to overwrite the original pandas dataframe
    pd.options.mode.chained_assignment = None
    
    #subset based on data level
    l5_df = landsat_archive.loc[(landsat_archive["SPACECRAFT_ID"] == spacecraft_id) & (landsat_archive["DATA_TYPE"] == data_level) & 
                          (landsat_archive["COLLECTION_CATEGORY"] == collection) & (landsat_archive["SENSOR_ID"] == sensor_id)]
    
    #subset based on path-row values
    l5_df["WRS_PATH"],l5_df["WRS_ROW"] = pd.to_numeric(l5_df["WRS_PATH"]),pd.to_numeric(l5_df["WRS_ROW"])
    l5_df = l5_df.loc[(l5_df["WRS_PATH"]==path) & (l5_df["WRS_ROW"]==row)]

    
    #subset based on cloud cover
    l5_df["CLOUD_COVER"] = pd.to_numeric(l5_df["CLOUD_COVER"])
    l5_df = l5_df.sort_values(by=['CLOUD_COVER'],axis=0).reset_index(drop=True)
    l5_df = l5_df[l5_df['CLOUD_COVER']<cloud_cover]
    
    #subset based unique scene years with the least amount of cloud cover
    l5_df['DATE_ACQUIRED'] = pd.to_datetime(l5_df['DATE_ACQUIRED'])
    l5_df = l5_df.groupby(l5_df['DATE_ACQUIRED'].dt.year, group_keys=False).apply(lambda x: x.loc[x['CLOUD_COVER'].idxmin()]).reset_index(drop=True)
    
    #export to csv
    csv_file=os.path.join(datadir,"l5_df.csv")
    l5_df.to_csv(csv_file)
    
    print("{} matching scenes were found from the archive".format(len(l5_df)))
    print("A csv of the selected scenes from the archive is written in: ",csv_file)

    
def downloadlProducts_Google(product_url,dl_dir,driver_exe,file_list,google_email,google_password):
    
    #create product directory
    dl_dir = os.path.abspath(dl_dir)
    product_id  = os.path.basename(product_url)[0:40]
    product_dir = os.path.join(dl_dir,product_id)
    os.makedirs(product_dir,exist_ok=True)
    
    #setup chrome driver and open the url
    #the default download directory accepts only absolute path
    options = Options()
    options.add_experimental_option("prefs", {
        "download.default_directory": product_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    browser = webdriver.Chrome(options=options,executable_path=driver_exe)
    browser.get(product_url)
    
    #scrape the Google Cloud Landsat product directory and download the specified files
    #complete username form 
    username = browser.find_element_by_id('identifierId')
    username.send_keys(google_email,Keys.ENTER) 

    #wait 5 seconds until the password form page is loaded
    wait=WebDriverWait(browser, 10)
    wait.until(EC.presence_of_element_located((By.NAME, "password")))

    #complete password form
    password = browser.find_element_by_name('password')
    password.send_keys(google_password,Keys.ENTER)

    #wait for landsat cloud directory page to load then find element tags that correspond to the files
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody tr td a")))
    elems = browser.find_elements_by_css_selector('tbody tr td a')
    file_baseurl='https://storage.cloud.google.com/'

    for elem in elems:
        if file_baseurl in elem.get_attribute("href") and any(data in elem.get_attribute("href") for data in file_list):
            dl_link=elem.get_attribute("href")
            browser.get(dl_link)

    #close browser if files are downloaded 
    file_counter2=[]
    while True:
        for f in os.listdir(product_dir):
            if f.endswith(('.TIF','MTL.txt')):
                file_counter2.append(f)
        try:
            if len(list(set(file_counter2)))==len(file_list):
                file_counter2.clear()
                time.sleep(3)
                browser.quit()
                break
        except:
            pass
    
    



