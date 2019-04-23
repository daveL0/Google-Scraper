#! /usr/bin/python

from wand.image import Image
import shutil
from shutil import copyfile
import dhash
import sys
import os
import time
import MySQLdb as DB
######################
# DATABASE CONSTANTS #
######################
HOST= '127.0.0.1'
USER='bot'
PASSWORD='resnetsucks'
DATABASE='dhash'
PORT=3306

TABLE='hash'

#OTHER CONSTANTS:
FOLDER = "/media/ramdisk/"
HAMMING_DISTANCE = 2
SAVE_FOLDER = "/data/downloads/images/"
#import multiprocessing
#using parallelism  rather than iwaitnotify since this way, we only need 1 DB connection
#^ for V2
#V1 will crash on Dave's VM with more than 20 connections
#Requires dhash, (pil or wand.image), sql server
newName= None
db = DB.connect(host=HOST, user=USER, passwd=PASSWORD, db=DATABASE, port=PORT)
cursor=db.cursor()

#get file name
string = sys.stdin.readlines()[0]
REMOVE_STRING = ' CREATE '
#remove inotify wait formattng
string = string[1:len(string)-2]
file = string.replace(REMOVE_STRING,'')
#If ends in -ext instead of .ext, change the - to a .
if file[-4:-3] != '.':
  os.rename(file, str(file[:-4] + "."+file[-3:]))
  file = file[:-4] + "."+file[-3:]

#open file
try:
  with Image(filename=file) as image:
    row, col = dhash.dhash_row_col(image)
    width = image.width
    height = image.height
    #image.close()
except:
  #NOT A VALID IMAGE
  db.close()
  os.remove(file)
  exit()
hash= dhash.format_hex(row, col)
hashL=str(hash[:16])
hashR=str(hash[16:])
#get the hamming weight, convert b16 string to b10, to binary string, count 1's
weight =  bin(int(hash, 16)).count('1')
#get items within hamming weight range.  Hamming weight is used to reduce the number of results so we don't have to compare against every item in the DB
cursor.execute("\
  With TBL1 AS( \
    SELECT conv(mid(dhash,1,16),16,10) as H_LEFT,conv(mid(dhash,17,16),16,10) as H_RIGHT, hammingWeight, x, y,dateDownloaded, name \
    FROM "+TABLE+" \
    WHERE  " + str(weight+HAMMING_DISTANCE) + " >= hammingWeight AND "+ str(weight-HAMMING_DISTANCE)+" <= hammingWeight)\
  SELECT \
    * \
  FROM TBL1 "
  #WHERE bit_Count(conv(dhash,16,10)^conv('"+hash+"',16,10)) <= " + str(HAMMING_DISTANCE) \
  #SQL CONV -> 64 bit percision, required 128, so we split it in half and do each half seperately
  +"WHERE "
  +"bit_Count(H_LEFT^conv('" + hashL + "',16,10)) + bit_Count(H_RIGHT^conv('" + hashR + "',16,10))  <= " + str(HAMMING_DISTANCE))
try:
  db.commit()
except:
  print("FATAL_ERROR")
  db.close()
  exit()
#bit_Count(A^B) == hamming distance
#Got the images that match
results = cursor.fetchall()
#dhash is in hexdecimal - stored as a string
itemsToRemove = []
insert = False
for item in results:
  #get the hamming distance, hash XOR itself  = 0
  hammingDelta = bin(int(item[0],16)^int(hash,16)).count('1')
  if hammingDelta <= HAMMING_DISTANCE:#They are judged to be the same image
    if width > item[2] and height > item[3]:
      #high resultion = better, remove old one
      itemsToRemove.append(item)
      insert = True

if len(results) == 0:
  insert  = True
#We need to insert the new items and remove the old ones
#Names will be in order of unsigned bigint+extension (Auto increment)
extension = file.split(".")
extension = "."+ extension[len(extension)-1] #final extension
#insert into DB
if insert:
  cursor.execute("\
    INSERT INTO "+TABLE+\
    " (dhash, hammingWeight,x,y,dateDownloaded, extension, name) \
     VALUES (%s,%s,%s,%s,CURDATE(),%s,DEFAULT)",(str(hash),str(weight),str(width),str(height),str(extension))
  )

  cursor.execute("SELECT MAX(name) FROM " + TABLE)
  db.commit()
  results = cursor.fetchall()
  newName = results[0][0]
  #save to disk
  try:
    #should be a blocking function
    shutil.copyfile(file,(SAVE_FOLDER+str(newName)+extension) )
  except:
    print("e")
  #remove all old ones from DB and the archive
  for item in itemsToRemove:
    #print(item)
    cursor.execute("DELETE FROM "+ TABLE + " WHERE name ='"+str(item[5])+"'")#name is in position 5
    try:
      pass
      os.remove(SAVE_FOLDER+str(item[5])+".*")
    except:
      pass
    db.commit()
else:
  pass
  #file is not being inserted
#in either case, remove from RAMDISK
#wait for file to be written, buffer flush
#while not os.path.exists( (SAVE_FOLDER+str(newName)+extension) ):
#  time.sleep(1)
db.close()
os.remove(file)