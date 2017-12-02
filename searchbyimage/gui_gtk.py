import sys
import os
import webbrowser
from threading import Thread

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib


def run(filename, search_provider):

    GLADE_XML_PATH = os.path.join(os.path.dirname(__file__), 'res/gui_gtk.glade')

    builder = Gtk.Builder()
    builder.add_from_file(GLADE_XML_PATH)
    window = builder.get_object('window')
    window.set_title(os.path.split(filename)[1])
    bar = builder.get_object('progressbar')
    window.show_all()

    def bar_update(percent):
        bar.set_fraction(percent)

    def progress_fn(percent):
        GLib.idle_add(bar_update, percent)

    provider = search_provider(progress_fn)

    def search():
        url = provider.search(filename)
        GLib.idle_add(done, url)

    def done(url):
        Gtk.main_quit()
        webbrowser.open(url)

    thread = Thread(target=search)
    thread.start()

    Gtk.main()
