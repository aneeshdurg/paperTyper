import cv2
import numpy as np
from sys import argv
from time import time
from time import sleep
import threading 
from multiprocessing import Process,Array,Event,Queue
from evdev import UInput, ecodes as e
from os import system

uinput = UInput()
cam = cv2.VideoCapture(1)
frameArr = [False, None]

def getFrames(frames):
    #Get frame and save to frame list
    while True:
        frame=frames.get()
        frame[0], frame[1] = cam.read()
        frames.put(frame)




def theProcess(bounds, thisWord, words):
	print "STARTED: "+thisWord
	first = None
	content = None
	lastCount = 0
	hwindex = 0
	flag = False
	normalArea = -1
	avgNormalArea = [0, 0]
	flip = False
	lastTime = -1
	pressed = False

	while True:
		frameArr = frames.get()
		s, f = frameArr[0], frameArr[1]
		frames.put(frameArr)
		if f == None:
			continue

		if "-s" in argv:
			cv2.imshow("frame", f)
		if s:
			f = f[bounds[0]:bounds[1], bounds[2]:bounds[3]]
			gray = cv2.cvtColor(f, cv2.cv.CV_BGR2GRAY)
			if first==None:
				first = gray
				content = gray
			else:
				diff = cv2.absdiff(first, gray)
				_, diff = cv2.threshold(diff,20,255,cv2.THRESH_BINARY)
				(cnts, _) = cv2.findContours(diff.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
				toDel = []
				totalArea = 0
				for c in xrange(len(cnts)):
					currentArea = cv2.contourArea(cnts[c]) 
					if currentArea<20:
						toDel.append(c)
					totalArea+=currentArea
				for i in xrange(len(toDel)):
					del cnts[toDel[i]-i]
				#print "NUM CONTS: ",len(cnts)
				if "-s" in argv:
					cv2.imshow(thisWord+"diff", diff)
				#white=np.sum(diff)
				if (lastCount>2*len(cnts) and len(cnts)==0):
					flag = True
					#print hwindex, "Hello world!"
				#print "DIFFERENCE: ",abs(white-lastCount)
				lastCount = len(cnts)
				first = gray
			thresh = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,101,20)
	
			#thresh = cv2.erode(thresh, None)
			thresh = cv2.dilate(thresh, None)
			if(avgNormalArea[1]<5):
				avgNormalArea[0]+=np.sum(thresh)
				avgNormalArea[1]+=1
				if(avgNormalArea[1]==5):
					normalArea = avgNormalArea[0]/avgNormalArea[1]
					print normalArea
			elif flag:
				if (abs(np.sum(thresh)-normalArea)>100000):
					if lastTime==-1:
						lastTime = time()
						#print thisWord
						words.put((thisWord+"_down", time()))
						pressed = True
					if((time()-lastTime)>=0.5):
						lastTime = time()
						#print thisWord
						#words.put((thisWord, time()))
						hwindex+=1
						#print hwindex
						#print np.sum(thresh)
						#print normalArea
					#else:
					#	print "TIME: ", time()-lastTime
					#flag = False
				else:
					flag = False
					if(pressed):
						words.put((thisWord+"_up", time()))
						pressed = False
					if "-s" in argv:
						cv2.imshow(thisWord+"Failure", thresh)
					#print "Failed!", abs(np.sum(thresh)-normalArea), "\n\t", np.sum(thresh), " ", normalArea
			#elif flip:
			#	flag = False
			#	normalArea = normalArea+np.sum(thresh)
			#	normalArea /= 2
			else:
				if(pressed):
					words.put((thisWord+"_up", time()))
					pressed = False
				flag = False
	
			if(not flag):
				lastTime = -1
				#print "RESET"
				#print "Adjusted to: ", normalArea
			flip = not flip
			#thresh = cv2.dilate(thresh, None)
			(cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
	
			#print len(cnts)
			cv2.drawContours(f, cnts, -1, 10, -1)
			if "-s" in argv:
				cv2.imshow(thisWord+"f", f)
			if "-s" in argv:
				cv2.imshow(thisWord+"t", thresh)
			cv2.waitKey(1)

def slider():
	
	last = -1
	while True:
		frameArr = frames.get()
		s, f = frameArr[0], frameArr[1]
		frames.put(frameArr)
		if f == None:
			continue
		f = f[170:212, 16:476]
		gray = cv2.cvtColor(f, cv2.cv.CV_BGR2GRAY)
		_, thresh = cv2.threshold(gray, 127, 255,cv2.THRESH_BINARY_INV)
		
		xAvg = 0
		counter = 0
		for i in xrange(len(thresh)):
			for j in xrange(len(thresh[0])):
				if thresh[i][j]==255:
					xAvg+=j
					counter+=1
		xAvg/=counter
		
		if counter>0.5*len(thresh)*len(thresh[0]):
			continue
		if last==-1:
			last = xAvg
		else:
			if 10<abs(last-xAvg)<200:
				if last>xAvg:
					uinput.write(e.EV_KEY, e.KEY_BRIGHTNESSUP, 1)
					uinput.write(e.EV_KEY, e.KEY_BRIGHTNESSUP, 0)
				else:
					uinput.write(e.EV_KEY, e.KEY_BRIGHTNESSDOWN, 1)
					uinput.write(e.EV_KEY, e.KEY_BRIGHTNESSDOWN, 0)
				uinput.syn()
				last = xAvg


		#avgX/=(thresh.shape[:2][1])
		#print "AVGX: ", x

def processKeys(commands):
	processed = 0
	exec("print processed")
	for c in commands:
		if len(c)>0:
			processed+=1
			exec("arg1 = "+c[0])
			exec("arg2 = "+c[1])
			uinput.write(e.EV_KEY, arg1, arg2)
	if processed!=0:
		uinput.syn()

def repeatProcessKeys(name):
	commands = actions[name]["down"]
	processed = 0
	exec("print processed")
	for c in commands:
		if len(c)>0:
			processed+=1
			exec("arg1 = "+c[0])
			exec("arg2 = "+c[1])
			uinput.write(e.EV_KEY, arg1, arg2)
	if processed!=0:
		uinput.syn()

	while keyEvents[name][0]:
		if time()-keyEvents[name][1]>=0.5:
			commands = actions[name]["down"]
			processed = 0
			exec("print processed")
			for c in commands:
				if len(c)>0:
					processed+=1
					exec("arg1 = "+c[0])
					exec("arg2 = "+c[1])
					uinput.write(e.EV_KEY, arg1, arg2)
			if processed!=0:
				uinput.syn()
			keyEvents[name] = (True, time())

def checkHeirarchy(name):

		parentOutput = None
		try:
			parentOutput = inputs.get_nowait()
		except:
			print "EMPTY QUEUE"
			pass
		if parentOutput!=None:
			parentName = parentOutput[0].split("_")[0]
			print "FOUND PARENT: ", parentName
			raw_input()
			if actions[parentName]['parent']!=name:
				checkHeirarchy(parentName)
			else:
				if actions[name]['parent']=='' or (actions[name]['parent'] in keyEvents and not keyEvents[actions[name]['parent']][0]):
					if name not in keyEvents or not keyEvents[name][0]:
						keyEvents[name] = (True, newOutput[1])
						if actions[name]["repeat"]:
							threading.Thread(target=repeatProcessKeys, args=(name,)).start()
						else:
							processKeys(actions[name]["down"])	
		else:
			if actions[name]['parent']=='' or (actions[name]['parent'] in keyEvents and not keyEvents[actions[name]['parent']][0]):
				if name not in keyEvents or not keyEvents[name][0]:
					keyEvents[name] = (True, newOutput[1])
					if actions[name]["repeat"]:
						threading.Thread(target=repeatProcessKeys, args=(name,)).start()
					else:
						processKeys(actions[name]["down"])				



frames = Queue()
frames.put([None,None])
camProcess = Process(target=getFrames, args=(frames,))
camProcess.start()

inputs = Queue()

config = open("paperTyper.cfg", "r")
config = config.readlines()
####USE CONFIG
actions = dict()
print config
for c in config:
	c = c.replace('\n', '')
	collumn = c.split(';')
	print collumn
	parent = ''
	for col in collumn:
		print col
		if len(col)!=0:
			parts = col.split(',')
			actions[parts[0]] = dict()
			bounds = parts[1].replace('[', '').replace(']', '').split(':')
			actions[parts[0]]["location"] = []
			for b in bounds:
				actions[parts[0]]["location"].append(int(b))
			dnCommands = parts[2].replace("'", "").split(" ")
			for i in xrange(len(dnCommands)):
				parser = dnCommands[i].split(":")
				#print parser
				dnCommands[i] = [parser[0],parser[1]]
			#print dnCommands
			actions[parts[0]]["down"] = dnCommands

			upCommands = parts[3].replace("'", "").split(" ")
			for i in xrange(len(upCommands)):
				if len(upCommands[i])!=0:
					parser = upCommands[i].split(":")
					upCommands[i] = [parser[0],parser[1]]
				else:
					upCommands[i] = []
			actions[parts[0]]["up"] = upCommands
			#actions[parts[0]]["down"] = 
			actions[parts[0]]["repeat"] = (parts[4]=='r')

			actions[parts[0]]['parent'] = parent
			parent = parts[0]

			actions[parts[0]]["process"] = Process(target=theProcess, args=(actions[parts[0]]["location"],parts[0], inputs))	
			actions[parts[0]]["process"].start()

			print actions
			#raw_input()

#raw_input()

#slider = Process(target=slider)
#slider.start() 
#
#thread2 = Process(target=theProcess, args=([377,432, 130,214],"2", numbers))
#thread2.start() 
#
#thread3 = Process(target=theProcess, args=([280,370, 287,573],"Hello World!", numbers))
#thread3.start() 

keyEvents = dict()
lastOutput = None


while True:
	newOutput = inputs.get()
	if newOutput[0] == 1:
		if lastOutput[0]!=2 or newOutput[1]-lastOutput[1]<0.1:
			pass
			print newOutput
	else:
		pass
		print newOutput
	name = newOutput[0].split("_")[0]
	if newOutput[0][-1]=='n':
		checkHeirarchy(name)
	else:
		keyEvents[name] = (False, newOutput[1])
		processKeys(actions[name]["up"])
	print keyEvents
	#system("clear")

	lastOutput = newOutput