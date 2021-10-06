# -*- coding: utf-8 -*-
"""flowsimulation.py
Setup course model and simulate with a number of teams.
Output waiting times and completion times"""

import random
import numbers
import simpy
import numpy
import matplotlib.pyplot as pyplot
import matplotlib.patches as mpatches

tStart = 8 * 60              # 08:00
tStartS = 9 * 60              # 09:00
# No. of teams to start simultaneously
tStartSimul = {"V":3, "S":4, "OB":4}
tStartInterval = 15        # Time between starting teams
tEnd = 30 * 60              # 01:00
# Speeds in km/h
meanSpeed = {"V": 2.3, "S":2.8, "OB": 3.0} 
stdevSpeed = {"V": 0.35, "S":0.25, "OB":0.3}
r = random.Random(3823)
teamTypes = ["V", "S", "OB"]


class Activity(object):

    def __init__(self, capacity, minDuration, maxDuration, name):
        self.capacity = capacity
        self.minDuration = minDuration
        self.maxDuration = maxDuration
        self.name = name
        self.accFirstTeamStart = {"V":[], "S": [], "OB": []}
        self.accLastTeamEnd = {"V":[], "S": [], "OB": []}
        self.accWaits = []
        self.accMaxQueue = []

    def setup(self, env):
        self.env = env
        self.slots = simpy.Resource(env, self.capacity)
        self.firstTeamStart = {"V":0, "S": 0, "OB": 0}
        self.lastTeamEnd = {"V":0, "S": 0, "OB": 0}
        self.waits = []
        self.maxQueue = 0

    def acceptTeam(self, team):
        tIn = self.env.now

        # print "%s begins %s at %s" % (team.name, self.name, formatTime(tIn))
        if self.firstTeamStart[team.teamType] == 0:
            self.firstTeamStart[team.teamType] = tIn

        if self.minDuration is None:
            yield self.env.timeout(0)
        else:
            # TODO: use random.normalvariate and express min/max duration as
            # mean/std.dev
            yield self.env.timeout(r.uniform(self.minDuration,
                                             self.maxDuration))

        tOut = self.env.now
        # print "%s completed %s at %s" % (team.name, self.name,
        # formatTime(tOut))
        self.lastTeamEnd[team.teamType] = tOut

    def addWaitTime(self, waitTime):
        self.waits.append(waitTime)

    def updateMaxQueue(self):
        self.maxQueue = max(len(self.slots.queue), self.maxQueue)

    def persistStats(self):
        for teamType in teamTypes:
            self.accFirstTeamStart[teamType].append(self.firstTeamStart[teamType])
            self.accLastTeamEnd[teamType].append(self.lastTeamEnd[teamType])
        self.accWaits.append(self.waits)
        self.accMaxQueue.append(self.maxQueue)


class Team:

    def __init__(self, name, teamType, course, startTime):
        self.name = name
        self.teamType = teamType
        self.course = course
        self.startTime = startTime
        self.accWaits = []
        self.accEndTime = []

    def setup(self, env): # Invoked for each run
        self.env = env
        self.speed = r.normalvariate(meanSpeed[self.teamType], stdevSpeed[self.teamType])
        self.waits = []
        self.endTime = 0

    def start(self, env):
        for element in self.course:
            if isinstance(element, numbers.Number):
                # TODO: Better model for speed, perhaps as function of time of
                # day?
                walkingTime = (element / self.speed) * 60
                #print("%s walks %.1f km in %s" % (self.name, element, formatTime(walkingTime)))
                yield self.env.timeout(walkingTime)

            if type(element) is Activity:
                with element.slots.request() as request:
                    arrivalTime = env.now
                    element.updateMaxQueue()
                    # print "%s arrives at %s at %s" % (self.name,
                    # element.name, formatTime(arrivalTime))
                    yield request
                    waitTime = env.now - arrivalTime
                    self.waits.append(waitTime)
                    element.addWaitTime(waitTime)
                    yield env.process(element.acceptTeam(self))
        self.endTime = env.now
        # print "%s: Start=%s, Finish=%s, Total wait=%d minutes" % (self.name,
        # formatTime(self.startTime), formatTime(self.endTime),
        # self.totalWaitTime)

    def persistStats(self):
        self.accWaits.append(self.waits)
        self.accEndTime.append(self.endTime)


