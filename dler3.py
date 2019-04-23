#! /usr/bin/python

#Downloads images using google Image Downloader.  Also runs test.py, which will ensure each image is only downloaded once
#NOTE: RUN AS ROOT FOR THIS VERSION
#V2 -> 1 progress file for all downloads
#V2 set up database tables if they don't exist
#V1.1 handle empty PROGRESS_FILE
###########
#/IMPORTS/#
###########
from google_images_download import google_images_download
import os
import datetime
from datetime import timedelta
from datetime import date
import subprocess
from subprocess import Popen
#import shlex
import time
import json
#############
#/CONSTANTS/#
#############
OFFSET_SIZE=50 #may have to limit to 100
THREAD_COUNT=1 #UNUSED
TIME_INTERVAL=1 #in days
TEMP_DIR="/media/ramdisk" #KEEP CONSTANT FOR v1
TEMP_SIZE="750M"
CLEAR_TEMP=True#unused
CHROME_DRIVER="/data/chromedriver"
PROGRESS_FILE="/data/PROGRESS"
#PROGRESS_FILE_FORMAT:, files cannot contain commas
#Progress=Date
#Offset=offSetCount
#END PROGRESS_FILE FORMAT:
FIRST_DATE=(2008,4,1) #YYYY/MM/DD, get all images upto this date in a single block 
SLEEP_TIME=5 #time to wait between checking if a folder is empty, higher offset makes this number less relevent

KEY_WORDS_FILE="keywords.txt"
PREFIX_FILE="" #"prefix.txt"
POSTFIX_FILE="" #"prefix.txt"
#OUTPUT_DIR=ZZZ#UNUSED
##################################
#CONSTANTS DERIVED FROM CONSTANTS#
##################################
START_DATE = datetime.datetime(FIRST_DATE[0], FIRST_DATE[1],FIRST_DATE[2])
#V2 do with with shell=false
I_NOTIFY_STRING = "inotifywait -m -r -e create "+ TEMP_DIR + " | while read -r line; do echo {$line} |./test.py ; done"
########################
#FUNCTION: DATE_CONVERT#
########################
def dateConv(date):
  dateTuple = date #str(date).split("-")
  #YYYY-MM-DD -> MM/DD/YYYY
  return str(dateTuple[1])+"/"+str(dateTuple[2])+"/"+str(dateTuple[0])

def dateConv2(date):
  dateTuple = str(date).split(" ")[0].split("-")
  #YYYY-MM-DD -> MM/DD/YYYY
  return str(dateTuple[1])+"/"+str(dateTuple[2])+"/"+str(dateTuple[0])

def unDateConv(dateStr):
  dateTuple = str(dateStr).split("/")
  #MM/DD/YYYY -> YYYY-MM-DD
  return datetime.datetime(int(dateTuple[2]), int(dateTuple[0]), int(dateTuple[1]))

####################
#load progress file#
####################
#needs debugging
#assume if it exists it is a file of the proper format with proper permissions, fix in V2
#does it exist?
if os.path.exists(PROGRESS_FILE):
  print("RESUMING DOWNLOAD...")
  #open it
  progressFile = open(PROGRESS_FILE,'r')
  #load all data
  progress = progressFile.readlines()
  progressFile.close()
  #get the last line only
  progress = progress[len(progress)-1]
  #get the date and the offset
  currentDate = progress.split('#')[0].split('-')
  currentDate = datetime.datetime(int(currentDate[0]),int(currentDate[1]),int(currentDate[2]))
  offsetCount = int(progress.split('#')[1])
  print("CONTINUING FROM: " + str(currentDate))
else:
  #doesn't exist, create, add first date and load defaults  
  progress = open(PROGRESS_FILE,"w")
  progress.close()
  currentDate = datetime.datetime(FIRST_DATE[0], FIRST_DATE[1], FIRST_DATE[2])
  offsetCount = 0
  print("NO PREVIOUS DOWNLOADS FOUND")

################
#Set up RAMDISK#
################
#REQUIRES ROOT!#
################
#V2 will not require root, at the expense of speed
os.system("mkdir -p "+TEMP_DIR)
os.system("mount -t tmpfs -o size="+ TEMP_SIZE + " tmpfs " +TEMP_DIR)
os.system("chmod 777 "+ TEMP_DIR +" -R")

#############
#iNotifyWait#
#############
inotify = Popen(args=I_NOTIFY_STRING, stdout=subprocess.PIPE, shell=True)
#wait for inotify to set up
time.sleep(SLEEP_TIME)

