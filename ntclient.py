import ntcore as nt
from wpimath.geometry import Translation2d
import time

inst = nt.NetworkTableInstance.getDefault()

autoOptionsSub = inst.getStringArrayTopic('Autos/Auto Options').subscribe([])
autoOptionTimesSub = inst.getDoubleArrayTopic('Autos/Auto Option Times').subscribe([])
timestampSub = inst.getDoubleTopic('Autos/timestamp').subscribe(0)
startOptionsSub = inst.getStringArrayTopic('Autos/Start Options').subscribe([])
selectionEntry = inst.getStringTopic('Autos/Selection').getEntry('')
selectionTimesEntry = inst.getDoubleArrayTopic('Autos/Selection Timestamps').getEntry([])
trajectorySub = inst.getStructArrayTopic('Autos/Trajectory', Translation2d).subscribe([])
trajectoryTimesSub = inst.getDoubleArrayTopic('Autos/Trajectory Timestamps').subscribe([])

prevTimestamp = 0

def init():
    inst.startClient4('SharkPlanner')
    
def connectToSim():
    inst.setServer('127.0.0.1')
    time.sleep(0.2)
    
def connectToDS():
    inst.setServerTeam(5000)
    inst.startDSClient()
    time.sleep(0.2)

def publishSelection(selection: list[tuple[str, float]]):
    if len(selection) == 0:
        selectionEntry.set('')
        selectionTimesEntry.set([])
        return

    toPublish = selection[0][0]
    times = [selection[0][1]]
    prevPoint = selection[0][0]
    for s, t in selection[1:]:
        times.append(t)
        if s.startswith('Collect'):
            toPublish += ';'+s
        else:
            toPublish += f';{prevPoint} to {s}'
            prevPoint = s
            
    selectionEntry.set(toPublish)
    selectionTimesEntry.set(times) # type: ignore

def getStartOptions() -> list[str]:
    return startOptionsSub.get()

def getSelection() -> list[tuple[str, float]]:
    raw = selectionEntry.get()
    if raw == '':
        return []
    splits = raw.split(';')
    selection = []
    for s in splits:
        if s.startswith('Collect'):
            selection.append(s)
            continue
        parts = s.split(' to ')
        selection.append(parts[-1])
    times = selectionTimesEntry.get()
    return list(zip(selection, times))

def waitForUpdate():
    global prevTimestamp
    while timestampSub.get() == prevTimestamp and autoOptionsSub.get():
        time.sleep(0.1)
    prevTimestamp = timestampSub.get()
    time.sleep(0.5)

def getNextAutos() -> list[tuple[str, float]]:
    paths = autoOptionsSub.get()
    times = autoOptionTimesSub.get()

    options = []
    for path, time in list(zip(paths, times)):
        if path.startswith('Collect'):
            options.append((path, time))
        else:
            options.append((path.split(' to ')[1], time))
            
    return options

def getTrajectory() -> list[tuple[tuple[float, float], float]]:
    traj = [(pos.x,pos.y) for pos in trajectorySub.get()]
    times = trajectoryTimesSub.get()
    
    return list(zip(traj, times))