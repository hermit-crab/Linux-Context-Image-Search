import os
import webbrowser
from threading import Thread
import tkinter
from tkinter import ttk


def run(filename, search_provider):
    root = tkinter.Tk()
    root.geometry('200x25')
    root.title(os.path.split(filename)[1])
    root.attributes('-topmost', 1)

    bar = ttk.Progressbar(root, orient='horizontal', mode='determinate')
    bar.pack(expand=True, fill=tkinter.BOTH)

    def progress_fn(prc):
        root.after_idle(bar_update, prc*100)

    provider = search_provider(progress_fn)

    progress = 0

    def bar_update(percent):
        nonlocal progress
        if percent >= 100:
            # tkinter progressbar resets at 100
            percent = 99
        bar.step(percent - progress)
        progress = percent

    def search():
        url = provider.search(filename)
        root.after_idle(done, url)

    def done(url):
        root.destroy()
        webbrowser.open(url)

    thread = Thread(target=search)
    thread.start()

    root.mainloop()
