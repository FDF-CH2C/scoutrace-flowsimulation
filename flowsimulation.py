# -*- coding: utf-8 -*-
"""flowsimulation.py
Setup course model and simulate with a number of teams.
Output waiting times and completion times"""

import random
import simpy
import numpy
import matplotlib.pyplot as pyplot
import matplotlib.patches as mpatches

tStart=7*60               #07:00
tStartSimul=3             #No. of teams to start simultaneously
tStartInterval=15         #Time between starting teams
tEnd=31*60                #07:00 next day
minSpeed=1.5              #km/h
minSpeedOB=2              #km/h
maxSpeed=2.5              #km/h
maxSpeedOB=4              #km/h
r=random.Random(3823)

class Activity(object):
    def __init__(self, capacity, minDuration, maxDuration, name):
        self.capacity = capacity
        self.minDuration = minDuration
        self.maxDuration = maxDuration
        self.name = name
        self.accFirstTeamStart = []
        self.accLastTeamEnd = []
        self.accWaits = []
        self.accMaxQueue = []
        
    def setup(self, env):
        self.env = env
        self.slots = simpy.Resource(env, self.capacity)
        self.firstTeamStart = 0
        self.lastTeamEnd = 0
        self.waits = []
        self.maxQueue = 0

    def acceptTeam(self, team):
        tIn=self.env.now

        #print "%s begins %s at %s" % (team.name, self.name, formatTime(tIn))
        if self.firstTeamStart == 0:
            self.firstTeamStart = tIn

        if self.minDuration is None:
            yield self.env.timeout(0)
        else:
            #TODO: use random.normalvariate and express min/max duration as mean/std.dev
            yield self.env.timeout(r.uniform(self.minDuration, self.maxDuration))
        
        tOut=self.env.now
        #print "%s completed %s at %s" % (team.name, self.name, formatTime(tOut))
        self.lastTeamEnd = tOut

    def addWaitTime(self, waitTime):
        self.waits.append(waitTime)

    def updateMaxQueue(self):
        self.maxQueue = max(len(self.slots.queue), self.maxQueue)

    def persistStats(self):
        self.accFirstTeamStart.append(self.firstTeamStart)
        self.accLastTeamEnd.append(self.lastTeamEnd)
        self.accWaits.append(self.waits)
        self.accMaxQueue.append(self.maxQueue-1) #Due to updating queue before "yield", value is one off

class Transport(object):
    def __init__(self, distance):
        self.distance = distance

class Team:
    def __init__(self, name, teamType, course, startTime):
        self.name = name
        self.teamType = teamType #TODO: Do we need to save this?
        self.course = course
        self.startTime = startTime
        if teamType=="V":
            self.minSpeed = minSpeed
            self.maxSpeed = maxSpeed
        else:
            self.minSpeed = minSpeedOB
            self.maxSpeed = maxSpeedOB
        self.accWaits = []
        self.accEndTime = []

    def setup(self, env):
        self.env = env
        self.waits = []
        self.endTime = 0
        
    def start(self, env):
        for element in self.course:
            if type(element) is Transport:
                #TODO: Better model for speed, perhaps as function of time of day?
                walkingTime = r.uniform(element.distance/self.minSpeed, element.distance/self.maxSpeed)*60
                #print "Team %s walks %d km in %s" % (self.name, element.distance, formatTime(walkingTime))
                yield self.env.timeout(walkingTime)

            if type(element) is Activity:   
                with element.slots.request() as request:
                    arrivalTime = env.now
                    element.updateMaxQueue()
                    #print "%s arrives at %s at %s" % (self.name, element.name, formatTime(arrivalTime))
                    yield request
                    waitTime = env.now-arrivalTime
                    self.waits.append(waitTime)
                    element.addWaitTime(waitTime)
                    yield env.process(element.acceptTeam(self))
        self.endTime = env.now
        #print "%s: Start=%s, Finish=%s, Total wait=%d minutes" % (self.name, formatTime(self.startTime), formatTime(self.endTime), self.totalWaitTime)

    def persistStats(self):
        self.accWaits.append(self.waits)
        self.accEndTime.append(self.endTime)

