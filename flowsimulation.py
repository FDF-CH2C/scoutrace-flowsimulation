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

tStart = 8 * 60             # 08:00
tStartSimul = 3             # No. of teams to start simultaneously
tStartInterval = 15         # Time between starting teams
tEnd = 32 * 60              # 08:00 next day
minSpeed = 2              # km/h
minSpeedOB = 2            # km/h
maxSpeed = 4.5              # km/h
maxSpeedOB = 5              # km/h
r = random.Random(3823)


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
        tIn = self.env.now

        # print "%s begins %s at %s" % (team.name, self.name, formatTime(tIn))
        if self.firstTeamStart == 0:
            self.firstTeamStart = tIn

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


class Team:

    def __init__(self, name, teamType, course, startTime):
        self.name = name
        self.teamType = teamType  # TODO: Do we need to save this?
        self.course = course
        self.startTime = startTime
        if teamType == "V":
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
        baseSpeed = r.uniform(self.minSpeed, self.maxSpeed)
        for element in self.course:
            if isinstance(element, numbers.Number):
                # TODO: Better model for speed, perhaps as function of time of
                # day?
                walkingTime = (element / baseSpeed) * 60
                # print("Team %s walks %d km in %s" % (self.name,
                # element, formatTime(walkingTime)))
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
    dataStartEnd = []
    dataMaxQueue = []
    labels = []
    noOfRuns = len(activities[0].accWaits)
    for a in activities:
        percStart = numpy.percentile(a.accFirstTeamStart, [5, 10, 25, 50])
        percEnd = numpy.percentile(a.accLastTeamEnd, [75, 90, 95, 50])
        dataStartEnd.append([percStart, percEnd])
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
    pyplot.show()

    # Plot activity start/end times as Gantt chart
    fig = pyplot.figure()
    figgantt = fig.add_subplot(111)
    y = len(dataStartEnd) - 1
    xmin = tEnd
    xmax = tStart
    for startList, endList in dataStartEnd:
        # 5th/95th percentile
        figgantt.barh(y, endList[0] - startList[0], left=startList[0],
                      alpha=0.3)
        # 10th/90th percentile
        figgantt.barh(y, endList[1] - startList[1], left=startList[1],
                      alpha=0.3)
        # 25th/75th percentile
        figgantt.barh(y, endList[2] - startList[2], left=startList[2],
                      alpha=0.3)
        # 50th percentile
        figgantt.barh(y, endList[3] - startList[3], left=startList[3],
                      alpha=0.3, edgecolor='red')
        y = y - 1
        xmin = min(startList[0], xmin)
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
    Setup course
    Activity: capacity, min, max, name
    """

    Post0 = Activity(3, 10, 13, "Startpost")
    Post1 = Activity(6, 20, 30, "Jolle")    
    Post2 = Activity(4, 10, 15, "Strand")
    Post3 = Activity(4, 10, 15, "Karts")
    Post3a = Activity(3, 10, 15, "Planter")
    Post4 = Activity(4, 10, 15, "Natur")
    Post5 = Activity(99, 60, 70, "Mad")
    Post6 = Activity(6, 15, 25, "Tons")
    Post6a = Activity(99, 10, 15, "Post6a -Død")
    Post6b = Activity(99, 10, 15, "Post6b - Død")
    Post7 = Activity(8, 10, 25, "Græshopper")
    Post7a = Activity(4, 10, 20, "Klatring")
    Post8 = Activity(4, 10, 15, "Olsenbanden")
    Post9 = Activity(4, 10, 15, "FHJ")
    Post9a = Activity(4, 10, 15, "Stød")
    Post10 = Activity(6, 10, 15, "Lys")
    Post11 = Activity(4, 10, 15, "Dukketeater")
    Post12 = Activity(4, 15, 20, "Post12?")
    Post13 = Activity(8, 10, 25, "Forbudt")
    Post14 = Activity(99, None, None, "Mål")


    Activities = [Post0, Post1, Post2, Post3, Post3a, Post4, Post5, Post6, Post6a, Post6b, Post7, Post7a,
                  Post8, Post9, Post9a, Post10, Post11, Post12, Post13, Post14]

    """
    Link activities [act1, distance1, act2, distance2, ...]
    """
    CourseV = [Post0, 2.7,
               Post1, 3,
               Post2, 2.7,
               Post3, 1.5,
               Post4, 3.2,
               Post5, 1,
               Post6, 1.7,
               Post7, 0.8,
               Post8, 2.1,
               Post9, 1.9,
               Post10, 1,
               Post11, 0.8,
               Post12, 1.6,
               Post13, 1.2,
               Post14]
    CourseS = [Post0, 2.7,
               Post1, 3,
               Post2, 2.7,
               Post3, 2.2,
               Post3a, 1.1,
               Post4, 3.2,
               Post5, 1,
               Post6, 1.7,
               Post7, 0.2,
               Post7a, 0.9,
               Post8, 2.1,
               Post9, 1.9,
               Post10, 1,
               Post11, 0.8,
               Post12, 1.6,
               Post13, 1.2,
               Post14]
    CourseOB = [Post0, 2.7,
               Post1, 3,
               Post2, 2.7,
               Post3, 2.2,
               Post3a, 1.1,
               Post4, 3.2,
               Post5, 1,
               Post6, 1.1,
               Post6a, 1.2,
               Post6b, 1.8,
               Post7, 0.2,
               Post7a, 0.9,
               Post8, 2.1,
               Post9, 1.9,
               Post9a, 2.2,
               Post10, 1,
               Post11, 0.8,
               Post12, 1.6,
               Post13, 1.2,
               Post14]

    print(printCourse(CourseV, "Væbnerrute", noVTeams))
    print(printCourse(CourseS, "Seniorrute", noSTeams))
    print(printCourse(CourseOB, "OB-rute", noOBTeams))

    # Setup teams - start 3 teams every 15 minutes
    Teams = []
    startTime = tStart

    teamType = "V"
    course = CourseV
    for j in range(noVTeams + noSTeams + noOBTeams):
        Teams.append(Team("Hold %d" % j, teamType, course, startTime))
        if j % tStartSimul == tStartSimul - 1:
            startTime += tStartInterval
        if j == noVTeams - 1:  # We have created last VTeam - switch to S
            teamType = "S"
            course = CourseS
        if j == noVTeams + noSTeams - 1:  # We have created last STeam - switch to OB
            teamType = "OB"
            course = CourseOB
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

    
    print("Activities")
    for act in Activities:
        print("%s: Total wait=%s, avg. wait=%s, Max queue=%s, Start=%s, End=%s"
              % (act.name, minMaxAvgSumPerRun(act.accWaits),
                 minMaxAvgAvgPerRun(act.accWaits), minMaxAvg(act.accMaxQueue),
                 minMaxAvgTime(act.accFirstTeamStart),
                 minMaxAvgTime(act.accLastTeamEnd)))
    
    
    for t in Teams:
        print("%s: Start=%s, End=%s, Total wait=%s, avg. wait/run=%s"
              % (t.name, formatTime(t.startTime), minMaxAvgTime(t.accEndTime),
              minMaxAvgSumPerRun(t.accWaits), minMaxAvgAvgPerRun(t.accWaits)))
    
    title = printCourse(CourseV, "Væbnerrute",  noVTeams) + "\n"
    title = printCourse(CourseS, "Seniorrute",  noSTeams) + "\n"
    title += printCourse(CourseOB, "OB-rute", noOBTeams)
    plotActivityStats(Activities, title)

# Run simulation (#Runs, #VTeams, #STeams, #OBTeams)
simulate(10, 20, 10, 20)
