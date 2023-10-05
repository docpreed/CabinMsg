import csv, subprocess
from nicegui import ui
from subprocess import Popen, PIPE, STDOUT
from datetime import datetime, timedelta


# seting defaults for sample config file creation
cfg_default_content='''\"
[Employees]
# Enter the names of your employees below in the format (first name) (last name):
Ernest Hemingway
Audrey Hepburn
Leonardo Da Vinci
Chuck Norris
Frank Sinatra

[Rooms]
# Enter the cabin names below in the format (sorting ID#) (cabin name)
00 kitchen 01
01 bathroom 02
02 bedroom 03
04 attic

[PageTitle]
# Here goes the page\'s title
CabinMessage System

[MessageRoomUnselected]
# What\'s to be displayed when no room is selected
Nothing selected!

[MessageRoomSelected]
# What\'s to be displayed in front of the selected room\'s name
Currently selected:

[BackButtonLabel]
# How the back from selection button shall be labeled
Back to overview

[NotificationMessage]
# here you can define what on screen message will be dispayed on notification, the placeholders (employee) and (room) have to be included!
(employee) has been notified to come to the (room).

[EmployeeMessage]
# here you can define what message the employee will receive, the placeholders (employee) and (room) have to be included!
Hello (employee),please come to the (room),thank you.

[ssh_user]
# change to your MacMini's user account name
user

[ssh_host]
# change to your MacMini's (static) IP address
192.168.1.0

#[Timetracking_SQL_connection]
# define the sql connection string for your time tracking database, uncomment the line below to use SQL
#DRIVER=FreeTDS;SERVER=[IPAddress]\[InstanceName];PORT=[Port];DATABASE=[DatabaseName];UID=[Username];PWD=[Password];TDS_Version=8.0;

#[Timetracking_SQL_query1]
# define what shall be selected from your Mitarbeiterstamm
#select (Name),(Vorname),(Personalnummer) FROM Master.Stamm_Personal;

#[Timetracking_SQL_query2]
# define what shall be selected from your Mitarbeiterstamm
#select TOP 1 * FROM Master.Buchungen WHERE Personalnummer=(Personalnummer) ORDER BY (Datum) desc, (Uhrzeit) desc;
\"'''

# retrieve the current directory on host's filesystem
sp = subprocess.Popen(["pwd"], stdout=subprocess.PIPE)
current_dir = str(sp.communicate())[3:-10]
del sp

# check if config file exists and if it doesn't, create sample config
cfg_file_name = "config.cfg"
command = ['ls', current_dir]
sp = subprocess.run(command, capture_output=True)
if cfg_file_name in str(sp.stdout):
    pass
else:
    print ("Configfile was not found, creating sample config file")
    sp = subprocess.Popen(["echo " + cfg_default_content + " > " + current_dir + '/' + cfg_file_name], shell=True)
    print ("Edit the file " + current_dir + "/" + cfg_file_name + " according to your needs and run again")
    #exit ()
del sp

PageTitle = None

