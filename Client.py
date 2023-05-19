from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os, io

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"
HEADER_SIZE = 12 
RECVFORM_BUFFER_SIZE = 32760
RECV_BUFFER_SIZE = 256
MAX_SEQ_NUM = 65535
TIME_OUT = 0.5 

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3

	streamSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	commSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	event = None
	listener = None
	isStreamSocketOpen = 0
	
	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0
		self.setupCounter = 0
		
	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
	def createWidgets(self):
		"""Build GUI."""
		# Create Setup button
		# self.setup = Button(self.master, width=20, padx=3, pady=3)
		# self.setup["text"] = "Setup"
		# self.setup["command"] = self.setupMovie
		# self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Stop"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2)
		
		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 
	
	def setupMovie(self):
		"""Setup button handler."""
	#TODO
		if (self.state != self.INIT):
			return
		else:
			if (self.setupCounter == 0):
				self.sendRtspRequest(self.SETUP)
				serverReply = self.recvRtspReply()
				respondCode, self.sessionId = self.parseRtspReply(serverReply)
    
				if (respondCode != "200"):
					if (respondCode == "404"):
						tkinter.messagebox.showerror(title="ERROR!", message="FILE_NOT_FOUND")
					elif (respondCode == "500"):
						tkinter.messagebox.showerror(title="ERROR!", message="CONNECTION_ERROR")
      
				if (self.isStreamSocketOpen == 0):
					self.openRtpPort()
					self.isStreamSocketOpen = 1
				self.rtspSeq += 1
				self.state = self.READY
				# self.setup.config(state = "disabled")
				self.start.config(state = "normal")
				self.setupCounter += 1
	
	
	def exitClient(self):
		"""Teardown button handler."""
	#TODO
		if (self.state != self.INIT):
			self.sendRtspRequest(self.TEARDOWN)
			self.rtspSeq += 1
			serverReply = self.recvRtspReply()
			respondCode, self.sessionId = self.parseRtspReply(serverReply)
			if (respondCode != "200"):
				if (respondCode == "404"):
					tkinter.messagebox.showerror(title="ERROR!", message="FILE_NOT_FOUND")
				elif (respondCode == "500"):
					tkinter.messagebox.showerror(title="ERROR!", message="CONNECTION_ERROR")
				return
			self.master.destroy()
		sys.exit(0)
			
	def pauseMovie(self):
		"""Pause button handler."""
	#TODO
		if (self.state != self.PLAYING):
			return
		self.sendRtspRequest(self.PAUSE)
		self.rtspSeq += 1
		serverReply = self.recvRtspReply()
		respondCode, self.sessionID = self.parseRtspReply(serverReply)
		if (respondCode != "200"):
			if (respondCode == "404"):
				tkinter.messagebox.showerror(title="ERROR!", message="FILE_NOT_FOUND")
			elif (respondCode == "500"):
				tkinter.messagebox.showerror(title="ERROR!", message="CONNECTION_ERROR")
			return
		self.start.config(state = "normal")
		self.pause.config(state = "disabled")
		self.state = self.READY
		self.event.set()
	
	def playMovie(self):
		"""Play button handler."""
	#TODO
		self.setupMovie()
		if self.state == self.INIT:
			tkinter.messagebox.showerror(title="ERROR!", message="NEED_SETUP_FIRST")
			return
		if self.state == self.READY:
			self.sendRtspRequest(self.PLAY)
			self.rtspSeq += 1
		serverReply = self.recvRtspReply()
		respondCode, self.sessionId = self.parseRtspReply(serverReply)
		if (respondCode != "200"):
			if (respondCode == "404"):
				tkinter.messagebox.showerror(title="ERROR!", message="FILE_NOT_FOUND")
			elif (respondCode == "500"):
				tkinter.messagebox.showerror(title="ERROR!", message="CONNECTION_ERROR")
			return
		self.state = self.PLAYING
		self.event = threading.Event()
		self.listener = threading.Thread(target = self.listenRtp)
		self.listener.start()
		self.start.config(state = "disabled")
		self.pause.config(state = "active")

	def listenRtp(self):		
		"""Listen for RTP packets."""
	#TODO
		rpt = RtpPacket
		while True:
			try:
				self.event.wait(0.03)
				if self.event.is_set():
					break
				data, addr = self.streamSocket.recvfrom(RECVFORM_BUFFER_SIZE)
				rpt.decode(self, data)
				if rpt.seqNum(self) == MAX_SEQ_NUM:
					self.state = self.INIT
					self.setup.config(state = "normal")
					self.start.config(state = "disabled")
					break
 
				frameBuffer = io.BytesIO(rpt.getPayload(self))
				frame = Image.open(frameBuffer)
				ImgTk = ImageTk.PhotoImage(image = frame)
				width, height = frame.size
				self.label.config(image = ImgTk, width = width, height = height)
			except:
				tkinter.messagebox.showerror(title= "VIDEO ENDED",
                                 			message= "End of video");
				#self.setupMovie();
				self.state = self.INIT;
				self.start.config(state = "normal")
				break;
					
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
	#TODO
	
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
	#TODO
		
	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
	#TODO
		self.commSocket.connect((self.serverAddr, self.serverPort))
		self.commSocket.settimeout(TIME_OUT)
	
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		#-------------
		# TO COMPLETE
		#-------------
		if requestCode == self.SETUP:
			self.commSocket.send(("SETUP " + self.fileName + " RTSP/1.0\nCSeq " 
			 					 + str(self.rtspSeq) + "\n" + "Transport RTP/UDP client_port " 
								 + str(self.rtpPort)).encode())
   
		elif requestCode == self.PLAY:
			self.commSocket.send(("PLAY " + self.fileName + " RTSP/1.0\nCSeq " 
			 					 + str(self.rtspSeq) + "\n" + "Session: "
								 + str(self.sessionId)).encode())
   
		elif requestCode == self.PAUSE:
			self.commSocket.send(("PAUSE " + self.fileName + " RTSP/1.0\nCSeq "
			 					 + str(self.rtspSeq) + "\n" + "Session: "
								 + str(self.sessionId)).encode())
   
		elif requestCode == self.TEARDOWN:
			self.commSocket.send(("TEARDOWN " + self.fileName + " RTSP/1.0\nCSeq "
			 					 + str(self.rtspSeq) + "\n" + "Session: "
								 + str(self.sessionId)).encode())

	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		#TODO
		reply = self.commSocket.recv(RECV_BUFFER_SIZE);
		print(reply);
		return reply.decode().split("\n");
	
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		#TODO
		respondCode = data[0].split(' ')[1]
		sessionId = data[2].split(' ')[1]
		return respondCode, sessionId
	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		self.streamSocket.bind((self.serverAddr, self.rtpPort));
		
		# Set the timeout value of the socket to 0.5sec
		self.streamSocket.settimeout(TIME_OUT);
  
	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		#TODO
		self.exitClient()