def plotActivityStats(activities, title):
    #TODO: Plot as subplots on same figure
    myFontdict={'fontsize': 8}
    
    dataWait = [] #List of activity wait lists
    dataStartEnd = [] #List of [start(5,10,25th percentile),end(75,90,95th percentile)] per activity
    dataMaxQueue = []
    labels = []
    noOfRuns = len(activities[0].accWaits)
    for a in activities:
        dataStartEnd.append([numpy.percentile(a.accFirstTeamStart,[5,10,25,50]), numpy.percentile(a.accLastTeamEnd,[75,90,95,50])])
        dataMaxQueue.append(a.accMaxQueue)
        actWaits = []
        teamsArrived = []
        for list in a.accWaits:
            actWaits.extend(list)
            teamsArrived.append(len(list))                       
        dataWait.append(actWaits)
        labels.append("%s (%.2f hold),\nKapacitet=%d, [%s;%s]" % (a.name, avg(teamsArrived), a.capacity, a.minDuration, a.maxDuration))
#       print("%s: Start=%s, End=%s, Total wait=%s, avg. wait=%s, max queue=%s" % (a.name, minMaxAvgTime(a.accFirstTeamStart), minMaxAvgTime(a.accLastTeamEnd), minMaxAvgSumPerRun(a.accWaits), minMaxAvgAvgPerRun(a.accWaits), minMaxAvgFormat(a.accMaxQueue)))
    
    #"Plot" course
    #pyplot.title(title, fontdict=myFontdict)
    
    #Plot total wait time/activity as boxplot
    #figwait = fig.add_subplot(211, label="Samlet ventetid pr. post")
    pyplot.boxplot(dataWait, labels=labels, vert=False)
    pyplot.title("Ventetid pr. post (%d gennemløb)" % noOfRuns)
    pyplot.show()

    #Plot max queue/activity as boxplot
    pyplot.boxplot(dataMaxQueue, labels=labels, vert=False)
    pyplot.title("Længste kø pr. post (%d gennemløb)" % noOfRuns)
    pyplot.show()
    
    #Plot activity start/end times as Gantt chart
    fig = pyplot.figure()
    figgantt = fig.add_subplot(111)
    y = 0
    xmin = tEnd
    xmax = tStart
    for startList, endList in dataStartEnd:
        figgantt.barh(y, endList[0]-startList[0], left=startList[0], alpha=0.3) #5th/95th percentile
        figgantt.barh(y, endList[1]-startList[1], left=startList[1], alpha=0.3) #10th/90th percentile
        figgantt.barh(y, endList[2]-startList[2], left=startList[2], alpha=0.3) #25th/75th percentile
        figgantt.barh(y, endList[3]-startList[3], left=startList[3], alpha=0.3, edgecolor='red') #50th percentile
        y = y+1
        xmin = min(startList[0],xmin)
        xmax = max(endList[0],xmax)

    patch5_95 = mpatches.Patch(alpha=0.3, label='95%')
    patch10_90 = mpatches.Patch(alpha=0.45, label='90%')
    patch25_75 = mpatches.Patch(alpha=0.6, label='75%')
    patch50 = mpatches.Patch(alpha=0.75, edgecolor='red', label='50%')
    pyplot.legend(handles=[patch5_95, patch10_90, patch25_75, patch50])
    
    labelsy = pyplot.yticks(numpy.arange(0.5,len(activities)+0.5),labels)
    pyplot.setp(labelsy)
    figgantt.set_xlim(xmin, xmax)
    figgantt.xaxis.set_major_locator(pyplot.MultipleLocator(60))
    figgantt.xaxis.set_major_formatter(pyplot.FuncFormatter(lambda x,pos: formatTime(x)))
    figgantt.set_title("Åbne- og lukketider pr. post")
    pyplot.show()

def formatTime(timestamp):
    if timestamp is None:
        return 0
    hour = timestamp / 60
    min = timestamp % 60
    return "%02d:%02d" % (hour, min)

def printCourse(course, courseName, noTeams):
    outputStr = "%s (%d hold):\n" % (courseName, noTeams)
    totalDistance = 0
    for element in course:
        if type(element) is Transport:
            outputStr += "-(%d)->" % element.distance
            totalDistance += element.distance
        if type(element) is Activity:
            outputStr += "%s[%d]" % (element.name, element.capacity)
    outputStr += "\nTotal distance: %d" % totalDistance
    return outputStr 

#Helper methods for performing calculations on 1- and 2-dimensional arrays
def avg(list, decimals=2):
    if len(list) > 0:
        return round(sum(list)/len(list), decimals)
    return 0

def minMaxAvg(list):
    return [min(list), max(list), avg(list)] 

def minMaxAvgFormat(list):
    mma = minMaxAvg(list)
    return "(%d/%d/%.2f)" % (mma[0], mma[1], mma[2])

def minMaxAvgTime(list):
    mma = minMaxAvg(list)
    return "(%s/%s/%s)" % (formatTime(mma[0]), formatTime(mma[1]), formatTime(mma[2]))

