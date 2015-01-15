# -*- coding: utf-8 -*-
"""flowsimulation.py
Setup course model and simulate with a number of teams.
Output waiting times and completion times"""

import random
import simpy

tStart=7*60               #07:00
tEnd=30*60                #06:00 next day
minSpeed=1.5               #km/h
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
                    element.updateMaxQueue
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

def formatTime(timestamp):
    hour = timestamp / 60
    min = timestamp % 60
    return "%02d:%02d" % (hour, min)

def printCourse(course):
    outputStr = ''
    totalDistance = 0
    for element in course:
        if type(element) is Transport:
            outputStr += "-(%d)->" % element.distance
            totalDistance += element.distance
        if type(element) is Activity:
            outputStr += "%s[%d]" % (element.name, element.capacity)
    print outputStr
    print "Total distance: %d" % totalDistance

def avg(list):
    if len(list) > 0:
        return round(sum(list)/len(list),2)
    return 0

def minMaxAvg(list):
    return "(%s/%s/%s)" % (min(list), max(list), avg(list)) 

def minMaxAvgTime(list):
    return "(%s/%s/%s)" % (formatTime(min(list)), formatTime(max(list)), formatTime(avg(list)))

def minMaxAvgSumPerRun(listOfLists):
    sumList = []
    for list in listOfLists:
        sumList.append(sum(list))
    return "(%s/%s/%s)" % (min(sumList), max(sumList), avg(sumList)) 

def minMaxAvgAvgPerRun(listOfLists):
    avgList = []
    for list in listOfLists:
        avgList.append(avg(list))
    return "(%s/%s/%s)" % (min(avgList), max(avgList), avg(avgList)) 

def start(env, teams, activities):
    for a in activities:
        a.setup(env)
    for t in teams:
        t.setup(env)
        waitTime = max(0, t.startTime-env.now)
        yield env.timeout(waitTime)
        env.process(t.start(env))


#Create environment - TODO: parameterise number of teams
def simulate(noOfRuns):
    """
    Setup course
    Activity: capacity, min, max, name 
    Transport: distance
    """
    P1 = Activity(2, 15, 35, "Startpost")
    T1 = Transport(2)
    P2 = Activity(2, 50, 55, "Sjov post")
    T2 = Transport(1.5)
    P3 = Activity(1, 15, 35, "Mørk post")
    T3 = Transport(2)
    T3a = Transport(1.5)
    P3a = Activity(1, 25, 40, "OB post")
    T3b = Transport(1.5)
    PN = Activity(3, 25, 55, "Forbudt Område")
    TN = Transport(2)
    PX = Activity(99, None, None, "Mål")

    Activities = [P1, P2, P3, P3a, PN, PX]

    CourseV = [P1,T1,P2,T2,P3,T3,PN,TN,PX]
    CourseOB = [P1,T1,P2,T2,P3,T3a,P3a,T3b,PN,TN,PX]
    print "Væbnerrute:"
    printCourse(CourseV)
    print "OB-rute:"
    printCourse(CourseOB)

    #Setup teams
    Teams = []
    for i in range(4):
        Teams.append(Team("Hold %d" % i, CourseV, tStart+i*10))

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

    for t in Teams:
        print "%s: Start=%s, End=%s, Total wait=%s, avg. wait/run=%s" % (t.name, formatTime(t.startTime), minMaxAvgTime(t.accEndTime), minMaxAvgSumPerRun(t.accWaits), minMaxAvgAvgPerRun(t.accWaits))

    for a in Activities:
        print "%s: Start=%s, End=%s, Total wait=%s, avg. wait=%s, max queue=%s" % (a.name, minMaxAvgTime(a.accFirstTeamStart), minMaxAvgTime(a.accLastTeamEnd), minMaxAvgSumPerRun(a.accWaits), minMaxAvgAvgPerRun(a.accWaits), minMaxAvg(a.accMaxQueue))
#Run simulation - TODO: collect stats and run simulation multiple times
simulate(3)
