# -*- coding: utf-8 -*-

# org. name: autoshutdown

#This plugin is free software, you are allowed to
#modify it (if you keep the license),
#but you are not allowed to distribute/publish
#it without source code (this version and your modifications).
#This means you also have to distribute
#source code of your modifications.
#png <from http://www.everaldo.com>

# modifications by shadowrider
# maintainer: <plugins@fs-plugins.de>

from . import _
from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSelection, ConfigEnableDisable, \
	ConfigYesNo, ConfigInteger, ConfigText, NoSave, ConfigNothing, ConfigIP, ConfigClock
from Components.ConfigList import ConfigListScreen
from Components.FileList import FileList
from Components.Harddisk import harddiskmanager
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.Sources.ServiceEvent import ServiceEvent
from Components.VolumeBar import VolumeBar
##
from Components.Pixmap import Pixmap
from Components.MenuList import MenuList
##
from ServiceReference import ServiceReference
from enigma import eTimer, iRecordableService, eActionMap, eServiceReference, eActionMap, getDesktop
import NavigationInstance
from os import path as os_path, system
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Tools import Notifications
from Tools.Directories import copyfile
from time import time, localtime, mktime,strftime
import datetime
import Screens.Standby

def calculateTime(hours, minutes, day_offset = 0):
	cur_time = localtime()
	unix_time = mktime((cur_time.tm_year, cur_time.tm_mon, cur_time.tm_mday, hours, minutes, 0, cur_time.tm_wday, cur_time.tm_yday, cur_time.tm_isdst)) + day_offset
	return unix_time

from enigma import eDVBVolumecontrol
from Components.VolumeControl import VolumeControl

version="1.8"
config.plugins.softsleepFS = ConfigSubsection()
config.plugins.softsleepFS.time = ConfigInteger(default = 120, limits = (1, 9999))
config.plugins.softsleepFS.inactivetime = ConfigInteger(default = 300, limits = (1, 1440))
config.plugins.softsleepFS.autostart = ConfigEnableDisable(default = False)
config.plugins.softsleepFS.enableinactivity = ConfigEnableDisable(default = False)
config.plugins.softsleepFS.inactivityaction = ConfigSelection(default = "standby", choices = [("standby", _("Standby")), ("deepstandby", _("Deepstandby"))])
config.plugins.softsleepFS.inactivitymessage = ConfigYesNo(default = True)
config.plugins.softsleepFS.messagetimeout = ConfigInteger(default = 20, limits = (1, 999))
config.plugins.softsleepFS.epgrefresh = ConfigYesNo(default = True)
config.plugins.softsleepFS.plugin = ConfigYesNo(default = False)
config.plugins.softsleepFS.volsteps = ConfigInteger(default = 4, limits = (0, 20))
config.plugins.softsleepFS.disable_at_ts = ConfigYesNo(default = False)
config.plugins.softsleepFS.disable_net_device = ConfigYesNo(default = False)
config.plugins.softsleepFS.wait_for_end = ConfigYesNo(default = False) #edit by s
config.plugins.softsleepFS.wait_max = ConfigInteger(default = 120, limits = (0, 1440))
config.plugins.softsleepFS.wait_min = ConfigInteger(default = 15, limits = (1, 1440))
config.plugins.softsleepFS.min_starttime = ConfigInteger(default = 20, limits = (1, 999))
config.plugins.softsleepFS.disable_hdd = ConfigYesNo(default = False)
config.plugins.softsleepFS.net_device = ConfigIP(default = [0,0,0,0])
config.plugins.softsleepFS.exclude_time_in = ConfigYesNo(default = False)
config.plugins.softsleepFS.exclude_time_in_begin = ConfigClock(default = calculateTime(20,0))
config.plugins.softsleepFS.exclude_time_in_end = ConfigClock(default = calculateTime(0,0))
config.plugins.softsleepFS.exclude_time_off = ConfigYesNo(default = False)
config.plugins.softsleepFS.exclude_time_off_begin = ConfigClock(default = calculateTime(20,0))
config.plugins.softsleepFS.exclude_time_off_end = ConfigClock(default = calculateTime(0,0))
config.plugins.softsleepFS.fake_entry = NoSave(ConfigNothing())
config.plugins.softsleepFS.debug = ConfigYesNo(default = False)

sytem_shut=False
sytem_shut2=False
try:
	sytem_shut= config.softsleepFS.enableinactivity.value
