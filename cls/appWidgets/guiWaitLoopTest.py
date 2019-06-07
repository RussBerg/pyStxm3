"""
This script uses a while loop that lets an LED blink while the GUI is still responsive.
Running this script outputs
LED on shiny!
LED off shiny!
LED on shiny!
LED off shiny!
LED on shiny!
LED off shiny!
while the GUI is responsive.
This was created because of an stackoverflow question:
    http://stackoverflow.com/questions/23057031/how-to-quit-the-program-in-while-loop-using-push-button-in-pyqt/23057966#23057966
"""

from PyQt5 import QtGui
import sys

from cls.appWidgets.guiWaitLoop import guiLoop, gui_sleep # https://gist.github.com/niccokunzmann/8673951

@guiLoop
def led_blink(argument):
    while 1:
        print(("LED on " + argument))
        yield 0.5 # time to wait
        print(("LED off " + argument))
        yield 0.5
        
        
        
app = QtWidgets.QApplication(sys.argv)

w = QtWidgets.QWidget()
w.resize(250, 150)
w.move(300, 300)
w.setWindowTitle('Simple')
w.show()

led_blink(w, 'shiny!')
print('before gui_sleep')
gui_sleep(w, 5.0)
print('after gui_sleep')


sys.exit(app.exec_())
