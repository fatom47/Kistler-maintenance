### Gets peak kN value from local maximum ###

import glob, os, datetime, re, shutil, socket, time as timer
from ftplib import FTP

limit = 95.0 # [%]
currentFile = "" # previous csv
prevPeak = 0.0 # previous peak value
newPeak = 0.0 # peak value of the newest file
prevStop = 0.0 # previous stop signal
newStop = 0.0 # stop value of the newest file
latest = datetime.datetime.now() # to prevent fake alert after app start
port = 12345 # port on which app should connect
state = 'N/A' # state to send
print(u'This window is needed for run of Oil watchdog application. Please, do not turn it off.\nToto okno je nezbytné pro běh aplikace Oil watchdog. Prosím, nevypínejte ho.') # u for Unicode
print('Version from 26.3.2021')
# Load settings from text file
try:
    settFile = open("./conf/Watchdog.txt","r")
    limit = float(settFile.readline()[5:])
    settFile.close()
    print (limit)
except:
    print("Settings file does not exist or is empty! Default values are used.")

# Log the need for oiling
def oiLog(now,fuel,curFile,result,prevPeak,newPeak):
    f = open("./conf/Oilog.csv","a")
    f.write("\n"+str(now)+";"+fuel+";"+curFile+";"+result+";"+str(prevPeak)+';'+str(newPeak))
    f.close()

# Locally save not OK curve
def localSave(result):
    global currentFile
    shutil.copyfile('./'+currentFile, './notOK/'+currentFile)

# Delete stored files
def eraseCSVs():
    for item in os.listdir("./"):
        if  item.endswith(".csv") or item.endswith(".~csv~"): # ghosts
            os.remove("./"+item)

# Connect to FTP server and download the latest file
def download():
    global currentFile
    ftp=FTP('10.20.30.40')
    ftp.login('name','password')
    ftp.cwd('work_dir')
    # The most recent folder
    entries = list(ftp.mlsd())
    # Only interested in directories
    entries = [entry for entry in entries if entry[1]["type"] == "dir"]
    # Sort by timestamp
    entries.sort(key = lambda entry: entry[1]['modify'], reverse = True)
    # Pick the first one
    latest_folder = entries[0][0]
    #print(latest_folder)
    ftp.cwd(latest_folder)
    # The most recent file
    entries = list(ftp.mlsd())
    entries.sort(key = lambda entry: entry[1]['modify'], reverse = True)
    latest_name = entries[0][0]
    #print(latest_name)
    # Download the latest file
    if currentFile != latest_name:
        eraseCSVs()
        timer.sleep(0.15)
        ftp.retrbinary("RETR " + latest_name,open(latest_name,'wb').write)
    ftp.quit()

# Curve processing
def curve():
    startTime = timer.time()
    global currentFile, latest, prevPeak, newPeak, prevStop, newStop, state

    try:
        download()
        list_of_files = glob.glob('*.csv') # * means all if need specific format then *.csv
        latest_file = max(list_of_files, key=os.path.getctime)
        timer.sleep(0.15)
        #print (latest_file)
        if latest_file != currentFile:
            #latest = datetime.datetime.now()
            currentFile = latest_file
            prevPeak = newPeak
            prevStop = newStop
            num_lines=sum(1 for line in open(currentFile))
            # 1149 is full house
            if num_lines == 1149:
                r = 1 # row number
                newPeak = 0.0 # reset variable
                f=open(currentFile,"r")
                
                for x in f:
                    if r==5:
                        fuel=x[22:28] # Diesel x Benzin
                    elif r==10:
                        regular = re.search(';(.+?);',x)
                        if regular:
                            result = regular.group(1) # Result
                        else:
                            result = 'N/A'
                    elif r==36:
                        newStop = float(x[17:21].replace(",",".")) # Stop signal [kN]
                    elif r>1120 and r<1138: # arc local maximum
                        number = float(x[6:10].replace(",","."))
                        if number>newPeak:
                            newPeak=number

                    r=r+1
                
                f.close()
                try:
                    if result != 'OK':
                        localSave(result)
                    
                    avgPeak = (newPeak + prevPeak)/2.0 # Moving average of the last 2 humps
                    avgStop = (newStop + prevStop)/2.0 # Moving average of the last 2 stop signals because of readjustment
                    warning = avgStop*limit*0.01
                    print('Hump ratio: '+str(round(100*avgPeak/avgStop,2))+' %')
                    if avgPeak<warning and result=='OK':
                        print('OK')
                        state = 'OK'
                    else:
                        print('OIL')
                        state = 'OIL'
                        oiLog(datetime.datetime.now(),fuel,currentFile,result,prevPeak,newPeak)
                except:
                    print('Er')
                    state = 'N/A'
            else:
                print('\n' + str(datetime.datetime.now()) + ': Unknown file format - cannot process: ' + str(currentFile))

##        else:
##            print('Nothing to do')

    except:
        print('Err')
        state = 'N/A'
    
    executionTime = (timer.time() - startTime)
    print('Execution time in seconds: ' + str(executionTime))

s = socket.socket() # create a socket object
print ("Socket successfully created")
s.bind(('', port)) # empty string makes the server listen to requests coming from other computers on the network
print ("socket binded to %s" %(port))
s.listen(3) # put the socket into listening mode
print ("socket is listening")    

while True: # a forever loop until we interrupt it or an error occurs
    print('----------------------------------------------')
    c, addr = s.accept() # Establish connection with client.
    print ('Got connection from', addr )
    print('Request was sent at '+str(datetime.datetime.now()))
    curve()
    c.send(state.encode('utf-8'))  # send a state to the client
    #c.send(b'Thank you for connecting')
    c.close() # Close the connection with the client