except:
	pass
try:
	sytem_shut2= config.softsleepFS.autostart.value
except:
	pass
no_system_shut=False
if sytem_shut2 or sytem_shut:
	no_system_shut=True


def checkIP(ip_address):
	ip_address = "%s.%s.%s.%s" % (ip_address[0], ip_address[1], ip_address[2], ip_address[3])
	ping_ret = system("ping -q -w1 -c1 " + ip_address)
	if ping_ret == 0:
		return True
	else:
		return False

def checkHardDisk():
	for hdd in harddiskmanager.HDDList():
		if not hdd[1].isSleeping():
			return True
	return False

def checkExcludeTime(begin_config, end_config):
	(begin_h, begin_m) = begin_config
	(end_h, end_m) = end_config
	cur_time = time()
	begin = calculateTime(begin_h, begin_m)
	end = calculateTime(end_h, end_m)
	if begin >= end:
		if cur_time < end:
			day_offset = -24.0 * 3600.0
			begin = calculateTime(begin_h, begin_m, day_offset)
		elif cur_time > end:
			day_offset = 24.0 * 3600.0
			end = calculateTime(end_h, end_m, day_offset)
		else:
			return False
	if cur_time > begin and cur_time < end:
		return True
	return False


class asdMessageBox(Screen):
	TYPE_YESNO = 0
	if getDesktop(0).size().width() < 1800:
		if config.plugins.softsleepFS.volsteps.value:
			skin = """
			<screen name="asdMessageBox" position="center,center" size="500,100" title="automatisches Abschalten">
			<widget name="Volume" pixmap="skin_default/progress_small.png" position="10,5" zPosition="1" size="480,7" transparent="1" />
			<widget name="QuestionPixmap" pixmap="skin_default/icons/input_question.png" position="20,20" size="53,53" alphatest="blend" />
			<widget name="list" position="100,20" size="390,70" itemHeight="32" transparent="1" />
			</screen>"""
		else:
			skin = """
			<screen name="asdMessageBox" position="center,center" size="500,100" title="automatisches Abschalten">
			<widget name="QuestionPixmap" pixmap="skin_default/icons/input_question.png" position="20,10" size="53,53" alphatest="blend" />
			<widget name="list" position="100,10" size="390,70" itemHeight="42" transparent="1" />
			</screen>"""
	else:
		if config.plugins.softsleepFS.volsteps.value:
			skin = """
			<screen name="asdMessageBox" position="center,center" size="500,120" title="automatisches Abschalten">
			<widget name="QuestionPixmap" pixmap="skin_default/icons/input_question.png" position="20,10" size="53,53" alphatest="blend" />
			<widget name="list" position="100,10" size="390,90" itemHeight="42" transparent="1" />
			<widget name="Volume" pixmap="skin_default/progress_small.png" position="10,105" zPosition="1" size="480,10" transparent="1" />
			</screen>"""
		else:
			skin = """
			<screen name="asdMessageBox" position="center,center" size="500,105" title="automatisches Abschalten">
			<widget name="QuestionPixmap" pixmap="skin_default/icons/input_question.png" position="20,10" size="53,53" alphatest="blend" />
			<widget name="list" position="100,10" size="390,90" itemHeight="42" transparent="1" />
			</screen>""" 

	def __init__(self, session, text, timeout = -1):
		Screen.__init__(self, session)
		self.volumeBar = VolumeBar()
		self["Volume"] = self.volumeBar
		self.volctrl = eDVBVolumecontrol.getInstance()
		self["QuestionPixmap"] = Pixmap()
		vol=int(self.volctrl.getVolume())
		self.volumeBar.setValue(vol)
		self.timer = eTimer()
		self.timer.callback.append(self.timerTick)
		self.timerRunning = False
		self.timeout = timeout
		self.origTitle = "autom. "
		zus_txt=" Ausschalten"
		if config.plugins.softsleepFS.inactivityaction.value == "standby":
			zus_txt=" Standby"
		self.origTitle = "autom."+zus_txt
		self.list = []
		self.list = [ (" "+_("cancel"), 1), (zus_txt, 0) ]
		self["list"] = MenuList(self.list)
		eActionMap.getInstance().bindAction('', -0x7FFFFFFF, self.pressKey)
		if self.timeout>0:
			self.startTimer()


	def startTimer(self):
		self.timer.start(1000)
		self.timerRunning=True

	def stopTimer(self):
		if self.timerRunning:
			del self.timer
			self.setTitle(self.origTitle)
			self.timerRunning = False

	def timerTick(self):
			self.timeout -= 1
			vol=int(self.volctrl.getVolume())
			self.volumeBar.setValue(vol)
			self.setTitle(self.origTitle + " "*5 +"> " + str(self.timeout) )
			if self.timeout == 0:
				self.timer.stop()
				self.timerRunning = False
				self.timeoutCallback()

	def timeoutCallback(self):
		#print ("[softsleepFS] Message-Timeout!")
		if config.plugins.softsleepFS.debug.value:
			f=open("/var/volatile/log/softsleepFS","a")
			f.write( datetime.datetime.fromtimestamp(time()).strftime('%H:%M:%S') + " end shutdown and message, aktion\n")
			f.close()
		self.cancel(True)


	def pressKey(self, key=None, flag=None):
		if key:
			if config.plugins.softsleepFS.debug.value:
				f=open("/var/volatile/log/softsleepFS","a")
				f.write( datetime.datetime.fromtimestamp(time()).strftime('%H:%M:%S') + " break shutdown and message, aktion\n")
				f.close()
			try:
				if self.timerRunning:self.stopTimer()
			except:
				pass
			if key==103:
				self.move(self["list"].instance.moveUp)
			elif key==108:
				self.move(self["list"].instance.moveDown)
			elif key==116:
				self.cancel(True)
			elif key== 352:
				self.ok()
			else:
				self.cancel()


	def ok(self):
		if self["list"].getCurrent()[1] == 0:
			self.cancel(True)
		else:
			self.cancel()

	def cancel(self,akt=False):
		eActionMap.getInstance().unbindAction('', self.pressKey)
		try:
			self.timer.stop()
			self.timerRunning = False
		except:
			pass
		if akt==True:
			self.close(True)
		else:
			self.close(False)

	def move(self, direction):
		self["list"].instance.moveSelection(direction)


