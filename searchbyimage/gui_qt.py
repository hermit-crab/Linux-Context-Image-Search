import glob
import os
import signal
import sys
import tempfile
import time
import traceback
import webbrowser
from threading import Thread

import psutil


try:
    from PyQt5 import QtCore, QtGui, QtWidgets
    from PyQt5.QtCore import Qt
except ImportError:
    from PyQt4 import QtCore, QtGui
    from PyQt4.QtCore import Qt
    QtWidgets = QtGui


from . import event_binder


def run(filename, search_provider):
    GUI(filename, search_provider)


class GUI(QtCore.QObject):

    # TODO: heavy refactoring

    update_progress = QtCore.pyqtSignal(float)

    global_mousemove = QtCore.pyqtSignal()
    global_keyrelease = QtCore.pyqtSignal(str)

    error = QtCore.pyqtSignal(tuple)
    done = QtCore.pyqtSignal()

    width = 7
    window_size = 50
    color = QtGui.QColor(139, 164, 195)
    cancel_color = QtGui.QColor(218, 84, 90)
    shadow_color = QtGui.QColor(0, 0, 0, 15)

    label_max_letters = 30
    label_style = '''
                    background-color: rgba(255, 255, 255, 160);
                    font-size: 10px;
                    color: black;
                    padding: 1px 4px;
                    border-radius: 3px;
                    '''

    def __init__(self, filename, search_provider):
        super().__init__()

        self.progress = 0
        self.aborted = False

        self.filename = os.path.split(filename)[1]

        pid = os.getpid()

        self.pidfile = os.path.join(tempfile.gettempdir(), 'pid.imgops.%s' % pid)
        open(self.pidfile, 'a').close()

        self.all_instances = self.find_instances()

        self.animate_timer = QtCore.QTimer()

        self.app = QtWidgets.QApplication(sys.argv)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        self.x_offset, self.y_offset = self.decide_window_offset()

        self.window = QtWidgets.QWidget()
        self.window.setGeometry(0, 0, self.window_size, self.window_size)
        self.to_mouse()
        self.window.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.window.setAttribute(Qt.WA_TranslucentBackground)
        self.window.setAttribute(Qt.WA_ShowWithoutActivating)

        # Label

        text = self.filename
        if len(text) > self.label_max_letters:
            part = int(self.label_max_letters/2) - 1
            text = text[:part] + ' .. ' + text[-part:]
        label = QtWidgets.QLabel(text, self.window)
        label.setStyleSheet(self.label_style)
        label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        delta = label.sizeHint().width() - self.window_size
        if delta > 0:
            self.x_offset -= delta/2
            self.to_mouse()
        else:
            delta = 0

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.window.setLayout(layout)
        layout.addWidget(label)

        # Animation

        self.pen = QtGui.QPen()
        self.canvas = QtWidgets.QWidget(self.window)
        self.canvas.setGeometry(delta/2, 0, self.window_size, self.window_size)
        self.canvas.paintEvent = self.paintEvent
        label.raise_()

        def update(frac):
            self.progress = frac if frac < 1 else 1
            self.window.update()

        def animate_progress(new_frac):
            self.animate(update, .4, self.progress, new_frac)

        self.update_progress.connect(animate_progress)

        def thread_emit_progress(frac):
            self.update_progress.emit(frac)

        # Controls

        self.global_mousemove.connect(self.to_mouse)
        self.global_keyrelease.connect(self.on_keyrelease)

        def listen():
            event_binder.listen(lambda *_: self.global_mousemove.emit(),
                                lambda key: self.global_keyrelease.emit(key))

        Thread(target=listen).start()

        self.error.connect(self.on_error)
        self.done.connect(self.app.quit)
        self.app.aboutToQuit.connect(self.on_quit)

        # Search

        provider = search_provider(thread_emit_progress)

        def search():
            try:
                url = provider.search(filename)
                webbrowser.open(url)
            except Exception:
                self.error.emit(sys.exc_info())
            else:
                while True:
                    if self.aborted or self.progress >= 1:
                        self.done.emit()
                        break
                    time.sleep(.3)

        Thread(target=search, daemon=True).start()

        # Main

        self.window.show()
        sys.exit(self.app.exec_())

    def decide_window_offset(self):
        x = 10
        y = 20

        print(self.all_instances)
        if len(self.all_instances) > 1:
            y += (self.window_size + 5) * (len(self.all_instances) - 1)

        return (x, y)

    def find_instances(self, cleanup=True):
        tempdir = tempfile.gettempdir()
        pidfiles = glob.glob(os.path.join(tempdir, 'pid.imgops.*'))

        pids = []
        for file in pidfiles:
            pid = int(file.split('.')[-1])
            if psutil.pid_exists(pid):
                pids.append(pid)
            elif cleanup:
                os.remove(file)
        return pids

    def to_mouse(self):
        pos = QtGui.QCursor.pos()
        x = pos.x() + self.x_offset
        y = pos.y() + self.y_offset
        self.window.setGeometry(x, y, self.window.width(), self.window.height())

    def on_keyrelease(self, key):
        if key == 'Escape' and self.is_top_instance():
            self.abort()

    def on_error(self, exc_info):
        self.show_error(''.join(traceback.format_exception(*exc_info)))

    def show_error(self, text):
        self.abort(quit=False)
        event_binder.stop()

        qtext = QtWidgets.QPlainTextEdit(text)
        qtext.setReadOnly(True)
        qtext.setWindowTitle('Error uploading ' + self.filename)
        qtext.setGeometry(0, 0, 455, 200)
        qtext.move(self.app.desktop().screen().rect().center() - qtext.rect().center())

        self.qtext = qtext
        self.qtext.show()

    def is_top_instance(self):
        return bool(set(self.all_instances).issuperset(self.find_instances(cleanup=False)))

    def on_quit(self):
        event_binder.stop()
        os.remove(self.pidfile)

    def abort(self, quit=True):
        if self.aborted:
            return

        self.update_progress.disconnect()
        try:
            self.animate_timer.timeout.disconnect()
        except Exception:
            pass
        self.aborted = True
        self.window.update()

        if quit:
            QtCore.QTimer.singleShot(100, self.done.emit)
        else:
            QtCore.QTimer.singleShot(100, self.window.close)

    def animate(self, fn, duration, start_value, end_value, callback=None):
        try:
            self.animate_timer.timeout.disconnect()
        except Exception:
            pass

        start = time.time()
        time_fraction = duration / 100
        value_fraction = (end_value - start_value) / 100

        def calc_next():
            delta = time.time() - start
            percent = delta / time_fraction
            fraction = value_fraction * percent
            if delta >= duration:
                self.animate_timer.stop()
                self.animate_timer.timeout.disconnect()
                if callback:
                    callback()

            return start_value + fraction

        self.animate_timer.timeout.connect(lambda: fn(calc_next()))
        self.animate_timer.start(30)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self.canvas)
        pen = self.pen

        angle = int(360 * self.progress)*16

        size = self.window_size - 10

        # circle shadow
        pen.setWidth(self.width)
        pen.setColor(self.shadow_color)
        pen.setCapStyle(Qt.FlatCap)
        painter.setPen(pen)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.drawEllipse(6, 6, size, size)

        # circle
        pen.setWidth(self.width)
        pen.setColor(self.cancel_color if self.aborted else self.color)
        pen.setCapStyle(Qt.FlatCap)
        painter.setPen(pen)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.drawArc(5, 5, size, size, 0, angle)
