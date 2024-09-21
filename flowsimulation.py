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

# 8:00, 9:00, 10:00
groupStartTimes = {"V": 8*60, "S": 9*60, "OB": 10*60}
# No. of teams to start simultaneously
tStartSimul = {"V":3, "S":4, "OB":4}
tStartInterval = 15        # Time between starting teams
tEnd = 30 * 60              # 06:00
tActivityBuffer = 5         # Extra buffer to add to activities
# Speeds in km/h (2021 measurements)
#meanSpeed = {"V": 3.3, "S":4, "OB": 4.3}
#stdevSpeed = {"V": 0.4, "S":0.4, "OB":0.5}

# Speeds in km/h (2022 measurements)
meanSpeed = {"V": 3.0, "S":3.5, "OB": 4.0} 
stdevSpeed = {"V": 0.5, "S":0.5, "OB":0.5}

r = random.Random(1)
teamTypes = ["V", "S", "OB"]

# Expected
# V: 20:30 - 03:10
# S: 23:15 - 03:35
# OB: 00:00 - 03:30
class Activity(object):

    def __init__(self, capacity, minDuration, maxDuration, name):
        self.capacity = capacity
        self.minDuration = minDuration
        self.maxDuration = maxDuration
        self.name = name
        self.accFirstTeamStart = {"V":[], "S": [], "OB": []} # Arrays for collecting timestamps of first team arrival for each run
        self.accLastTeamEnd = {"V":[], "S": [], "OB": []} # Arrays for collecting timestamps of last team departure for each run
        self.accWaits = [] # Array to store lists of waiting times for each run
        self.accMaxQueue = [] # Array to store max queue length for each run

    # Invoked for each run
    def setup(self, env):
        self.env = env
        self.slots = simpy.Resource(env, self.capacity)
        self.firstTeamStart = {"V":0, "S": 0, "OB": 0} # Variables to store first team arrival. Used in persistStats
        self.lastTeamEnd = {"V":0, "S": 0, "OB": 0} # Variables to store last team departure. Used in persistStats
        self.waits = [] # List of wait times
        self.maxQueue = 0 # High watermark for queue

    # Let team start activity
    def acceptTeam(self, team):
        tIn = self.env.now

        if self.firstTeamStart[team.teamType] == 0:
            self.firstTeamStart[team.teamType] = tIn

        if self.minDuration is None:
            yield self.env.timeout(0)
        else:
            yield self.env.timeout(r.uniform(self.minDuration,
                                             self.maxDuration))

        tOut = self.env.now
        self.lastTeamEnd[team.teamType] = tOut

    # Register waiting time for a team
    def addWaitTime(self, waitTime):
        self.waits.append(waitTime)

    # Update high watermark if necessary
    def updateMaxQueue(self):
        self.maxQueue = max(len(self.slots.queue), self.maxQueue)

    # Store statistics in aggregate arrays for later analysis
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
        self.accWaits = [] # Array of waiting time lists for each run
        self.accEndTime = []

    def setup(self, env): # Invoked for each run
        self.env = env
        self.speed = r.normalvariate(meanSpeed[self.teamType], stdevSpeed[self.teamType])
        self.waits = [] # List of waiting times
        self.endTime = 0

    # Go through course
    def start(self, env):
        for element in self.course: # Handle walking
            if isinstance(element, numbers.Number):
                walkingTime = (element / self.speed) * 60
                yield self.env.timeout(walkingTime)

            if type(element) is Activity: # Handle activities
                with element.slots.request() as request:
                    arrivalTime = env.now # Line up at activity
                    element.updateMaxQueue()
                    yield request # Wait for turn
                    waitTime = env.now - arrivalTime
                    self.waits.append(waitTime)
                    element.addWaitTime(waitTime)
                    yield env.process(element.acceptTeam(self)) # Do activity
                    self.env.timeout(tActivityBuffer) # Extra buffer for activity
        self.endTime = env.now

    # Store statistics in aggregate arrays for later analysis
    def persistStats(self):
        self.accWaits.append(self.waits)
        self.accEndTime.append(self.endTime)


def plotActivityStats(activities, title):
    dataWait = []  # List of activity wait lists
    # List of [start(5,10,25th percentile),end(75,90,95th percentile)] per activity
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

    # Plot max queue/activity as boxplot
    pyplot.boxplot(dataMaxQueue[::-1], labels=labels[::-1], vert=False)
    pyplot.title("Længste kø pr. post (%d gennemløb)" % noOfRuns)
    pyplot.grid(True)

    # Plot activity start/end times as Gantt chart
    fig = pyplot.figure()
    figgantt = fig.add_subplot(111)
    xmin = groupStartTimes["V"]
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
# Average of a list of numbers
def avg(list, decimals=2):
    if len(list) > 0:
        return round(sum(list) / len(list), decimals)
    return 0

# Returns array with [5th percentile, 95th percentile, average] from a list of numbers
def minMaxAvg(list):
    return [numpy.percentile(list,5), numpy.percentile(list,95), avg(list)]

# Returns result of minMaxAvg(list) as a single string
def minMaxAvgFormat(list):
    mma = minMaxAvg(list)
    return "(%d/%d/%.2f)" % (mma[0], mma[1], mma[2])

# Return result of minMaxAvg(list) as a single string with values formatted as time
def minMaxAvgTime(list):
    mma = minMaxAvg(list)
    return "(%s/%s/%s)" \
        % (formatTime(mma[0]), formatTime(mma[1]), formatTime(mma[2]))