def plotActivityStats(activities, title):
    # TODO: Plot as subplots on same figure
    # myFontdict = {'fontsize': 8}

    dataWait = []  # List of activity wait lists
    # List of [start(5,10,25th percentile),end(75,90,95th percentile)] per
    # activity
    dataStartEnd = {"V": [], "S": [], "OB": []}
    dataMaxQueue = []
    labels = []
    noOfRuns = len(activities[0].accWaits)
    for a in activities:
        for teamType in teamTypes:
            percStart = numpy.percentile(a.accFirstTeamStart[teamType], [5, 10, 25, 50])
            percEnd = numpy.percentile(a.accLastTeamEnd[teamType], [95, 90, 75, 50])
            dataStartEnd[teamType].append([percStart, percEnd])
        dataMaxQueue.append(a.accMaxQueue)
        actWaits = []
        teamsArrived = []
        for list in a.accWaits:
            actWaits.extend(list)
            teamsArrived.append(len(list))
        dataWait.append(actWaits)
        labels.append("%s (%.2f hold),\nKapacitet=%d, [%s;%s]" %
                    (a.name, avg(teamsArrived), a.capacity, a.minDuration,
                    a.maxDuration))
        """print("%s: Start=%s, End=%s, Total wait=%s, avg. wait=%s,
                max queue=%s" %
                (a.name, minMaxAvgTime(a.accFirstTeamStart),
                minMaxAvgTime(a.accLastTeamEnd),
                minMaxAvgSumPerRun(a.accWaits),
                minMaxAvgAvgPerRun(a.accWaits),
                minMaxAvgFormat(a.accMaxQueue)))"""

    # "Plot" course
    # pyplot.title(title, fontdict=myFontdict)

    # Plot total wait time/activity as boxplot
    # figwait = fig.add_subplot(211, label="Samlet ventetid pr. post")
    # TODO: This is apparently showing unaggregated data
    """
    pyplot.boxplot(dataWait[::-1], labels=labels[::-1], vert=False)
    pyplot.title("Ventetid pr. post (%d gennemløb)" % noOfRuns)
    pyplot.show()
    """
    
    # Plot max queue/activity as boxplot
    pyplot.boxplot(dataMaxQueue[::-1], labels=labels[::-1], vert=False)
    pyplot.title("Længste kø pr. post (%d gennemløb)" % noOfRuns)
    pyplot.grid(True)
    #pyplot.show()

    # Plot activity start/end times as Gantt chart
    fig = pyplot.figure()
    figgantt = fig.add_subplot(111)
    xmin = tStart
    xmax = tEnd
    for teamType in teamTypes:
        y = len(dataStartEnd["V"]) - 0.5
        colorString = 'blue'
        if teamType=="S":
            colorString = 'orange'
        elif teamType == "OB":
            colorString = 'gray'
        for startList, endList in dataStartEnd[teamType]:
            # 5th/95th percentile
            figgantt.barh(y, endList[0] - startList[0], left=startList[0],
                        alpha=0.3, color=colorString)
            # 10th/90th percentile
            figgantt.barh(y, endList[1] - startList[1], left=startList[1],
                        alpha=0.3, color=colorString)
            # 25th/75th percentile
            figgantt.barh(y, endList[2] - startList[2], left=startList[2],
                        alpha=0.3, color=colorString)
            # 50th percentile
            figgantt.barh(y, endList[3] - startList[3], left=startList[3],
                        alpha=0.3, edgecolor='red', color=colorString, zorder=100)
            y -= 1
            xmax = max(endList[0], xmax)

    patch5_95 = mpatches.Patch(alpha=0.3, label='95%')
    patch10_90 = mpatches.Patch(alpha=0.45, label='90%')
    patch25_75 = mpatches.Patch(alpha=0.6, label='75%')
    patch50 = mpatches.Patch(alpha=0.75, edgecolor='red', label='50%')
    pyplot.legend(handles=[patch5_95, patch10_90, patch25_75, patch50], loc=1)

    labelsy = pyplot.yticks(numpy.arange(0.5, len(activities) + 0.5), labels[::-1])
    pyplot.setp(labelsy)
    figgantt.set_xlim(xmin, xmax)
    figgantt.xaxis.set_major_locator(pyplot.MultipleLocator(60))
    figgantt.xaxis.set_major_formatter(
        pyplot.FuncFormatter(lambda x, pos: formatTime(x)))
    figgantt.set_title("Åbne- og lukketider pr. post")
    figgantt.grid(True)
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
        if isinstance(element, numbers.Number):
            outputStr += "-(%.1f)->" % element
            totalDistance += element
        if type(element) is Activity:
            outputStr += "%s[%d]" % (element.name, element.capacity)
    outputStr += "\nTotal distance: %.1f" % totalDistance
    return outputStr

