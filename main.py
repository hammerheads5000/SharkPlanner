from nicegui import ui
import ntclient
import asyncio

selection: list[str] = []
times: list[float] = []

@ui.refreshable
def autoList():
    global selection
    with ui.list().classes('w-full'):
        sumTime = 0
        for s, t in list(zip(selection, times)):
            sumTime += t
            with ui.item():
                with ui.item_section():
                    ui.item_label(s)
                with ui.item_section():
                    ui.item_label(f'{sumTime:.2f} s')

@ui.refreshable
def autoSelection():
    def updateAutoItems():
        ntclient.publishSelection(list(zip(selection, times)))
        ntclient.waitForUpdate()
        options = {(auto, time): f'{auto} ({time:.2f} s)' for auto,time in ntclient.getNextAutos()}
        selection_dropdown.set_options(options)
        selection_dropdown.set_value('')
        autoList.refresh()
        trajectoryVisualization.refresh()

    def addAutoItem(item: tuple[str, float] | None):
        if not item:
            return
        selection.append(item[0])
        times.append(item[1])
        updateAutoItems()
        
    def deleteAutoItem():
        if len(selection) == 0:
            return
        selection.pop()
        times.pop()
        updateAutoItems()

    with ui.card():
        ui.label('Auto').classes('text-bold')
        ui.separator()

        autoList()

        with ui.row():
            options = {}
            autos = ntclient.getNextAutos()
            if selection:
                options = {(auto, time): f'{auto} ({time:.2f} s)' for auto,time in autos}
            else:
                options = {(start, 0): start for start in ntclient.getStartOptions()}
            selection_dropdown = ui.select(options=options, label='Next point', with_input=True)
            ui.button(icon='add', on_click=lambda: addAutoItem(selection_dropdown.value)).props('round')
            ui.button(icon='delete', on_click=deleteAutoItem).props('round')

field_w = 16.51
field_h = 8.04

viewTime = 0
def setViewTime(time):
    global viewTime
    viewTime = time*sum(times)
    timeLabel.set_text(f'{viewTime:.1f} s')
    trajectoryVisualization.refresh()

def viewer():
    with ui.image(source='rebuilt field.png').classes('grow'):
        trajectoryVisualization()
    
@ui.refreshable
def trajectoryVisualization():
    def translateCoords(trajPoint: tuple[tuple[float, float], float]) -> str:
        return f'{int(trajPoint[0][0]/field_w*920 + 40)},{int(1000 - (trajPoint[0][1]/field_h*880 + 60))}'
    
    def getCoordString(traj: list[tuple[tuple[float, float], float]]):
        return ' '.join(map(translateCoords, traj))
    
    def getPointFromTime(traj: list[tuple[tuple[float, float], float]]):
        for pos, t in traj:
            if t >= viewTime:
                return f'cx="{int((pos[0]/field_w*920 + 40)*field_w/field_h)}" cy="{int(1000 - (pos[1]/field_h*880 + 60))}"'
        return 'cx="0" cy="0" r="0"'
    traj = ntclient.getTrajectory()
    ui.html(content=f'''
                <svg viewBox="0 0 1000 1000" preserveAspectRatio="none" style="width:100%;height:100%">
                    <polyline points="{getCoordString(traj)}"
                    style="fill:none;stroke:white;stroke-width:4;vector-effect: non-scaling-stroke"/>
                    <circle {getPointFromTime(traj)} r="18" fill="blue" transform="scale({field_h/field_w},1)"/>
                </svg>''').classes('w-full h-full bg-transparent')

def connectToSim():
    global selection, times
    ntclient.connectToSim()
    selectiontimes = ntclient.getSelection()
    if not selectiontimes:
        selection, times = [], []
    else:
        selection, times = [list(t) for t in zip(*ntclient.getSelection())]
    autoSelection.refresh()
    autoList.refresh()
    trajectoryVisualization.refresh()
    
def connectToDS():
    global selection, times
    ntclient.connectToDS()
    selectiontimes = ntclient.getSelection()
    if not selectiontimes:
        selection, times = [], []
    else:
        selection, times = [list(t) for t in zip(*ntclient.getSelection())]
    autoSelection.refresh()
    autoList.refresh()
    trajectoryVisualization.refresh()

with ui.row():
    ui.button('Connect to Sim', on_click=connectToSim)
    ui.button('Connect to DS', on_click=connectToDS)

with ui.row(wrap=False).classes('w-full'):
    autoSelection()
    with ui.card().classes('grow'):
        viewer()
        with ui.row(wrap=False).classes('w-full'):
            timeLabel = ui.label('0.0 s').classes('w-fit text-nowrap')
            timeSlide = ui.slider(min=0, max=1, value=0, step=0.01, on_change=lambda e: setViewTime(e.value)).classes('w-full')
ntclient.init()
ui.run(dark=True)