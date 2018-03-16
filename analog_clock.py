#!/usr/bin/env python3
# coding: UTF-8
# license: GPL
#
## @package _08c_clock
#
#  A very simple analog clock.
#
#  The program transforms worldcoordinates into screencoordinates
#  and vice versa according to an algorithm found in:
#  "Programming principles in computer graphics" by Leendert Ammeraal.
#
#  Based on the code of Anton Vredegoor (anton.vredegoor@gmail.com)
#
#  @author Paulo Roma
#  @since 01/05/2014
#  @see https://code.activestate.com/recipes/578875-analog-clock
#  @see http://orion.lcg.ufrj.br/python/figuras/fluminense.png
import sys
import os
from math import sin, cos, pi
from threading import Thread
import random

MIN_ACC = 15  # minute accuracy

if sys.version_info.major == 3:
    from tkinter import *  # python 3
    from tkinter import messagebox
else:
    try:
        import tkMessageBox as messagebox
        from mtTkinter import *  # for thread safe
    except ImportError:
        from Tkinter import *  # python 2

hasPIL = True
# we need PIL for resizing the background image
# in Fedora do: yum install python-pillow-tk
# or yum install python3-pillow-tk
try:
    from PIL import Image, ImageTk
except ImportError:
    hasPIL = False


## Class for handling the mapping from window coordinates
#  to viewport coordinates.
#
class mapper:
    ## Constructor.
    #
    #  @param world window rectangle.
    #  @param viewport screen rectangle.
    #
    def __init__(self, world, viewport):
        self.world = world
        self.viewport = viewport
        x_min, y_min, x_max, y_max = self.world
        X_min, Y_min, X_max, Y_max = self.viewport
        f_x = float(X_max - X_min) / float(x_max - x_min)
        f_y = float(Y_max - Y_min) / float(y_max - y_min)
        self.f = min(f_x, f_y)
        x_c = 0.5 * (x_min + x_max)
        y_c = 0.5 * (y_min + y_max)
        X_c = 0.5 * (X_min + X_max)
        Y_c = 0.5 * (Y_min + Y_max)
        self.c_1 = X_c - self.f * x_c
        self.c_2 = Y_c - self.f * y_c

    ## Maps a single point from world coordinates to viewport (screen) coordinates.
    #
    #  @param x, y given point.
    #  @return a new point in screen coordinates.
    #
    def __windowToViewport(self, x, y):
        X = self.f * x + self.c_1
        Y = self.f * -y + self.c_2  # Y axis is upside down
        return X, Y

    ## Maps two points from world coordinates to viewport (screen) coordinates.
    #
    #  @param x1, y1 first point.
    #  @param x2, y2 second point.
    #  @return two new points in screen coordinates.
    #
    def windowToViewport(self, x1, y1, x2, y2):
        return self.__windowToViewport(x1, y1), self.__windowToViewport(x2, y2)


## Class for creating a new thread.
#
class makeThread(Thread):
    """Creates a thread."""

    ## Constructor.
    #  @param func function to run on this thread.
    #
    def __init__(self, func):
        Thread.__init__(self)
        self.__action = func
        self.debug = False

    ## Destructor.
    #
    def __del__(self):
        if (self.debug): print ("Thread end")

    ## Starts this thread.
    #
    def run(self):
        if (self.debug): print ("Thread begin")
        self.__action()


