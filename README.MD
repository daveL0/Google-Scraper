Google-Scraper

This program is a wrapper around hardikvasa's google-images-download program.  It will download all images off of Google that match a particular search.
This wrapper adds: 1. Ability to resume download of large amounts of images.  2. Remove most (but not all) duplicate images so the harddrive isn't clutttered with many copies the same image.  3. The ability to not specify how many images you want to download.  It will just download all of them.  4. Since the program runs searches based on date (details below) it is possible to use a simple cron job to download the latest images matching your search every day or week.

Details:
The program starts by creating a RAMdisk, then will set up an inotifywait on the RAMdisk.  The first part of the program will call the Google-images-download program to downloand all images for a paricular search since the last time the program was ran.  As they are stored on the RAMdisk, the second part (called by inotifywait) will use a Dhash to see if the file already exists in storage.  If it does, and the previous file is of an equal or higher resolution, the downloaded file is discarded.  If it appears to have no match, the file is moved from the RAMdisk and is stored in a more permanent location.  The file's metadata is stored in the database.  If there is a match that is a lower resolution than the current file, that file is removed and replaced with the higher resolution one.

Dependencies:
Google-images-download (and related dependencies, ie selenium)
MySQL or MariaDB 10.3 or other SQL database
python Wand package
inotifywait (Linux package)
chromedriver

Why use this wrapper:
If you just want to get lots of images, without many duplicates and get them every day.  Can be used to get new images every day for machine learning algrothims for example.  Of if you just want to archive all images of something.

Notes:
all metadata (including filename and source) is lost when using this program.

TODO:
Database setup script
Don't require root
offload settings to a seperate file
Paramertise SQL queries
fix bugs
windows capability
cleanup
don't require chromedriver
better documentation
fix file paths
fix the never leave the folder bug
rename files
update this readme