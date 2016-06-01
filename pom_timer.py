#!/usr/bin/env python3
# encoding: utf-8

"""
Count down seconds from a given minute value
using the Tkinter GUI toolkit that comes with Python.

Basic Tk version by vegaseat (I extended this):
https://www.daniweb.com/programming/software-development/threads/464062/countdown-clock-with-python

The sound file is borrowed from here:
https://github.com/Luxtylo/pomodoro.py

Author: Laszlo Szathmary, alias Jabba Laci, 2016, jabba.laci@gmail.com
"""

import os
import re
import shlex
import sys
import time
from collections import OrderedDict
from subprocess import PIPE, STDOUT, Popen

# Manjaro: sudo pacman -S tk
# Ubuntu:  sudo apt-get install python3-tk
import tkinter as tk

go_on = None    # will be set later

VERSION = '0.1'
MINUTES = 25    # 25 minutes is the default
WINDOW_TITLE = 'pom timer'
DEBUG = False
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SOUND_FILE = '{d}/timer_done.mp3'.format(d=PROJECT_DIR)
SOUND_VOLUME = '0.04'

required_commands = [
    '/usr/bin/wmctrl',      # in package wmctrl
    '/usr/bin/xdotool',     # in package xdotool
    '/usr/bin/play',        # in package sox
]


def check_required_commands():
    """
    Verify if the external binaries are available.
    """
    for cmd in required_commands:
        if not os.path.isfile(cmd):
            print("Error: the command '{0}' is not available! Abort.".format(cmd))
            sys.exit(1)

check_required_commands()


###################################
## window and process management ##
###################################

def get_simple_cmd_output(cmd, stderr=STDOUT):
    """
    Execute a simple external command and get its output.

    The command contains no pipes. Error messages are
    redirected to the standard output by default.
    """
    args = shlex.split(cmd)
    return Popen(args, stdout=PIPE, stderr=stderr).communicate()[0].decode("utf8")


def get_wmctrl_output():
    """
    Parses the output of wmctrl and returns a list of ordered dicts.
    """
    cmd = "wmctrl -lGpx"
    lines = [line for line in get_simple_cmd_output(cmd)
             .encode('ascii', 'ignore')
             .decode('ascii').split("\n") if line]

    res = []
    for line in lines:
        pieces = line.split()
        d = OrderedDict()
        d['wid'] = pieces[0]
        d['desktop'] = int(pieces[1])
        d['pid'] = int(pieces[2])
        d['geometry'] = [int(x) for x in pieces[3:7]]
        d['window_class'] = pieces[7]
        d['client_machine_name'] = pieces[8]
        d['window_title'] = ' '.join(pieces[9:])
        res.append(d)
    #
    return res


def get_wid_by_title(title_regexp):
    """
    Having the window title (as a regexp), return its wid.

    If not found, return None.
    """
    for d in get_wmctrl_output():
        m = re.search(title_regexp, d['window_title'])
        if m:
            return d['wid']
    #
    return None


def activate_window_by_id(wid):
    """
    Put the focus on and activate the the window with the given ID.
    """
    os.system('xdotool windowactivate {wid}'.format(wid=wid))


def switch_to_window(title_regexp):
    """
    Put the focus on the window with the specified title.
    """
    wid = get_wid_by_title(title_regexp)
    if wid:
        if DEBUG:
            print('# window id:', wid)
        wid = int(wid, 16)
        if DEBUG:
            print('# switching to the other window')
        activate_window_by_id(wid)
    else:
        if DEBUG:
            print('# not found')


#########
## GUI ##
#########

def formatter(sec):
    # format as 2 digit integers, fills with zero to the left
    # divmod() gives minutes, seconds
    return "{:02d}:{:02d}".format(*divmod(sec, 60))


def play_sound():
    os.system("play -q -v {vol} {fname} &".format(
        vol=SOUND_VOLUME, fname=SOUND_FILE
    ))


def count_down():
    global go_on
    go_on = True
    for t in range(MINUTES * 60 - 1, -1, -1):
        if t == 0:
            play_sound()
            switch_to_window(WINDOW_TITLE)
        time_str.set(formatter(t))
        root.update()
        # delay one second
        for _ in range(2):
            time.sleep(0.5)    # if minimized then maximized,
            root.update()      # it's more responsive this way
        if not go_on:
            return
    reset()


def reset():
    global go_on
    go_on = False
    time_str.set(formatter(MINUTES * 60))
    root.update()


def center(win):
    """
    centers a tkinter window
    :param win: the root or Toplevel window to center

    from http://stackoverflow.com/a/10018670/232485
    """
    win.update_idletasks()
    width = win.winfo_width()
    frm_width = win.winfo_rootx() - win.winfo_x()
    win_width = width + 2 * frm_width
    height = win.winfo_height()
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = height + titlebar_height + frm_width
    x = win.winfo_screenwidth() // 2 - win_width // 2
    y = win.winfo_screenheight() // 2 - win_height // 2
    win.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    win.deiconify()


def print_usage():
    print("""
Jabba's Pomodoro Timer v{ver}

Usage: {fname} [parameter]

Parameters:
-h, --help        this help
-play             play the sound and quit (for testing the volume)
<minutes>         If not specified, then the default value is 25.
""".strip().format(ver=VERSION, fname=sys.argv[0]))

if len(sys.argv) > 1:
    param = sys.argv[1]
    if param in ['-h', '--help']:
        print_usage()
        sys.exit(0)
    elif param == '-play':
        # for testing the volume
        play_sound()
        sys.exit(0)
    elif re.search(r'\d+', param):
        try:
            MINUTES = int(param)
        except ValueError:
            print("Error: unknown option.")
            sys.exit(1)
    else:
        print("Error: unknown option.")
        sys.exit(1)


root = tk.Tk()
root.wm_title(WINDOW_TITLE)
root.resizable(width=False, height=False)
root.geometry('{}x{}'.format(200, 150))
time_str = tk.StringVar()
# create the time display label, give it a large font
# label auto-adjusts to the font
label_font = ('helvetica', 40)
tk.Label(root, textvariable=time_str, font=label_font, bg='white',
         fg='blue', relief='raised', bd=3).pack(fill='x', padx=5, pady=5)
time_str.set(formatter(MINUTES * 60))
root.update()
# create buttons
# pack() positions the buttons below the label
tk.Button(root, text='Start', command=count_down).pack()
tk.Button(root, text='Reset', command=reset).pack()
# start the GUI event loop
root.wm_attributes("-topmost", 1)    # always on top
center(root)
root.mainloop()