## Class for drawing a simple analog clock.
#  The backgroung image may be changed by pressing key 'i'.
#  The image path is hardcoded. It should be available in directory 'images'.
#
class ClockTest:
    ## Constructor.
    #
    #  @param deltahours time zone.
    #  @param sImage whether to use a background image.
    #  @param w canvas width.
    #  @param h canvas height.
    #  @param useThread whether to use a separate thread for running the clock.
    #
    def __init__(self, root, w=400, h=400, useThread=False, **kwargs):
        self.world = [-1, -1, 1, 1]
        self.imgPath = './images/fluminense.png'  # image path
        if hasPIL and os.path.exists(self.imgPath):
            self.showImage = True
        else:
            self.showImage = False

        self.hour = 0
        self.minute = 0
        self.second = 0
        self.visualize = kwargs.get("visualize", False)
        self.setColors()
        self.circlesize = 0.09
        self._ALL = 'handles'
        self.root = root
        width, height = w, h
        self.pad = width / 16

        if self.showImage:
            self.fluImg = Image.open(self.imgPath)

        self.root.bind("<Escape>", lambda _: root.destroy())
        self.canvas = Canvas(root, width=width, height=height, background=self.bgcolor)
        viewport = (self.pad, self.pad, width - self.pad, height - self.pad)
        self.T = mapper(self.world, viewport)
        self.root.title('Clock Test')
        self.canvas.bind("<Configure>", self.resize)
        self.root.bind("<KeyPress-i>", self.toggleImage)
        self.canvas.pack(fill=BOTH, expand=YES)

        if kwargs.get("demo"):
            # demo is animation with no end in sight
            self.animate(delay=50)

        else:
            if useThread:
                st = makeThread(self.poll)
                st.debug = True
                st.start()
            else:
                self.poll()

    ## Called when the window changes, by means of a user input.
    #
    def resize(self, event):
        sc = self.canvas
        sc.delete(ALL)  # erase the whole canvas
        width = sc.winfo_width()
        height = sc.winfo_height()

        imgSize = min(width, height)
        self.pad = imgSize / 16
        viewport = (self.pad, self.pad, width - self.pad, height - self.pad)
        self.T = mapper(self.world, viewport)

        if self.showImage:
            flu = self.fluImg.resize((int(0.8 * 0.8 * imgSize), int(0.8 * imgSize)), Image.ANTIALIAS)
            self.flu = ImageTk.PhotoImage(flu)
            sc.create_image(width / 2, height / 2, image=self.flu)
        else:
            self.canvas.create_rectangle([[0, 0], [width, height]], fill=self.bgcolor)

        self.redraw()  # redraw the clock

    ## Sets the clock colors.
    #
    def setColors(self):
        if self.showImage:
            self.bgcolor = 'antique white'
            self.timecolor = 'dark orange'
            self.circlecolor = 'dark green'
        else:
            self.bgcolor = '#000000'
            self.timecolor = '#ffffff'
            self.circlecolor = '#808080'

    ## Toggles the displaying of a background image.
    #
    def toggleImage(self, event):
        if hasPIL and os.path.exists(self.imgPath):
            self.showImage = not self.showImage
            self.setColors()
            self.resize(event)

    ## Redraws the whole clock.
    #
    def redraw(self, **kwargs):
        start = pi / 2  # 12h is at pi/2
        step = pi / 6
        for i in range(12):  # draw the minute ticks as circles
            angle = start - i * step
            x, y = cos(angle), sin(angle)
            self.paintcircle(x, y)
        self.painthms(**kwargs)  # draw the handles
        if not self.showImage:
            self.paintcircle(0, 0)  # draw a circle at the centre of the clock

    ## Draws the handles.
    #
    def painthms(self, **kwargs):
        hour = kwargs.get("hour", self.hour)
        minute = kwargs.get("minute", self.minute)
        second = kwargs.get("second", self.second)
        self.canvas.delete(self._ALL)  # delete the handles
        # self.root.title('%02i:%02i:%02i' % (h, m, s))
        if kwargs.get('easy'):
            hour_offset = 0
            second_offset = 0
        else:
            hour_offset = minute
            second_offset = second
        angle = pi / 2 - pi / 6 * (hour + hour_offset / 60.0)
        x, y = cos(angle) * 0.70, sin(angle) * 0.70
        scl = self.canvas.create_line
        # draw the hour handle
        scl(self.T.windowToViewport(0, 0, x, y), fill=self.timecolor, tag=self._ALL, width=self.pad / 3)
        angle = pi / 2 - pi / 30 * (minute + second_offset / 60.0)
        x, y = cos(angle) * 0.90, sin(angle) * 0.90
        # draw the minute handle
        scl(self.T.windowToViewport(0, 0, x, y), fill=self.timecolor, tag=self._ALL, width=self.pad / 5)
        # angle = pi / 2 - pi / 30 * second
        # x, y = cos(angle) * 0.95, sin(angle) * 0.95
        # # draw the second handle
        # scl(self.T.windowToViewport(0, 0, x, y), fill=self.timecolor, tag=self._ALL, arrow='last')

    ## Draws a circle at a given point.
    #
    #  @param x,y given point.
    #
    def paintcircle(self, x, y):
        ss = self.circlesize / 2.0
        sco = self.canvas.create_oval
        sco(self.T.windowToViewport(-ss + x, -ss + y, ss + x, ss + y), fill=self.circlecolor)

    @staticmethod
    def _get_arg_kwarg(target, default, args, kwargs):
        return_value = default
        # search args for target
        for element in args:
            if type(element) is dict and target in element:
                    return_value = element.get(target)
                    break
        # dictionary takes priority
        return_value = kwargs.get(target, return_value)
        return return_value

    def animate(self, *args, **kwargs):
        delay = self._get_arg_kwarg("delay", 100, args, kwargs)
        stop_hour_minute = self._get_arg_kwarg("stop_hour_minute", None, args, kwargs)
        if stop_hour_minute is not None:
            if stop_hour_minute == (self.hour, self.minute):
                self.redraw()
                return
        self.minute += 1
        if self.minute == 60:
            self.minute = 0
            self.hour += 1
            self.hour %= 12
        self.redraw()
        self.root.after(delay, self.animate, dict(delay=delay, stop_hour_minute=stop_hour_minute))
        return

    def poll(self):
        correct = 0
        wrong = 0

        while True:
            self.hour = random.randint(0, 11)
            self.minute = random.randint(0, int(60/MIN_ACC)-1) * MIN_ACC
            hour_minute_answer = (int(self.hour), int(self.minute))
            if self.visualize:
                self.minute = 0
                self.animate(delay=1, stop_hour_minute=hour_minute_answer)
            else:
                self.redraw()
            q = QuestionWindow(self.root,
                               title="Question #{}".format(correct+wrong+1),
                               time_answer=hour_minute_answer)
            if not q.still_going:
                break
            if q.correct_answer:
                correct += 1
            else:
                wrong += 1
        messagebox.showinfo("Score", "You got {} of {} correct!".format(correct, correct + wrong))
        self.root.destroy()


