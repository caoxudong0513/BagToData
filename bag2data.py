'''
bag2data

Copyright 2012 Nick Speal <nick@speal.ca> and McGill University's Aerospace Mechatronics Laboratory contributors.
Copyright 2016 W. Nicholas Greene <wng@csail.mit.edu> Massachusetts Institute of Technology
Copyright 2017 Francisco Alexandre R. Alencar <alealencar@gmail.com> Mobile Robotics Laboratory - ICMC/USP

The following code is a derivative work of the code from the Nick Speal and Nicholas Greene.
This code therefore is also licensed under the terms of the GNU Public License, verison 2.

This script saves each topic in a rosbag file as a folder with images or csv files.

Written by Francisco A. R. Alencar in July 2017

URL: www.lrm.icmc.usp.br
Youtube: www.youtube.com/lrmicmc

Based on:

Bag2CSV - OpenAgInitiative
http://github.com/OpenAgInitiative/openag_cv/blob/master/utils/Bag2CSV.py

bag_to_images.py - MIT
http://www.pythonexample.com/snippet/python/bag_to_imagespy_wngreene_python

'''

import rosbag, sys, csv
import time
import string
import os
import argparse
import cv2
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

def main():
    parser = argparse.ArgumentParser(description="Extract images and data from a ROS bag.")
    parser.add_argument("--files", nargs='*', help="Input ROS bag files.")

    args = parser.parse_args()

    if args.files is None:
        listOfBagFiles = [f for f in os.listdir(".") if f[-4:] == ".bag"]	#get list of only bag files in current dir.
    else:
        listOfBagFiles = args.files

    numberOfFiles = str(len(listOfBagFiles))
    print "Reading " + numberOfFiles + " bagfiles... \n"
    #for f in listOfBagFiles:
    #    print f
    main_count = 0
    for bagFile in listOfBagFiles:
        main_count += 1
        print "Reading file " + str(main_count) + " of  " + numberOfFiles + ": " + bagFile
        #access bag
        bag = rosbag.Bag(bagFile)
        bagContents = bag.read_messages()
        bagName = bag.filename


        #create a new directory
        folder = string.rstrip(bagName, ".bag")
        try:	#else already exists
            os.makedirs(folder)
        except:
            pass

        #get list of topics from the bag
        listOfTopics = []
        for topic, msg, t in bagContents:
            if topic not in listOfTopics:
                listOfTopics.append(topic)

        forbiden_list = ["image", "rosout", "tf"]
        for topicName in listOfTopics:
            if ("camera_info" in topicName) or not any(forbiden in topicName for forbiden in forbiden_list):
                #Create a new CSV file for each topic
                filename = folder + '/' + string.replace(topicName[1:], '/', '_') + '.csv'
                with open(filename, 'w+') as csvfile:
                    filewriter = csv.writer(csvfile, delimiter = ',')
                    firstIteration = True	#allows header row
                    for subtopic, msg, t in bag.read_messages(topicName):	# for each instant in time that has data for topicName
                        #parse data from this instant, which is of the form of multiple lines of "Name: value\n"
                        #	- put it in the form of a list of 2-element lists
                        msgString = str(msg)
                        msgList = string.split(msgString, '\n')
                        instantaneousListOfData = []
                        for nameValuePair in msgList:
                            splitPair = string.split(nameValuePair, ':')
                            for i in range(len(splitPair)):	#should be 0 to 1
                                splitPair[i] = string.strip(splitPair[i])
                            instantaneousListOfData.append(splitPair)
                        #write the first row from the first element of each pair
                        if firstIteration:	# header
                            headers = ["rosbagTimestamp"]	#first column header
                            for pair in instantaneousListOfData:
                                headers.append(pair[0])
                            filewriter.writerow(headers)
                            firstIteration = False
                        # write the value from each pair to the file
                        values = [str(t)]	#first column will have rosbag timestamp
                        for pair in instantaneousListOfData:
                            values.append(pair[1])
                        filewriter.writerow(values)

            elif "image" in topicName and "imu" not in topicName:
                bridge = CvBridge()
                folder_img =  string.replace(topicName[1:], '/', '_')
                #create a new directory
                try:	#else already exists
                    os.makedirs(folder+"/"+folder_img)
                except:
                    pass

                count = 0
                print topicName
                f=open(os.path.join(folder+"/time.txt"),'w')
                for topic, msg, t in bag.read_messages(topics=[topicName]):
                    #convert ros image to cv2 image
                    print topicName
                    cv_img = bridge.imgmsg_to_cv2(msg, desired_encoding="passthrough")
                    #write image with seconds and milliseconds information
                    cv2.imwrite(os.path.join(folder+"/"+folder_img, "{:04d}".format(count)+"-{}.{:03d}.bmp".format(str(t.secs)[-4:], t.nsecs/1000000)), cv_img)
                    f.write("{:04d}".format(count)+" {}.{:03d}".format(str(t.secs)[-4:], t.nsecs/1000000))
                    f.write('\n')
                    print "Wrote image %i" % count

                    count += 1
                f.close()

        bag.close()

    print "Done reading all " + numberOfFiles + " bag files."
    return

if __name__ == '__main__':
    main()
