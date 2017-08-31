# -*- coding: utf-8 -*-
import os
import re
import time
import subprocess
import threading
import shlex
import Queue
from sys import argv
import sys, os
from optparse import OptionParser
import getpass
import threading
import inspect
import ctypes 

def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble, 
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")

def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)

def getlog():
	global poll_alive
	log_process=subprocess.Popen("adb logcat -v threadtime",stdout=subprocess.PIPE,stderr=subprocess.STDOUT,shell=True)
	pull_report = "adb pull /sdcard/TunnyBrowser/feedback/."
	if os.path.exists(log_dirs) == False :
                os.makedirs(log_dirs)
	while log_process.poll() == None:
		poll_alive = True
		line = log_process.stdout.readline()
		native_crash = re.compile(r".*Fatal.signal.*",re.I)
		java_crash = re.compile(r".*E.AndroidRuntime:.(Android|java).*",re.I)
		#java_crash = re.compile(r".*E.AndroidRuntime:.(Android|java|.at).*",re.I)
		anr_process = re.compile(r".*E.ActivityManager.*ANR.in")
		#switch
		if java_crash.search(line)!= None:
			current_time = time.strftime('%H-%M',time.localtime(time.time()))
			pull_java_crash_log = '%s "%s\%s"' %(pull_report,log_dirs,current_time)
			#pull_java_crash_log = pull_report + "%s\%s" + log_dirs + "/" + current_time
			adb_pull_java_crash_log = subprocess.Popen(pull_java_crash_log, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
			#os.popen('adb pull /sdcard/TunnyBrowser/feedback/. "%s\%s"' %(log_dirs,current_time))
			os.popen('adb logcat -v threadtime -d >"%s\%s_java_crash.txt"' %(log_dirs,current_time))
		elif native_crash.search(line) != None:
			current_time = time.strftime('%H-%M',time.localtime(time.time()))
			os.popen('adb logcat -v threadtime -d >"%s\%s_native_crash.txt"' %(log_dirs,current_time))
			os.popen('adb pull /sdcard/TunnyBrowser/feedback/. "%s\%s"' %(log_dirs,current_time))
		elif anr_process.search(line)!= None:
			current_time = time.strftime('%H-%M',time.localtime(time.time()))
			os.popen('adb logcat -v threadtime -d >"%s\%s_anr.txt"' %(log_dirs,current_time))
			os.popen('adb pull /data/anr/. "%s\%s"' %(log_dirs,current_time))
		else:
			pass
	else:
		print time.ctime(),"logcat is disconnect!"
		poll_alive = False




def kill_process(name):
    proc = subprocess.Popen(shlex.split("adb shell ps"), stdout=subprocess.PIPE)
    pid_index = -1
    for line in iter(proc.stdout.readline,''):
        if pid_index == -1:
            lst = line.split()
            for i in range(0, len(lst)):
                if lst[i] == "PID":
                    pid_index = i
                    break
            if pid_index == -1:
                print "Can't get pid from command ps"
        if line.find(name) != -1:
            pid = line.split()[pid_index]
            #print "kill process %s" % pid
            os.system("adb shell kill %s" % pid)

def run_monkey(package):
	ps_list = os.popen('adb shell ps').read()
	if re.search("com.android.commands.monkey",ps_list) != None:
		print "monkey is running"
	else:
		run_monkey = subprocess.Popen('adb shell monkey -p %s -s 600 -v -v \
                --throttle 1000 --ignore-crashes --ignore-timeouts --ignore-security-exceptions\
                 --monitor-native-crashes --pct-syskeys 1 150000 >>sss.txt' %package,stdout=subprocess.PIPE,shell=True)
		print "monkey start"
#threads = []

def waiting_time(totaltime,package):
	run_time = totaltime*3600
	start_time = 0
	monkey_path = r"//share/MemberShare/Dolphin INT Shell Test/Monkey Test/MonkeyTool.apk"
	os.system('adb install -r "%s"' %monkey_path)
	os.popen("adb shell am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -n com.automation.monkeytool/com.automation.monkeytool.TopViewActivity")
	os.popen("adb logcat -c")
	os.popen("adb shell pm grant %s permission.READ_LOGS" %package)
	os.popen("adb shell rm -r /sdcard/TunnyBrowser/feedback/")
	startfile = "%s\%s_teststart.txt" %(log_dirs,time.strftime('%H-%M',time.localtime(time.time())))
	start = open(startfile,"w")
	start.close()
	#wait_log = threading.Thread(target=getlog,args=(package,))
	threading.Thread(target=getlog).setDaemon(True)
	threading.Thread(target=getlog).start()
	while start_time < run_time:
		run_monkey(package)
		time.sleep(1800)
		print poll_alive
		if poll_alive == False:
			threading.Thread(target=getlog).start()
		start_time += 1800
	else:
		endfile = "%s/%s_testend" %(log_dirs,time.strftime('%H-%M',time.localtime(time.time())))
		end = open(endfile,"w")
		end.close()
		#卸载monkeytools
		os.popen("adb uninstall com.automation.monkeytool")
		#杀掉monkey程序
		print "test end"
		kill_process("commands.monkey")
		os.popen("taskkill /F /im adb.exe")
		


if __name__ == '__main__':
	if len(sys.argv)<1:
		print "please input test version and runtime;like as python monkey.py en 10"
		sys.exit(1)
	company = sys.argv[1]
	global package
	if company == "en":
		package = "mobi.mgeek.TunnyBrowser"
	elif company == "express":
		package = "com.dolphin.browser.express.web"
	elif company == "jp":
		package = "com.dolphin.browser.android.jp"
	elif company == "newhome":
		package = "com.dolphin.browser.id"
	elif company == "discover":
		package = "com.dolphin.web.browser.android"
	elif company == "uc":
		package = "com.UCMobile.intl"
	elif company == "mobo":
		package = "com.mobogenie"
	elif company == "cb":
		package = "com.cyou.batterymaster"
		
	totaltime = int(sys.argv[2])
	global log_dirs
	log_dirs = r"\\share\membershare\Dolphin INT Shell Test\Monkey Test\%s\%s" %(time.strftime('%Y-%m-%d',time.localtime(time.time())),getpass.getuser())
        if os.path.exists(log_dirs) == False :
            os.makedirs(log_dirs);
	waiting_time(totaltime,package)