class Dialog(Toplevel):
    def __init__(self, parent, title=None, window_x=None, window_y=None):

        Toplevel.__init__(self, parent)
        self.transient(parent)

        if title:
            self.title(title)

        self.parent = parent

        self.result = None

        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+{}+{}".format(window_x-8 if window_x is not None else (parent.winfo_rootx() + 500),
                                      window_y-31 if window_y is not None else (parent.winfo_rooty() + 50)))

        self.initial_focus.focus_set()

        self.wait_window(self)

    #
    # construction hooks

    def body(self, master):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden

        pass

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons

        box = Frame(self)

        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Exit", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    #
    # standard button semantics

    def ok(self, event=None):

        if not self.validate():
            self.initial_focus.focus_set()  # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        self.apply()

        self.cancel()

    def cancel(self, event=None):
        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

    #
    # command hooks

    def validate(self):

        return 1  # override

    def apply(self):

        pass  # override


class QuestionWindow(Dialog):
    e1 = None
    still_going = True
    user_answer = None
    correct_answer = False

    def __init__(self, parent, **kwargs):
        self.window_x = kwargs.get('window_x')
        self.window_y = kwargs.get('window_y')
        self.time_answer = kwargs.get('time_answer')
        if self.time_answer is None:
            exit(1)
        if sys.version_info.major == 3:
            super(QuestionWindow, self).__init__(parent, title=kwargs.get('title'),
                                                 window_x=self.window_x,
                                                 window_y=self.window_y)
        else:
            Dialog.__init__(self, parent, title=kwargs.get('title'),
                            window_x=self.window_x,
                            window_y=self.window_y)

    def body(self, master):
        row = 0
        Label(master, text="What time is it?").grid(row=row, sticky='w')

        self.e1 = Entry(master, width=5, justify=RIGHT)

        self.e1.grid(row=row, column=1, sticky='w')
        self.e1.focus_set()

    def apply(self):
        if self.correct_answer:
            messagebox.showinfo(
                "Correct",
                "Correct!"
            )
            self.user_answer = None
        else:
            ca = list(self.time_answer)  # list to be mutable
            if ca[0] == 0:
                ca[0] = 12
            messagebox.showerror(
                "Sorry",
                "Sorry, the correct answer was {ca[0]}:{ca[1]:02}".format(ca=ca)
            )

    def validate(self):
        """
        Validates that the entry is only a blank or an integer
        :return: Boolean
        """
        try:
            regex = r'(^[012]?\d)\D?([0-5]\d)$'
            match = re.search(regex, self.e1.get())
            h, m = (int(x) for x in match.group(1, 2))
            # 2400 is valid, but that's it
            if (h == 24 and m > 0) or h > 24:
                return False
            self.correct_answer = (h % 12, m) == self.time_answer
            return True
        except AttributeError:
            pass  # RE failed
        return False

    def ok(self, event=None):
        if not self.validate():
            messagebox.showwarning(
                "Bad input",
                "No time was found in your answer.\nPlease use the format hh:mm."
            )
            self.e1.select_range(0, len(self.e1.get()))
            self.e1.focus_set()  # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        self.apply()
        self.parent.focus_set()
        self.destroy()

    def cancel(self, event=None):
        # put focus back to the parent window
        self.still_going = False
        self.parent.focus_set()
        self.destroy()


def main():
    width = height = 400
    use_thread = False

    root = Tk()
    root.geometry('+0+0')
    ClockTest(root, width, height, use_thread, demo=False, visualize=True)

    root.mainloop()


if __name__ == '__main__':
    sys.exit(main())