class softsleepFSactionsfs:

	def __init__(self):
		self.oldservice = None
		self.session=self
		self.message=None
		self.volctrl = eDVBVolumecontrol.getInstance()
		self.bgr=128
		now = datetime.datetime.now().hour
		if now>=19:self.bgr=118
		self.setHelligkeit(self.bgr)
		#open("/proc/stb/vmpeg/0/pep_brightness", "w").write("%0.8X" % int(self.brg*256))
		self.asdvolume_timer = eTimer()
		self.asdvolume_timer.timeout.get().append(self.volume_down)
		self.startTimer2 = eTimer()
		self.startTimer2.callback.append(self.startKeyTimer)

	def cancelShutDown(self):
		from Screens.Standby import inStandby
		if not inStandby:
			self.stopKeyTimer()
			self.asdvolume_timer.stop()
			self.volctrl.setVolume(self.org_volume,self.org_volume)
			self.setHelligkeit(self.bgr)
			self.startKeyTimer()
		else:
			self.stopTimer()
			self.startTimer()

	def setHelligkeit(self,wert=0):
		if wert>0:
			open("/proc/stb/vmpeg/0/pep_brightness", "w").write("%0.8X" % int(wert*256))


	def doShutDown(self):
		do_shutdown = True
		if config.plugins.softsleepFS.disable_net_device.value and checkIP(config.plugins.softsleepFS.net_device.value):
			print ("[softsleepFS] network device is not down  --> ignore shutdown callback")
			do_shutdown = False
		if config.plugins.softsleepFS.exclude_time_off.value:
			begin = config.plugins.softsleepFS.exclude_time_off_begin.value
			end = config.plugins.softsleepFS.exclude_time_off_end.value
			if checkExcludeTime(begin, end):
				print ("[softsleepFS] shutdown timer end but we are in exclude interval --> ignore power off")
				do_shutdown = False
		
		if config.plugins.softsleepFS.epgrefresh.value == True and os_path.exists("/usr/lib/enigma2/python/Plugins/Extensions/EPGRefresh/EPGRefresh.py"):
			begin = config.plugins.epgrefresh.begin.value
			end = config.plugins.epgrefresh.end.value
			if checkExcludeTime(begin, end):
				print ("[softsleepFS] in EPGRefresh interval => restart of Timer")
				do_shutdown = False
		if config.plugins.softsleepFS.disable_hdd.value and checkHardDisk():
			print ("[softsleepFS] At least one hard disk is active  --> ignore shutdown callback")
			do_shutdown = False
		if do_shutdown:
			print ("[softsleepFS] PowerOff STB")
			session.open(Screens.Standby.Standby)
			self.asdvolume_timer.stop()
			session.open(Screens.Standby.TryQuitMainloop,1)
		else:
			self.cancelShutDown()

	def enterStandBy(self):
		print ("[softsleepFS] STANDBY . . . ")
		session.open(Screens.Standby.Standby)
		self.asdvolume_timer.stop()
		self.volctrl.setVolume(self.org_volume,self.org_volume)
		self.setHelligkeit(self.bgr)

	def startTimer(self):
		if config.plugins.softsleepFS.autostart.value == True:
			print ("[softsleepFS] Starting ShutDownTimer")
			shutdowntime = config.plugins.softsleepFS.time.value*60000
			self.softsleepFSTimer = eTimer()
			self.softsleepFSTimer.start(shutdowntime, True)
			self.softsleepFSTimer.callback.append(shutdownactionsfs.doShutDown)

	def stopTimer(self):
		try:
			if self.softsleepFSTimer.isActive():
				print ("[softsleepFS] Stopping ShutDownTimer")
				self.softsleepFSTimer.stop()
		except:
			print ("[softsleepFS] No ShutDownTimer to stop")

	def startKeyTimer(self,endtime=None): 
		if config.plugins.softsleepFS.enableinactivity.value == True and not no_system_shut:
			start_fail=False
			leng=None
			max=int(config.plugins.softsleepFS.wait_max.value)*60
			debtxt=""
			nowtime=int(time())
			if nowtime<1000:
				start_fail=True
			else:
				min_wait=False
				if config.plugins.softsleepFS.wait_for_end.value:
					self.startTimer2.stop()
					endcheck=self.check_endtime()
					endtime=endcheck[0]
					name= endcheck[1]
					art= endcheck[2]
					if not endtime: 
						start_fail=True
					else:
						leng=int(endtime-nowtime)
						if leng<60:leng=60
						min_leng=int(config.plugins.softsleepFS.wait_min.value)*60
						debtxt+=str(art)+", leng: "+str(leng)+", max: "+str(max)+"\n"
						if art=="sender" and leng < min_leng:
							min_wait=True
						elif max>0 and (leng>max or (art=="file" and leng<=min_leng):
							leng=max
			if start_fail:
				self.startTimer2.startLongTimer(5)
				debtxt+="wait for data, 5 sec\n"
			elif min_wait:
				debtxt+="minimal time, first wait for next event: "+datetime.datetime.fromtimestamp(int(time()+leng)).strftime('%H:%M:%S') +", "+str(leng/60)+" minutes\n"
				if leng>0:
					self.startTimer2.startLongTimer(leng+60)
			else:
				inactivetime=None

				if leng:
					inactivetime=leng*1000
					r="next event: (wait for end until): "
					t=leng
				else:
					inactivetime = config.plugins.softsleepFS.inactivetime.value
					inactivetime=inactivetime*60000
					r="next event: "
					t=config.plugins.softsleepFS.inactivetime.value*60
				if inactivetime and inactivetime>0:
					try:
						debtxt+=r+ datetime.datetime.fromtimestamp(int(time()+t)).strftime('%H:%M:%S') +", "+str(inactivetime/60000)+" minutes\n"
						self.softsleepFSKeyTimer = eTimer()
						self.softsleepFSKeyTimer.start(inactivetime, True)
						self.softsleepFSKeyTimer.callback.append(shutdownactionsfs.endKeyTimer)
					except Exception as e:
						if config.plugins.softsleepFS.debug.value:
							f=open("/var/volatile/log/softsleepFS","a")
							f.write(str(e)+"\n")
							f.close()
				else:
					debtxt+="no inactive time set\n"
			if config.plugins.softsleepFS.debug.value:
				f=open("/var/volatile/log/softsleepFS","a")
				f.write(debtxt)
				f.close()

	def stopKeyTimer(self):
		try:
			self.softsleepFSKeyTimer.stop()
			self.asdvolume_timer.stop()
			self.volctrl.setVolume(self.org_volume,self.org_volume)
			self.setHelligkeit(self.bgr)
		except:
			print ("[softsleepFS] No inactivity timer to stop")

	def endKeyTimer(self):
		do_action = True
		if config.plugins.softsleepFS.inactivityaction.value == "deepstandby"  and config.plugins.softsleepFS.disable_net_device.value and checkIP(config.plugins.softsleepFS.net_device.value):
			print ("[softsleepFS] network device is not down  --> ignore shutdown callback")
			do_action = False
		if config.plugins.softsleepFS.disable_at_ts.value:
			running_service = session.nav.getCurrentService()
			timeshift_service = running_service and running_service.timeshift()
			if timeshift_service and timeshift_service.isTimeshiftActive():
				print ("[softsleepFS] inactivity timer end but timeshift is active --> ignore inactivity action")
				do_action = False
		if config.plugins.softsleepFS.exclude_time_in.value:
			begin = config.plugins.softsleepFS.exclude_time_in_begin.value
			end = config.plugins.softsleepFS.exclude_time_in_end.value
			if checkExcludeTime(begin, end):
				print ("[softsleepFS] inactivity timer end but we are in exclude interval --> ignore inactivity action")
				do_action = False
		if do_action:
			if config.plugins.softsleepFS.inactivitymessage.value == True:
				self.asdkeyaction = None
				if config.plugins.softsleepFS.inactivityaction.value == "standby":
					self.asdkeyaction = _("Go to standby")
				elif config.plugins.softsleepFS.inactivityaction.value == "deepstandby":
					self.asdkeyaction = _("Power off STB")
				self.org_volume = int(self.volctrl.getVolume())
				self.setHelligkeit(40)
				#open("/proc/stb/vmpeg/0/pep_brightness", "w").write("%0.8X" % int(40*256))
				if config.plugins.softsleepFS.volsteps.value:
					self.vol_steps= config.plugins.softsleepFS.volsteps.value
					self.volume_down()
				print ("autshotdownFS message")
				if not self.message:
					self.message=True
					session.openWithCallback(shutdownactionsfs.actionEndKeyTimer, asdMessageBox, _("softsleepFS: %s ?") % self.asdkeyaction, timeout=config.plugins.softsleepFS.messagetimeout.value) # % self.asdkeyaction
			else:
				res = True
				shutdownactionsfs.actionEndKeyTimer(res)

	def actionEndKeyTimer(self, res):
		self.message=None
		if res == True:
			if config.plugins.softsleepFS.inactivityaction.value == "standby":
				print ("[softsleepFS] inactivity timer end => go to standby")
				self.enterStandBy()
			elif config.plugins.softsleepFS.inactivityaction.value == "deepstandby":
				print ("[softsleepFS] inactivity timer end => shutdown")
				self.doShutDown()
		else:
			pass

	def volume_down(self):
			akt_volume = int(self.volctrl.getVolume())
			if akt_volume >0:
				self.volctrl.setVolume(akt_volume-1, akt_volume-1)
				self.asdvolume_timer.startLongTimer(self.vol_steps)
			else:
				try:
					self.asdvolume_timer.stop()
				except:
					pass

	def check_endtime(self):
		endtime=None
		event_name=None
		art=None
		sref = session.nav.getCurrentlyPlayingServiceReference()
		if sref:
			art = "sender"
			try:
				ref= sref.toString()
				if sref and "0:0:0:0:0:0:0:0:0:" in ref:
					art="file"
				elif ref.startswith("4097:0"):
					art=None
					do_action = True
				else:
					art = "sender"
			except Exception as e:
				if config.plugins.softsleepFS.debug.value:
					f=open("/var/volatile/log/softsleepFS","a")
					f.write(str(e)+"\n")
					f.close()
			if art is not None:
				s=session.nav.getCurrentService()
				if art=="file":
					seek = s and s.seek()
					if seek:
						vlength = seek.getLength()
						vpos = seek.getPlayPosition()
						if not vlength[0] and not vpos[0]:
							vlength=vlength[1]/90000
						try:
							vpos=int(vpos[1]/90000)
							endtime=time()+vlength-vpos
						except:
							endtime=None
				else:
					info1 = s and s.info()
					event1 = info1 and info1.getEvent(0)
					if event1:event_name = event1.getEventName()
					event2 = info1 and info1.getEvent(1)
					if event2:
						endtime = event2.getBeginTime()
					elif event1:
						start = event1.getBeginTime()
						leng = event1.getDuration()
						if start and leng:
							endtime = start + leng
		return (endtime,event_name,art)

shutdownactionsfs = softsleepFSactionsfs()

def autostart(reason, **kwargs):
	global session
	if "session" in kwargs and reason == 0:
		session = kwargs["session"]
		print ("[softsleepFS] start....")
		config.misc.standbyCounter.addNotifier(standbyCounterChanged, initial_call = False)
		f=open("/var/volatile/log/softsleepFS","w")
		f.close()
		eActionMap.getInstance().bindAction('', -0x7FFFFFFF, keyPressed)
		shutdownactionsfs.startKeyTimer()

def keyPressed(key, flag):
	if config.plugins.softsleepFS.enableinactivity.value == True:
		from Screens.Standby import inStandby
		if not inStandby:
			if flag == 1:
				shutdownactionsfs.stopKeyTimer()
				shutdownactionsfs.startKeyTimer()
	return 0

def standbyCounterChanged(configElement):
	print ("[softsleepFS] go to standby . . .")
	if leaveStandby not in Screens.Standby.inStandby.onClose:
		Screens.Standby.inStandby.onClose.append(leaveStandby)
	shutdownactionsfs.startTimer()
	shutdownactionsfs.stopKeyTimer()

def leaveStandby():
	print ("[softsleepFS] leave standby . . .")
	shutdownactionsfs.stopTimer()
	f=open("/var/volatile/log/softsleepFS","w")
	f.close()
	shutdownactionsfs.startKeyTimer()

def main(session, **kwargs):
	print ("[softsleepFS] Open Configuration")
	session.open(softsleepFSConfiguration)

def startSetup(menuid):
	if menuid != "shutdown":
		return [ ]
	return [(_("AutoShutDown settings")+" +" , main, "softsleepFS_setup", 60)]

def Plugins(**kwargs):
	list=[]
	list=[PluginDescriptor(name="softsleepFS"+" "+_("Setup"), description=_("configure automated power off / standby"), where = PluginDescriptor.WHERE_MENU, fnc=startSetup)]

	if not no_system_shut:
		list.append(PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = autostart))
	if config.plugins.softsleepFS.plugin.value:
			list.append(PluginDescriptor(name="softsleepFS"+" "+_("Setup"), description=_("configure automated power off / standby"), where = PluginDescriptor.WHERE_PLUGINMENU, icon="softsleepFS.png", fnc=main))
			list.append(PluginDescriptor(name="softsleepFS"+" "+_("Setup"), description=_("configure automated power off / standby"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main))
	return list 

class softsleepFSConfiguration(Screen, ConfigListScreen):

	if getDesktop(0).size().width() < 1800:
		skin = """
		<screen position="center,center" size="820,500" title="softsleepFS Setup" >
		<widget name="config" position="10,10" size="800,450" itemHeight="32" font="Regular;22" scrollbarMode="showOnDemand" enableWrapAround="1"/>
		<ePixmap pixmap="skin_default/buttons/key_red.png" zPosition="2" position="10,470" size="40,25" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/key_green.png" zPosition="2" position="170,470" size="40,25" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/key_yellow.png" zPosition="2" position="320,470" size="240,25" alphatest="on" />
		<widget name="buttonred" position="55,470" size="100,20" valign="center" halign="left" zPosition="2" foregroundColor="white" font="Regular;18"/>
		<widget name="buttongreen" position="215,470" size="70,20" valign="center" halign="left" zPosition="2" foregroundColor="white" font="Regular;18"/>
		<widget name="buttonyellow" position="365,470" size="100,20" valign="center" halign="left" zPosition="2" foregroundColor="white" font="Regular;18"/>
		</screen>"""  
	else:
		skin = """
		<screen position="center,center" size="1200,800" title="softsleepFS Setup" >
		<widget name="config" position="10,10" size="1180,720" itemHeight="42" font="Regular;35" scrollbarMode="showOnDemand" enableWrapAround="1"/>
		<ePixmap pixmap="skin_default/buttons/key_red.png" zPosition="2" position="10,770" size="40,25" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/key_green.png" zPosition="2" position="280,770" size="40,25" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/key_yellow.png" zPosition="2" position="550,770" size="40,25" alphatest="on" />
		<widget name="buttonred" position="55,765" size="200,35" valign="center" halign="left" zPosition="2" foregroundColor="white" font="Regular;30"/>
		<widget name="buttongreen" position="335,765" size="200,35" valign="center" halign="left" zPosition="2" foregroundColor="white" font="Regular;30"/>
		<widget name="buttonyellow" position="600,765" size="200,35" valign="center" halign="left" zPosition="2" foregroundColor="white" font="Regular;30"/>
		</screen>"""   

	def __init__(self, session, args = 0):
		self.session = session
		Screen.__init__(self, session)
		self.createConfigList()
		self.onShown.append(self.setWindowTitle)
		ConfigListScreen.__init__(self, self.list, session = self.session, on_change = self.changedEntry)
		self["buttonred"] = Label(_("Exit"))
		self["buttongreen"] = Label(_("OK"))
		self["buttonyellow"] = Label(_("Default"))
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"green": self.save,
				"red": self.cancel,
				"yellow": self.revert,
				"save": self.save,
				"cancel": self.cancel,
				"ok": self.keyOk,
			}, -2)

	def createConfigList(self):
		self.list = []
		if no_system_shut:
			self.list.append(getConfigListEntry(_("Please first deactivate System-autoshutdown"), config.plugins.softsleepFS.fake_entry))
			self.list.append(getConfigListEntry(_("and restart your Box"), config.plugins.softsleepFS.fake_entry))
		else:
			self.list.append(getConfigListEntry("---------- " + _("Configuration for automatic power off in standby"), config.plugins.softsleepFS.fake_entry))
			self.list.append(getConfigListEntry(_("Enable automatic power off in standby:"), config.plugins.softsleepFS.autostart))
		if config.plugins.softsleepFS.autostart.value == True:
			self.list.append(getConfigListEntry(_("Time in standby for power off (min):"), config.plugins.softsleepFS.time))
			self.list.append(getConfigListEntry(_("Disable power off for given interval:"), config.plugins.softsleepFS.exclude_time_off))
			if config.plugins.softsleepFS.exclude_time_off.value:
				self.list.append(getConfigListEntry(_("Begin of excluded interval (hh:mm):"), config.plugins.softsleepFS.exclude_time_off_begin))
				self.list.append(getConfigListEntry(_("End of excluded interval (hh:mm):"), config.plugins.softsleepFS.exclude_time_off_end))
		self.list.append(getConfigListEntry(" ", config.plugins.softsleepFS.fake_entry))
		self.list.append(getConfigListEntry("---------- " + _("Configuration for inactivity actions"), config.plugins.softsleepFS.fake_entry))
		self.list.append(getConfigListEntry(_("Enable action after inactivity:"), config.plugins.softsleepFS.enableinactivity))
		if config.plugins.softsleepFS.enableinactivity.value == True:
			if config.plugins.softsleepFS.wait_for_end.value != True:
				self.list.append(getConfigListEntry(_("Time for inactivity (min):"), config.plugins.softsleepFS.inactivetime))
			self.list.append(getConfigListEntry(_("Wait for the end of the program:"), config.plugins.softsleepFS.wait_for_end)) #edit by s
			if config.plugins.softsleepFS.wait_for_end.value == True:
				self.list.append(getConfigListEntry(_("Minimum remaining length (min):"), config.plugins.softsleepFS.wait_min))
				self.list.append(getConfigListEntry(_("Force switch off after (min):"), config.plugins.softsleepFS.wait_max))
			self.list.append(getConfigListEntry(_("Action for inactivity:"), config.plugins.softsleepFS.inactivityaction))
			self.list.append(getConfigListEntry(_("Lower Volume (sec.):"), config.plugins.softsleepFS.volsteps))
			self.list.append(getConfigListEntry(_("Disable inactivity action at timeshift:"), config.plugins.softsleepFS.disable_at_ts))

			self.list.append(getConfigListEntry(_("Show message before inactivity action:"), config.plugins.softsleepFS.inactivitymessage))
			if config.plugins.softsleepFS.inactivitymessage.value == True:
				self.list.append(getConfigListEntry(_("Message timeout (sec):"), config.plugins.softsleepFS.messagetimeout))
			self.list.append(getConfigListEntry(_("Disable inactivity action for given interval:"), config.plugins.softsleepFS.exclude_time_in))
			if config.plugins.softsleepFS.exclude_time_in.value:
				self.list.append(getConfigListEntry(_("Begin of excluded interval (hh:mm):"), config.plugins.softsleepFS.exclude_time_in_begin))
				self.list.append(getConfigListEntry(_("End of excluded interval (hh:mm):"), config.plugins.softsleepFS.exclude_time_in_end))
		self.list.append(getConfigListEntry(" ", config.plugins.softsleepFS.fake_entry))
		self.list.append(getConfigListEntry("---------- " + _("Common configuration"), config.plugins.softsleepFS.fake_entry))
		if config.plugins.softsleepFS.enableinactivity.value or config.plugins.softsleepFS.autostart.value:
			self.list.append(getConfigListEntry(_("Disable power off in EPGRefresh interval:"), config.plugins.softsleepFS.epgrefresh))
			self.list.append(getConfigListEntry(_("Disable power off until a hard disk is active:"), config.plugins.softsleepFS.disable_hdd))
			self.list.append(getConfigListEntry(_("Disable power off until a given device is pingable:"), config.plugins.softsleepFS.disable_net_device))
			if config.plugins.softsleepFS.disable_net_device.value:
				self.list.append(getConfigListEntry(_("IP address of network device:"), config.plugins.softsleepFS.net_device))
		self.list.append(getConfigListEntry(_("Show in Extensions/Plugins:"), config.plugins.softsleepFS.plugin))
		self.list.append(getConfigListEntry(_("debug:"), config.plugins.softsleepFS.debug))

	def changedEntry(self):
		shutdownactionsfs.stopKeyTimer()
		self.createConfigList()
		self["config"].setList(self.list)
		shutdownactionsfs.startKeyTimer()

	def setWindowTitle(self):
		self.setTitle(_("softsleepFS")+" "+str(version)+" - "+_(" Setup"))

	def keyOk(self):
		pass

	def save(self, ret = True):
		if not no_system_shut:
			shutdownactionsfs.stopKeyTimer()
		for x in self["config"].list:
			x[1].save()
		self.changedEntry()
		shutdownactionsfs.startKeyTimer()
		if ret:
			self.close()

	def cancel(self):
		if not no_system_shut and self["config"].isChanged():
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"), MessageBox.TYPE_YESNO, default = False)
		else:
			for x in self["config"].list:
				x[1].cancel()
			self.close(False,self.session)

	def cancelConfirm(self, result):
		if result is None or result is False:
			print ("[softsleepFS] Cancel not confirmed.")
		else:
			print ("[softsleepFS] Cancel confirmed. Configchanges will be lost.")
			for x in self["config"].list:
				x[1].cancel()
			self.close(False,self.session)

	def revert(self):
		if not no_system_shut:
			self.session.openWithCallback(self.keyYellowConfirm, MessageBox, _("Reset softsleepFS settings to defaults?"), MessageBox.TYPE_YESNO, timeout = 20, default = False)

	def keyYellowConfirm(self, confirmed):
		if not no_system_shut:
			if not confirmed:
				print ("[softsleepFS] Reset to defaults not confirmed.")
			else:
				print ("[softsleepFS] Setting Configuration to defaults.")
				config.plugins.softsleepFS.time.setValue(120)
				config.plugins.softsleepFS.min_starttime.steValue(20)
				config.plugins.softsleepFS.autostart.setValue(0)
				config.plugins.softsleepFS.enableinactivity.setValue(0)
				config.plugins.softsleepFS.inactivetime.setValue(300)
				config.plugins.softsleepFS.inactivityaction.setValue("standby")
				config.plugins.softsleepFS.epgrefresh.setValue(1)
				config.plugins.softsleepFS.plugin.setValue(0)
				config.plugins.softsleepFS.inactivitymessage.setValue(1)
				config.plugins.softsleepFS.wait_for_end.setValue(0) #edit by s
				config.plugins.softsleepFS.wait_max.setValue(120)
				config.plugins.softsleepFS.wait_min.setValue(15)
				config.plugins.softsleepFS.messagetimeout.setValue(20)
				config.plugins.softsleepFS.disable_at_ts.setValue(0)
				config.plugins.softsleepFS.disable_net_device.setValue(0)
				config.plugins.softsleepFS.disable_hdd.setValue(0)
				config.plugins.softsleepFS.net_device.setValue([0,0,0,0])
				config.plugins.softsleepFS.exclude_time_in.setValue(0)
				config.plugins.softsleepFS.exclude_time_in_begin.setValue([20, 0])
				config.plugins.softsleepFS.exclude_time_in_end.setValue([0, 0])
				config.plugins.softsleepFS.exclude_time_off.setValue(0)
				config.plugins.softsleepFS.exclude_time_off_begin.setValue([20, 0])
				config.plugins.softsleepFS.exclude_time_off_end.setValue([0, 0])
				config.plugins.softsleepFS.debug.setValue(0)
				self.save(False)