# Helper methods for performing calculations on 1- and 2-dimensional arrays


def avg(list, decimals=2):
    if len(list) > 0:
        return round(sum(list) / len(list), decimals)
    return 0


def minMaxAvg(list):
    return [min(list), max(list), avg(list)]


def minMaxAvgFormat(list):
    mma = minMaxAvg(list)
    return "(%d/%d/%.2f)" % (mma[0], mma[1], mma[2])


def minMaxAvgTime(list):
    mma = minMaxAvg(list)
    return "(%s/%s/%s)" \
        % (formatTime(mma[0]), formatTime(mma[1]), formatTime(mma[2]))


def minMaxAvgSumPerRun(listOfLists):
    """Find min/max/avg of aggregated (summed) lists"""
    sumList = []
    for list in listOfLists:
        sumList.append(sum(list))
    return minMaxAvgTime(sumList)


def minMaxAvgAvgPerRun(listOfLists):
    """Find min/max/avg of aggregated (averaged) lists"""
    avgList = []
    for list in listOfLists:
        avgList.append(avg(list))
    return minMaxAvgTime(avgList)

def startCloseTime(act: Activity):
    allStartTimes = act.accFirstTeamStart["V"] + act.accFirstTeamStart["S"] + act.accFirstTeamStart["OB"]
    allStartTimes = [i for i in allStartTimes if i] # Remove None values
    p5StartTime = numpy.percentile(allStartTimes or [0], 5)
    allCloseTimes = act.accLastTeamEnd["V"] + act.accLastTeamEnd["S"] + act.accLastTeamEnd["OB"]
    allCloseTimes = [i for i in allCloseTimes if i] # Remove None values
    p95CloseTime = numpy.percentile(allCloseTimes or [0], 95)
    return [formatTime(p5StartTime), formatTime(p95CloseTime)]

def start(env, teams, activities):
    for a in activities:
        a.setup(env)
    for t in teams:
        t.setup(env)
        waitTime = max(0, t.startTime - env.now)
        yield env.timeout(waitTime)
        env.process(t.start(env))

# Create environment


