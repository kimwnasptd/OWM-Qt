'''
This module will be used for showint messages to the statusbar of the GUI
'''

global bar


# The StatusBar in QtApplication
def initBar(qtbar):
    global bar
    bar = qtbar


def show(msg):
    global bar
    bar.showMessage(msg)