"""Find min/max/avg of aggregated (summed) lists"""
def minMaxAvgSumPerRun(listOfLists):
    sumList = []
    for list in listOfLists:
        sumList.append(sum(list))
    return minMaxAvgTime(sumList)

"""Find min/max/avg of aggregated (averaged) lists"""
def minMaxAvgAvgPerRun(listOfLists):
    avgList = []
    for list in listOfLists:
        avgList.append(avg(list))
    return minMaxAvgTime(avgList)

def start(env, teams, activities):
    for a in activities:
        a.setup(env)
    for t in teams:
        t.setup(env)
        waitTime = max(0, t.startTime-env.now)
        yield env.timeout(waitTime)
        env.process(t.start(env))

#Create environment
def simulate(noOfRuns, noVTeams, noOBTeams):
    """
    Setup course
    Activity: capacity, min, max, name 
    Transport: distance
    """
    P1 = Activity(6, 5, 15, "Startpost")
    T1 = Transport(2)
    P2 = Activity(3, 15, 25, "Sjov post")
    T2 = Transport(1.5)
    P3 = Activity(2, 15, 25, "Mørk post")
    T3 = Transport(3)
    T3a = Transport(1.5)
    P3a = Activity(1, 25, 40, "OB post")
    T3b = Transport(2.5)
    P4 = Activity(99, 60, 70, "Madpost")
    T4 = Transport(2)
    P5 = Activity(2, 35, 50, "Vandpost")
    T5 = Transport(2)
    P6 = Activity(2, 20, 40, "Mørkepost")
    T6 = Transport(3)
    P6 = Activity(2, 20, 40, "Kodepost")
    T6 = Transport(3)
    T6a = Transport(2)
    P6a = Activity(1, 25, 35, "OB post 2")
    T6b = Transport(3)
    P7 = Activity(99, 5, 20, "Død post")
    T7 = Transport(3)
    P8 = Activity(4, 35, 50, "Raftepost")
    T8 = Transport(3)
    PN = Activity(3, 25, 55, "Forbudt Område")
    TN = Transport(2)
    PX = Activity(99, None, None, "Mål")

    Activities = [P1, P2, P3, P3a, P4, P5, P6, P6a, P7, P8, PN, PX]

    CourseV = [P1,T1,P2,T2,P3,T3,P4,T4,P5,T5,P6,T6,P7,T7,P8,T8,PN,TN,PX]
    CourseOB = [P1,T1,P2,T2,P3,T3a,P3a,T3b,P4,T4,P5,T5,P6,T6a,P6a,T6b,P7,T7,P8,T8,PN,TN,PX]

    print(printCourse(CourseV, "Væbnerrute", noVTeams))
    print(printCourse(CourseOB, "OB-rute", noOBTeams))

    #Setup teams - start 3 teams every 15 minutes
    Teams = []
    startTime = tStart

    teamType="V"
    course=CourseV
    for j in range(noVTeams+noOBTeams):
        Teams.append(Team("Hold %d" % j, teamType, course, startTime))
        if j%tStartSimul==tStartSimul-1:
            startTime+=tStartInterval
        if j==noVTeams-1: #We have created last VTeam - switch to OB
            teamType="OB"
            course=CourseOB
        j += 1

    print("Running %d simulations" % noOfRuns)
    for i in range(noOfRuns):
        env = simpy.Environment()
        env.process(start(env, Teams, Activities))
        env.run(until=tEnd)
        for t in Teams:
            t.persistStats()
        for a in Activities:
            a.persistStats()

    #Collect stats from activities
    print("Activities")
    for act in Activities:
        print("%s: Total wait=%s, avg. wait=%s, Max queue=%s, Start=%s, End=%s"  % (act.name, minMaxAvgSumPerRun(act.accWaits), minMaxAvgAvgPerRun(act.accWaits), minMaxAvg(act.accMaxQueue), minMaxAvgTime(act.accFirstTeamStart), minMaxAvgTime(act.accLastTeamEnd)))

    """
    for t in Teams:
        print("%s: Start=%s, End=%s, Total wait=%s, avg. wait/run=%s" % (t.name, formatTime(t.startTime), minMaxAvgTime(t.accEndTime), minMaxAvgSumPerRun(t.accWaits), minMaxAvgAvgPerRun(t.accWaits)))
    """
    
    title = printCourse(CourseV, "Væbnerrute",  noVTeams) + "\n" + printCourse(CourseOB, "OB-rute", noOBTeams)
    plotActivityStats(Activities, title)
    
#Run simulation
simulate(100,12,8)
