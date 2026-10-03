# -*- coding: utf-8 -*-
"""flowsimulation.py
Setup course model and simulate with a number of teams.
Output waiting times and completion times"""

import random
import numbers
import argparse
import runpy
from pathlib import Path
import simpy
import numpy
import matplotlib.pyplot as pyplot
import matplotlib.patches as mpatches

# 8:00, 10:00, 11:00
groupStartTimes = {"V": 8*60, "S": 10*60, "OB": 11*60}
# No. of teams to start simultaneously
tStartSimul = {"V":3, "S":4, "OB":4}
tStartInterval = 15        # Time between starting teams
tEnd = 30 * 60             # 06:00
# Speeds in km/h (2021 measurements)
#meanSpeed = {"V": 3.3, "S":4, "OB": 4.3}
#stdevSpeed = {"V": 0.4, "S":0.4, "OB":0.5}

# Speeds in km/h (2022 measurements)
meanSpeed = {"V": 3.0, "S":3.5, "OB": 4.0} 
stdevSpeed = {"V": 0.5, "S":0.5, "OB":0.5}

r = random.Random(1)
teamTypes = ["V", "S", "OB"]

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
            duration = 0
        else:
            duration = r.uniform(self.minDuration, self.maxDuration)
        yield self.env.timeout(duration)

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
        self.endTime = None

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
    noOfRuns = len(next(iter(activities.values())).accWaits)
    for a in activities:
        act = activities[a]
        for teamType in teamTypes:
            startTimes = [time for time in act.accFirstTeamStart[teamType] if time]
            endTimes = [time for time in act.accLastTeamEnd[teamType] if time]
            if startTimes and endTimes:
                percStart = numpy.percentile(startTimes, [5, 10, 25, 50])
                percEnd = numpy.percentile(endTimes, [95, 90, 75, 50])
                dataStartEnd[teamType].append([percStart, percEnd])
            else:
                dataStartEnd[teamType].append(None)
        dataMaxQueue.append(act.accMaxQueue)
        actWaits = []
        teamsArrived = []
        for list in act.accWaits:
            actWaits.extend(list)
            teamsArrived.append(len(list))
        dataWait.append(actWaits)
        labels.append("%s (%.2f hold),\nKapacitet:%d, [%s;%s]" %
                    (act.name, avg(teamsArrived), act.capacity, act.minDuration,
                    act.maxDuration))

    # Plot max queue/activity as boxplot
    pyplot.boxplot(dataMaxQueue[::-1], tick_labels=labels[::-1],
                   orientation="horizontal")
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
        for percentiles in dataStartEnd[teamType]:
            if percentiles is None:
                startList, endList = [0, 0, 0, 0], [0, 0, 0, 0]
            else:
                startList, endList = percentiles
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

    pyplot.yticks(numpy.arange(0.5, len(activities) + 0.5), labels[::-1])
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
def startCloseTime(act= Activity):
    allStartTimes = act.accFirstTeamStart["V"] + act.accFirstTeamStart["S"] + act.accFirstTeamStart["OB"]
    allStartTimes = [i for i in allStartTimes if i] # Remove None values
    allCloseTimes = act.accLastTeamEnd["V"] + act.accLastTeamEnd["S"] + act.accLastTeamEnd["OB"]
    allCloseTimes = [i for i in allCloseTimes if i] # Remove None values
    if not allStartTimes or not allCloseTimes:
        return ["N/A", "N/A"]
    p5StartTime = numpy.percentile(allStartTimes, 5)
    p95CloseTime = numpy.percentile(allCloseTimes, 95)
    return [formatTime(p5StartTime), formatTime(p95CloseTime)]

def start(env, teams, activities):
    for a in activities:
        activities[a].setup(env)
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

def loadCourse(routeFile):
    routePath = Path(routeFile)
    if not routePath.is_absolute():
        routePath = Path(__file__).resolve().parent / routePath

    route = runpy.run_path(str(routePath), init_globals={"Activity": Activity})
    course = route["course"]

    if "Act" in route:
        activities = route["Act"]
    elif "Activities" in route:
        activities = {str(index): activity
                      for index, activity in enumerate(route["Activities"])}
    else:
        uniqueActivities = {}
        for routeElements in course.values():
            for element in routeElements:
                if isinstance(element, Activity):
                    uniqueActivities.setdefault(str(len(uniqueActivities)), element)
        activities = uniqueActivities

    return course, activities

# Create environment

def simulate(noOfRuns, noVTeams, noSTeams, noOBTeams, routeFile="rute2025.py"):
    course, Act = loadCourse(routeFile)

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
        env.process(start(env, Teams, Act))
        env.run(until=tEnd)
        for t in Teams:
            t.persistStats()
        for act in Act:
            Act[act].persistStats()

    
    print("Activities: Start/Close")
    for a in Act:
        act = Act[a]
        # print("%s: Total wait:%s, avg. wait:%s, Max queue:%s, StartV:%s, EndV:%s, StartS:%s, EndS:%s, StartOB:%s, EndOB:%s, Start/Close:%s"
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
          completedTimes = [endTime for endTime in t.accEndTime if endTime is not None]
          completionSummary = minMaxAvgTime(completedTimes) if completedTimes else "N/A"
          incompleteRuns = len(t.accEndTime) - len(completedTimes)
          print("%s: Start:%s, End:%s (%d/%d incomplete), Total wait:%s, avg. wait/run:%s"
              % (t.name, formatTime(t.startTime), completionSummary,
              incompleteRuns, noOfRuns,
              minMaxAvgSumPerRun(t.accWaits), minMaxAvgAvgPerRun(t.accWaits)))
    
    title = printCourse(course["V"], "Væbnerrute",  noVTeams) + "\n"
    title += printCourse(course["S"], "Seniorrute",  noSTeams) + "\n"
    title += printCourse(course["OB"], "OB-rute", noOBTeams)
    plotActivityStats(Act, title)

def main():
    parser = argparse.ArgumentParser(description="Simulate scout race routes")
    parser.add_argument("--route", default="rute2026.py",
                        help="route definition file (default: rute2026.py)")
    parser.add_argument("--vteams", type=int, default=30,
                        help="number of V teams (default: 30)")
    parser.add_argument("--steams", type=int, default=10,
                        help="number of S teams (default: 10)")
    parser.add_argument("--obteams", type=int, default=20,
                        help="number of OB teams (default: 20)")
    args = parser.parse_args()
    simulate(50, args.vteams, args.steams, args.obteams, args.route)


if __name__ == "__main__":
    main()