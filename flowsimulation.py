# -*- coding: utf-8 -*-
"""flowsimulation.py
Setup course model and simulate with a number of teams.
Output waiting times and completion times"""

import random
import simpy
import numpy
import matplotlib.pyplot as pyplot

tStart=7*60               #07:00
tEnd=30*60                #06:00 next day
minSpeed=1               #km/h
maxSpeed=2.5               #km/h
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
        self.accMaxQueue.append(self.maxQueue)

class Transport(object):
    def __init__(self, distance):
        self.distance = distance

class Team:
    def __init__(self, name, course, startTime):
        self.name = name
        self.course = course
        self.startTime = startTime
        self.accWaits = []
        self.accEndTime = []

    def setup(self, env):
        self.env = env
        self.waits = []
        self.endTime = 0
        
    def start(self, env):
        for element in self.course:
            if type(element) is Transport:
                walkingTime = r.uniform(element.distance/minSpeed, element.distance/maxSpeed)*60
                #print "Team %s walks %d km in %d minutes" % (self.name, element.distance, walkingTime) #TODO: Format time in hh:mm
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
    myFontdict={'fontsize': 8}
    
    dataWait = [] #List of activity wait lists
    dataStartEnd = [] #List of activity start(P0.05)/end(P0.95) time lists
    labels = []
    for a in activities:
        dataStartEnd.append([numpy.percentile(a.accFirstTeamStart,5), numpy.percentile(a.accLastTeamEnd,95)])
        sumWaits = []
        for list in a.accWaits:
            sumWaits.append(sum(list))                        
        dataWait.append(sumWaits)
        labels.append("%s\n Kap.=%d,\n[%s;%s]" % (a.name, a.capacity, a.minDuration, a.maxDuration))
#        print("%s: Start=%s, End=%s, Total wait=%s, avg. wait=%s, max queue=%s" % (a.name, minMaxAvgTime(a.accFirstTeamStart), minMaxAvgTime(a.accLastTeamEnd), minMaxAvgSumPerRun(a.accWaits), minMaxAvgAvgPerRun(a.accWaits), minMaxAvgFormat(a.accMaxQueue)))
    
    #"Plot" course
    pyplot.title(title, fontdict=myFontdict)
    
    #Plot total wait time/activity as boxplot
    #figwait = fig.add_subplot(211, label="Samlet ventetid pr. post")
    pyplot.boxplot(dataWait, labels=labels, vert=False)
    pyplot.title("Samlet ventetid pr. post")
    pyplot.show()

    #Plot activity start/end times as Gantt chart
    fig = pyplot.figure()
    figgantt = fig.add_subplot(111)
    y = 0
    xmin = tEnd
    xmax = tStart
    for i in dataStartEnd:
        figgantt.barh(y, i[1]-i[0], left=i[0])
        y = y+1
        xmin = min(i[0],xmin)
        xmax = max(i[1],xmax)
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

def minMaxAvgSumPerRun(listOfLists):
    sumList = []
    for list in listOfLists:
        sumList.append(sum(list))
    return minMaxAvgTime(sumList)

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
    P1 = Activity(2, 15, 35, "Startpost")
    T1 = Transport(2)
    P2 = Activity(3, 20, 35, "Sjov post")
    T2 = Transport(1.5)
    P3 = Activity(2, 15, 35, "Mørk post")
    T3 = Transport(2)
    T3a = Transport(1.5)
    P3a = Activity(1, 25, 40, "OB post")
    T3b = Transport(1.5)
    P4 = Activity(99, 60, 70, "Madpost")
    T4 = Transport(2)
    P5 = Activity(2, 35, 60, "Vandpost")
    T5 = Transport(2)
    PN = Activity(3, 25, 55, "Forbudt Område")
    TN = Transport(2)
    PX = Activity(99, None, None, "Mål")

    Activities = [P1, P2, P3, P3a, P4, P5, PN, PX]

    CourseV = [P1,T1,P2,T2,P3,T3,P4,T4,P5,T5,PN,TN,PX]
    CourseOB = [P1,T1,P2,T2,P3,T3a,P3a,T3b,P4,T4,P5,T5,PN,TN,PX]

    print(printCourse(CourseV, "Væbnerrute", noVTeams))
    print(printCourse(CourseOB, "OB-rute", noOBTeams))

    #Setup teams
    Teams = []
    for i in range(noVTeams):
        Teams.append(Team("Hold %d" % i, CourseV, tStart+i*10))
    for i in range(noOBTeams):
        Teams.append(Team("Hold %s" % i, CourseOB, tStart+80+i*10))


    print("Running %d simulations" % noOfRuns)
    for i in range(noOfRuns):
        env = simpy.Environment()
        env.process(start(env, Teams, Activities))
        env.run(until=tEnd)
        for t in Teams:
            t.persistStats()
        for a in Activities:
            a.persistStats()

        """
        #Collect stats from activities
        print "Activities"
        for act in Activities:
            print "%s: Total wait=%d minutes, avg. wait=%d minutes, Max queue=%d, Start=%s, End=%s"  % (act.name, sum(act.waits), avg(act.waits), act.maxQueue, formatTime(act.firstTeamStart), formatTime(act.lastTeamEnd))

        #Collect stats from teams
        print "Teams"
        for team in Teams:
            print "%s: Start=%s, End=%s, Total wait=%d minutes, avg. wait=%d" % (team.name, formatTime(team.startTime), formatTime(team.endTime), sum(team.waits), avg(team.waits))
        """

#    for t in Teams:
#        print("%s: Start=%s, End=%s, Total wait=%s, avg. wait/run=%s" % (t.name, formatTime(t.startTime), minMaxAvgTime(t.accEndTime), minMaxAvgSumPerRun(t.accWaits), minMaxAvgAvgPerRun(t.accWaits)))

    title = printCourse(CourseV, "Væbnerrute",  noVTeams) + "\n" + printCourse(CourseOB, "OB-rute", noOBTeams)
    plotActivityStats(Activities, title)
#Run simulation
simulate(10,12,8)