##############################
#Other misc setup, const args#
##############################

args =  {"keywords_from_file":KEY_WORDS_FILE}
#Prefix file, from one line each to a comma seperated list
if PREFIX_FILE != "":
  prefixFile= open(PREFIX_FILE,'r')
  #load all data
  prefixList = prefixFile.readlines()
  prefixFile.close()
  prefixList = ','.join(map(str, prefixList))
  args["prefix_keywords"] = prefixList

#Postfix file from one line each to a comma seperated list
if POSTFIX_FILE != "":
  postfixFile= open(POSTFIX_FILE,'r')
  #load all data
  postfixList = postfixFile.readlines()
  postfixFile.close()
  postfixList = ','.join(map(str, postfixList))
  args["suffix_keywords"] = postfixList

args["output_directory"] = TEMP_DIR
args["related_images"] = True
args["no_directory"] = True
args["chromedriver"] = CHROME_DRIVER

###################################
###################################
##                               ##
##  Start download part of code  ##
##                               ##
###################################
###################################
END_LOOP = False
downloader = google_images_download.googleimagesdownload()

####################################
#First download has different dates#
####################################
if str(currentDate.date()) == str(START_DATE.date()):
  timeRange = {"time_min":"01/01/0000","time_max":dateConv2(START_DATE.date())}
  args["time_range"] = json.dumps(timeRange) 
  args["offset"] = 0
  args["limit"] = OFFSET_SIZE
 
  print("STARTING TO DOWNLOAD...")
  imagesCaptured = ["PLACEHOLDER"]
  while len(imagesCaptured) > 0:
    print(args["offset"])
    imagesCaptured = downloader.download(args)
    #flatten list
    imagesCaptured = [item for sublist in imagesCaptured.values() for item in sublist]
    #print(imagesCaptured)
    args["offset"] = args["limit"]
    args["limit"] = args["limit"]+OFFSET_SIZE
  args["offset"] = 0
  args["limit"] = OFFSET_SIZE
  #wait for the temp directory to empty, don't want to overload the RAMDISK
  while len(os.listdir(TEMP_DIR))>0:
    time.sleep(SLEEP_TIME)
  print("END DAY 1")
  #adjust the day range
  timeRange["time_min"] = timeRange["time_max"]
  timeRange["time_max"] = dateConv2( unDateConv(timeRange["time_max"]) + timedelta(days=1))
  args["time_range"] = json.dumps(timeRange)
else:
  timeRange = {}
  timeRange ["time_min"] = dateConv2(currentDate)
  timeRange ["time_max"] = dateConv2(unDateConv(timeRange["time_min"]) + timedelta(days=1))
  args["time_range"] = json.dumps(timeRange)
  args["offset"] = offsetCount
  args["limit"] = args["offset"]+OFFSET_SIZE 
###########################
#The rest of the downloads#
###########################

#not equal, we don't want to mark "Today" as having downloaded all of the pictures without the day being over
while unDateConv(timeRange["time_min"]).date() < date.today():
  imagesCaptured = ["PLACEHOLDER"]
  while len(imagesCaptured) > 0:
    imagesCaptured = downloader.download(args) 
    #flatten list
    imagesCaptured = [item for sublist in imagesCaptured.values() for item in sublist]
    print(args["offset"])
    #next offset
    args["offset"] = args["limit"]
    args["limit"] = args["limit"]+OFFSET_SIZE
    #append to file
    progressFile = open(PROGRESS_FILE,'a+')
    progressFile.write(str(unDateConv(timeRange["time_min"]).date()) +"#"+str(args['offset'])+'\n')
    progressFile.close()
    #wait for RAMDISK to clear, don't overload it
    #V2, make sure bad files don't hold up the program, if the file is still there after 3 wait peroids, assume it needs manual action taken, move to a diferent folder
    interations=0
    while len(os.listdir(TEMP_DIR))>0:
      print(os.listdir(TEMP_DIR))
      print("SLEEP")
      time.sleep(SLEEP_TIME)
    print("AWAKE")
  #next date
  args['offset'] = 0
  args['limit'] = OFFSET_SIZE
  timeRange["time_min"] = timeRange["time_max"]
  timeRange["time_max"] = dateConv2( unDateConv(timeRange["time_max"]) + timedelta(days=1))
  args["time_range"] = json.dumps(timeRange)

#########
#CLEANUP#
#########