# to add an individual instance for each user
@ui.page('/mainpage')
def mainpage():

  # init empty list arrays & dictionary
  ssh_host = None
  Employees = []
  tmp_Rooms = []
  Rooms = []
  emButtons = {}
  emButtonsNames = {}
  roButtons = {}
  roButtonsNames = {}
  heading = None
  selectionMsgSelected = None
  selectionMsgUnselected = None
  BackButtonLabel = None
  notification_message = None
  employee_message_template = None
  current_room_name = None
  ssh_user = None
  ssh_host = None
  use_timetracking = 0
  timetracking_sqlconn = None
  timetracking_sqlquery1 = None
  timetracking_sqlquery2 = None

  # read the config file
  with open('config.cfg', 'r') as ma:
    reader = csv.reader(ma)
    heading = None
    for row in reader:
      rowvar = str(row)[2:-2]
      # detect if current line contains a section heading
      if "[" in rowvar:
        heading = rowvar
      # skip empty lines or lines containing only a single character
      elif len(rowvar) < 2:
        pass
      # skip comments
      elif "#" in rowvar:
        pass
      # Add lines below given heading to the appropriate lists (arrays)
      else:
        if heading == '[Employees]':
          Employees.append(rowvar)
        elif heading == '[Rooms]':
          tmp_Rooms.append(rowvar)
        elif heading == '[PageTitle]':
          PageTitle = rowvar
          print (PageTitle)
        elif heading == '[MessageRoomSelected]':
          selectionMsgSelected = rowvar
        elif heading == '[MessageRoomUnselected]':
          selectionMsgUnselected = rowvar
        elif heading == '[BackButtonLabel]':
          BackButtonLabel = rowvar
        elif heading == '[NotificationMessage]':
          notification_message = rowvar
        elif heading == '[EmployeeMessage]':
          employee_message_template = rowvar
        elif heading == '[ssh_user]':
          ssh_user = rowvar
        elif heading == '[ssh_host]':
          ssh_host = rowvar
        elif heading == '[Timetracking_SQL_connection]':
          use_timetracking = 1
          timetracking_sqlconn = rowvar
        elif heading == '[Timetracking_SQL_query1]':
          timetracking_sqlquery1 = rowvar.replace("', '",",") #.replace('(','').replace(')','')
        elif heading == '[Timetracking_SQL_query2]':
          timetracking_sqlquery2 = rowvar.replace("', '",",")


  # sort arrays aplhabetically by item names
  Employees.sort()
  tmp_Rooms.sort()

  # strip leading index numbers from items in array
  n = 0
  while (n < len(tmp_Rooms)):
    Rooms.append(tmp_Rooms[n][3:])
    n += 1
  del n
  del tmp_Rooms

  # to store room selection
  class roSelection:
      def __init__(self):
          self.name = None
  ro_selection = roSelection()

  # SQL connection
  # if sql server connection is activated
  if use_timetracking > 0:
    import pyodbc #, pandas as pd
    conn = pyodbc.connect(timetracking_sqlconn)
    conn2 = pyodbc.connect(timetracking_sqlconn)
    cursor = conn.cursor()
    # How many concurrent operations are allowed by database server:
    print('Maximum no. of concurrent database connections: ' + str (conn.getinfo(pyodbc.SQL_MAX_CONCURRENT_ACTIVITIES)))
    subcursor = conn2.cursor()



  # What happens when you press an employee button
  def fnc_emButton(sndrinfo):
    nonlocal notification_message
    nonlocal current_room_name
    nonlocal employee_message_template
    # replace (employee) and (room) placeholders from config file with current values
    employee_message = employee_message_template.replace("(employee)",str(sndrinfo)).replace("(room)",str(current_room_name)).replace("'","")
    print ('Employee message: ' + employee_message )

    # actual commands to be executed on employee button click
    # ssh connection
    nonlocal ssh_user
    nonlocal ssh_host
    ssh_params = 'tell application \"Messages\" to send \"' + employee_message + '\" to buddy \"' + sndrinfo + '\"\';'
    ssh_command = 'osascript -e \'' + ssh_params

    stdout, stderr = Popen(['ssh', '{}@{}'.format(ssh_user, ssh_host), ssh_command], stderr=PIPE, stdout=PIPE).communicate()
    stdout = str(stdout)[2:-1]
    stderr = str(stderr)[2:-1]
    if stdout != "":
      print('ssh_command output:' + stdout)
    if str(stderr) != "":
      if 'buddy' in stderr:
        ui.notify('Error: No iMessage adressbook entry found on ' + ssh_host + ' for: \"' + sndrinfo + '\"')
      elif ('route to host' in stderr) or ('ssh' in stderr):
        ui.notify('Error: No ssh connection to ' + ssh_host + ' possible, have you set up passwordless authentification already?')
        ui.notify('Hint: ssh-keygen -t rsa && ssh-copy-id ' + ssh_user + '@' + ssh_host)
      else:
        ui.notify('Error: ' + stderr[0:-4])
      print('ssh_command error:' + stderr.replace('\r\n',''))
    else:
      ui.notify(
        # while displaying notification_message, also replace (employee) and (room) placeholders from config file with current values
        f'' + notification_message.replace('(employee)',str(sndrinfo)).replace('(room)',str(current_room_name)) + ''
      )
    sndrinfo = None
    employee_message = None
    current_room_name = None
    del stdout
    del stderr
    fnc_emButtonsInvisible()
    fnc_goBack()


  # UI layout
  with ui.card().classes('w-full').classes('items-center'):
    with ui.column().classes('w-3/4 items-center'):

      # page title
      with ui.card().classes('bg-[#cbd5e1]'):
        ui.label(PageTitle).style('color: #0000BB; font-size: 200%; font-weight: 300')

      # currently selected room
      ui.separator()
      with ui.card():
        lbl_kabinenueberschrift = ui.label(selectionMsgUnselected).style('color: #FF0000; font-size: 180%; font-weight: 300')

      # back-button
      btn_goBack = ui.button()

      # placeholder for keeping layout when btn_goBack is not visible
      lbl_placeholder = ui.label().classes('w-' + str(len(BackButtonLabel)) + ' bg-transparent h-12')

      # add buttons for every room from the [Rooms] section in the configfile
      with ui.row().classes('w-full justify-center').bind_visibility_from(btn_goBack,'value'):
        n = 0
        while n < len(Rooms):
          roButtons["button{0}".format(n)] = ui.button(Rooms[n], on_click=lambda e: fnc_raumselection(e.sender.text)).bind_text_to(ro_selection, 'name')
          roButtons["button" + str(n)].classes('w-24 h-24')
          roButtons["button" + str(n)].set_visibility(True)
          n += 1
        del n

      # add buttons for every employee from the [Employees] section in the config file
      with ui.row().classes('w-full justify-center').bind_visibility_from(btn_goBack,'value'):
        n = 0
        while n < len(Employees):
          emButtons["button{0}".format(n)] = ui.button(Employees[n], on_click=lambda e: fnc_emButton(e.sender.text))
          emButtons["button" + str(n)].classes('w-24 h-24')
          emButtons["button" + str(n)].set_visibility(False)
          n += 1
        del n

  # dictionaries to have a name <-> {id} pair of every button for referencing it by name
  for n in emButtons:
    emButtonsNames[emButtons[n].text] = n

  for n in roButtons:
    roButtonsNames[roButtons[n].text] = n

  # to hide all roButtons instances
  def fnc_roButtonsInvisible():
    n = 0
    while n < len(roButtons.items()):
      roButtons["button" + str(n)].set_visibility(False)
      n += 1
    del n

  # to unhide all roButton instances
  def fnc_roButtonsVisible():
    n = 0
    while n < len(roButtons.items()):
      roButtons["button" + str(n)].set_visibility(True)
      n += 1
    del n

  # to hide all emButtons instances
  def fnc_emButtonsInvisible():
    n = 0
    while n < len(emButtons.items()):
      emButtons["button" + str(n)].set_visibility(False)
      n += 1
    del n

  # to unhide all emButton instances
  def fnc_emButtonsVisible():
    n = 0
    while n < len(emButtons.items()):
      emButtons["button" + str(n)].set_visibility(True)
      n += 1
    del n

  # what happens when you select a room
  def fnc_raumselection(room_name):
    nonlocal current_room_name
    current_room_name = str(room_name) #.split('\n', 1)[0]
    btn_goBack.set_visibility(True)
    lbl_placeholder.set_visibility(False)
    fnc_emButtonsVisible()
    lbl_kabinenueberschrift.set_text(selectionMsgSelected + ' ' + f'\n' + str(room_name))
    lbl_kabinenueberschrift.style('color: #6E93D6; font-size: 200%; font-weight: 300')
    fnc_roButtonsInvisible()

  # what happens when you press the back button
  def fnc_goBack():
    btn_goBack.set_visibility(False)
    lbl_placeholder.set_visibility(True)
    fnc_emButtonsInvisible()
    lbl_kabinenueberschrift.set_text(selectionMsgUnselected)
    lbl_kabinenueberschrift.style('color: #FF0000; font-size: 200%; font-weight: 300')
    fnc_roButtonsVisible()


  # set sttributes of btn_goBack
  btn_goBack.set_text(BackButtonLabel)
  btn_goBack.set_visibility(False)
  btn_goBack.on('click', fnc_goBack)


  def fnc_employeestatus():
    if use_timetracking > 0:
#      timetracking_sqlquery1.replace('(',"\'' + str(row.").replace(')',") + '\''")
      for row in cursor.execute(timetracking_sqlquery1):
        if (row.Vorname + ' ' + row.Name) in Employees:
          nonlocal timetracking_sqlquery2
#          timetracking_sqlquery2 = timetracking_sqlquery2.replace('(',"row.").replace(')',"")
          timetracking_sqlquery3 = timetracking_sqlquery2.replace('(Personalnummer)',str(row.Personalnummer))
          for subrow in subcursor.execute(timetracking_sqlquery3):
            dt = datetime.strptime(str(subrow.Datum), '%Y%m%d')
            print (row.Vorname + ' ' + row.Name + ' ' + str(row.Personalnummer) + ' ' + str((dt + timedelta(minutes=subrow.Uhrzeit))) + ' ' + str(subrow.Buchungsart) )
            if subrow.Buchungsart == 'B1':
              emButtons[emButtonsNames[row.Vorname + ' ' + row.Name]].classes('bg-green')
            elif subrow.Buchungsart == 'B2':
              emButtons[emButtonsNames[row.Vorname + ' ' + row.Name]].classes('bg-grey')
            else:
              emButtons[emButtonsNames[row.Vorname + ' ' + row.Name]].classes('bg-lightgrey')
      print ('Employeestatus was updated')
    else:
      print ('Timetracking not being used, edit config.cfg to use.')

  ui.timer(60, fnc_employeestatus)




# GUI startup
ui.run (port = 8000, title=PageTitle, dark=None) # favicon=''