def simulate(noOfRuns, noVTeams, noSTeams, noOBTeams):
    """
    Setup course - insert own course here!
    Activity: capacity, min, max, name
    """

    Post0 = Activity(8, 10, 13, "Startpost")
    Post0A = Activity(5, 10, 15, "Post 0A")
    Post0B = Activity(5, 10, 15, "Post 0B")
    Post0C = Activity(5, 10, 15, "Post 0C")
    Post1 = Activity(5, 10, 15, "Post 1")
    Post2 = Activity(5, 10, 15, "Post 2")
    Post3 = Activity(5, 10, 15, "Post 3")
    Post4 = Activity(5, 10, 15, "Post 4")
    Post5 = Activity(5, 10, 15, "Post 5")
    Post5A = Activity(5, 10, 15, "Post 5A")
    Post5B = Activity(99, 5, 10, "Post 5B") # Død post - rundt om grusgraven
    Post6 = Activity(5, 10, 15, "Post 6")
    PostM = Activity(99, 60, 70, "Mad") # Opgave på madposten. Tager ikke ekstra tid
    Post7 = Activity(99, 0, 0, "Post 7")
    Post8 = Activity(5, 10, 15, "Post 8")
    Post9 = Activity(5, 10, 15, "Post 9")
    Post10 = Activity(5, 10, 15, "Post 10")
    Post11 = Activity(5, 10, 15, "Post 11")
    Post12 = Activity(5, 10, 15, "Post 12")
    Post13 = Activity(5, 10, 15, "Post 13")
    Post14 = Activity(5, 10, 15, "DFO")
    PostMaal = Activity(99, None, None, "Mål")

    Activities = [Post0, Post0A, Post0B, Post0C, Post1, Post2, Post3, Post4, Post5, Post5A,
                Post5B, Post6, PostM, Post7, Post8, Post9, Post10, Post11, Post12, Post13, Post14, PostMaal]

    """
    Link activities [act1, distance1, act2, distance2, ...]
    """
    course = {"V": [Post0, 1.5,
                Post1, 1.2,
                Post2, 1.1,
                Post3, 1.2,
                Post4, 1.0,
                Post5, 2.4,
                Post6, 2.0,
                PostM, 0,
                Post7, 2.0,
                Post8, 2.1,
                Post9, 1.5,
                Post10, 1.4,
                Post11, 1.9,
                Post12, 1.3,
                Post13, 1.6,
                Post14, 1.4,
                PostMaal],
          "S": [Post0, 1.0,
                Post0A, 1.2,
                Post0B, 2.5,
                Post1, 1.2,
                Post2, 1.1,
                Post3, 1.2,
                Post4, 1.0,
                Post5, 2.5,
                Post5A, 2.5, # 6 km på kortet
                Post5B, 0,
                Post6, 2.0,
                PostM, 0,
                Post7, 2.0,
                Post8, 2.1,
                Post9, 1.5,
                Post10, 1.4,
                Post11, 1.9,
                Post12, 1.3,
                Post13, 1.6,
                Post14, 1.4,
                PostMaal],
          "OB": [Post0, 1.0,
                Post0A, 1.2,
                Post0B, 2.5,
                Post1, 1.2,
                Post2, 1.1,
                Post3, 1.2,
                Post4, 1.0,
                Post5, 2.5,
                Post5A, 2.5, # 6 km på kortet
                Post5B, 0,
                Post6, 2.0,
                PostM, 0,
                Post7, 2.0,
                Post8, 2.1,
                Post9, 1.5,
                Post10, 1.4,
                Post11, 1.9,
                Post12, 1.3,
                Post13, 1.6,
                Post14, 1.4,
                PostMaal]}
    """ Setup course END """

    print(printCourse(course["V"], "Væbnerrute", noVTeams))
    print(printCourse(course["S"], "Seniorrute", noSTeams))
    print(printCourse(course["OB"], "OB-rute", noOBTeams))

    # Setup teams
    Teams = []
    startTime = tStart

    teamType = "V"
    startGroup = tStartSimul[teamType]
    for j in range(noVTeams + noSTeams + noOBTeams):
        Teams.append(Team("Hold %d (%s)" % (j,teamType), teamType, course[teamType], startTime))
        if j % startGroup == startGroup - 1:
            startTime += tStartInterval
        if j == noVTeams - 1:  # We have created last VTeam - switch to S
            j = 0
            teamType = "S"
            startTime = tStartS
        if j == noVTeams + noSTeams - 1:  # We have created last STeam - switch to OB
            teamType = "OB"
        startGroup = tStartSimul[teamType]
        j += 1

    Teams.sort(key=lambda x: x.startTime)
    print("Running %d simulations" % noOfRuns)
    for i in range(noOfRuns):
        env = simpy.Environment()
        env.process(start(env, Teams, Activities))
        env.run(until=tEnd)
        for t in Teams:
            t.persistStats()
        for a in Activities:
            a.persistStats()

    
    print("Activities: Start/Close")
    for act in Activities:
        # print("%s: Total wait=%s, avg. wait=%s, Max queue=%s, StartV=%s, EndV=%s, StartS=%s, EndS=%s, StartOB=%s, EndOB=%s, Start/Close=%s"
        #       % (act.name, minMaxAvgSumPerRun(act.accWaits),
        #          minMaxAvgAvgPerRun(act.accWaits), minMaxAvg(act.accMaxQueue),
        #          minMaxAvgTime(act.accFirstTeamStart["V"]),
        #          minMaxAvgTime(act.accLastTeamEnd["V"]),
        #          minMaxAvgTime(act.accFirstTeamStart["S"]),
        #          minMaxAvgTime(act.accLastTeamEnd["S"]),
        #          minMaxAvgTime(act.accFirstTeamStart["OB"]),
        #          minMaxAvgTime(act.accLastTeamEnd["OB"]),
        #          startCloseTime(act)))
        startCloseTimes = startCloseTime(act)
        print("%9s: %s, %s"
              % (act.name,
                 startCloseTimes[0],
                 startCloseTimes[1]))
    
    for t in Teams:
        print("%s: Start=%s, End=%s, Total wait=%s, avg. wait/run=%s"
              % (t.name, formatTime(t.startTime), minMaxAvgTime(t.accEndTime),
              minMaxAvgSumPerRun(t.accWaits), minMaxAvgAvgPerRun(t.accWaits)))
    
    title = printCourse(course["V"], "Væbnerrute",  noVTeams) + "\n"
    title += printCourse(course["S"], "Seniorrute",  noSTeams) + "\n"
    title += printCourse(course["OB"], "OB-rute", noOBTeams)
    plotActivityStats(Activities, title)

# Run simulation (#Runs, #VTeams, #STeams, #OBTeams)
simulate(50, 25, 10, 25)