# Aggregates the inner lists by sum and returns result of minMaxAvgTime() on the list of aggregates
def minMaxAvgSumPerRun(listOfLists):
    """Find min/max/avg of aggregated (summed) lists"""
    sumList = []
    for list in listOfLists:
        sumList.append(sum(list))
    return minMaxAvgTime(sumList)

# Aggregates the inner lists by average and returns result of minMaxAvgTime() on the list of aggregates
def minMaxAvgAvgPerRun(listOfLists):
    """Find min/max/avg of aggregated (averaged) lists"""
    avgList = []
    for list in listOfLists:
        avgList.append(avg(list))
    return minMaxAvgTime(avgList)

# Find the [0.05;0.95] interval for opening time of an activity
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

def startTeams(teamType, numberOfTeams, Teams, course):
    startGroup = tStartSimul[teamType]
    startTime = groupStartTimes[teamType]
    for j in range(numberOfTeams):
        Teams.append(Team("Hold %d (%s)" % (j,teamType), teamType, course[teamType], startTime))
        if j % startGroup == startGroup - 1:
            startTime += tStartInterval
        j += 1
    return Teams

# Create environment

def simulate(noOfRuns, noVTeams, noSTeams, noOBTeams):
    """
    Setup course - insert own course here!
    Activity: capacity, min, max, name
    """

    Post0 = Activity(8, 10, 13, "Startpost")
    Post0A = Activity(5, 10, 15, "Post 0A")
    Post0B = Activity(5, 10, 15, "Post 0B")
    Post1 = Activity(5, 10, 15, "Post 1")
    Post2 = Activity(7, 20, 25, "Post 2")
    Post3 = Activity(5, 10, 15, "Post 3")
    Post4 = Activity(10, 15, 20, "Post 4")
    Post5 = Activity(5, 15, 20, "Post 5")
    Post5A = Activity(5, 10, 15, "Post 5A")
    Post5B = Activity(5, 10, 15, "Post 5B")
    Post6 = Activity(7, 15, 20, "Post 6")
    Post7 = Activity(5, 10, 15, "Post 7") # Død
    Post8 = Activity(5, 10, 15, "Post 8")
    Post9 = Activity(4, 10, 15, "Post 9") # Klatring
    Post10 = Activity(99, 60, 70, "Mad") # Opgave på madposten. Tager ikke ekstra tid
    Post11 = Activity(5, 10, 15, "Post 11")
    Post12 = Activity(5, 10, 15, "Post 12")
    Post13 = Activity(5, 10, 15, "Post 13")
    Post14 = Activity(5, 10, 15, "Post 14")
    Post15 = Activity(5, 15, 20, "Post 15")
    Post16 = Activity(20, 10, 40, "DFO")
    PostMaal = Activity(99, None, None, "Mål")

    Activities = [Post0, Post0A, Post0B, Post1, Post2, Post3, Post4, Post5, Post5A, Post5B, Post6, Post7, Post8,
                Post9, Post10, Post11, Post12, Post13, Post14, Post15, Post16, PostMaal]

    """
    Link activities [act1, distance1, act2, distance2, ...]
    """
    course = {"V": [
                Post0, 1,
                Post1, 0.7,
                Post2, 0.9,
                Post3, 0.1,
                Post4, 0.5,
                Post5, 1.9,
                Post6, 2.2,
                Post7, 2.1,
                Post8, 1.4,
                Post9, 2.2,
                Post10,2.5,
                Post11,1.7,
                Post12,1.2,
                Post13,2.3,
                Post14,1.7,
                Post15,1.7,
                Post16,1.8,
                PostMaal],
          "S": [Post0, 1.3,
                Post0A,3,
                Post0B,0.6,
                Post1, 0.7,
                Post2, 0.9,
                Post3, 0.1,
                Post4, 0.5,
                Post5, 1.4,
                Post5A,2.3,
                Post5B,1.3,
                Post6, 2.2,
                Post7, 2.1,
                Post8, 1.4,
                Post9, 2.2,
                Post10,2.5,
                Post11,1.7,
                Post12,1.2,
                Post13,2.3,
                Post14,1.7,
                Post15,1.7,
                Post16,1.8,
                PostMaal],
          "OB": [
                Post0, 1.3,
                Post0A,3,
                Post0B,0.6,
                Post1, 0.7,
                Post2, 0.9,
                Post3, 0.1,
                Post4, 0.5,
                Post5, 1.4,
                Post5A,2.3,
                Post5B,1.3,
                Post6, 2.2,
                Post7, 2.1,
                Post8, 1.4,
                Post9, 2.2,
                Post10,2.5,
                Post11,1.7,
                Post12,1.2,
                Post13,2.3,
                Post14,1.7,
                Post15,1.7,
                Post16,1.8,
                PostMaal]}
    """ Setup course END """

    print(printCourse(course["V"], "Væbnerrute", noVTeams))
    print(printCourse(course["S"], "Seniorrute", noSTeams))
    print(printCourse(course["OB"], "OB-rute", noOBTeams))

    # Setup teams
    Teams = []

    ## New start logic. Start each group at a fixed time
    Teams = startTeams("V", noVTeams, Teams, course)
    Teams = startTeams("S", noSTeams, Teams, course)
    Teams = startTeams("OB", noOBTeams, Teams, course)

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
simulate(50, 27, 14, 20)