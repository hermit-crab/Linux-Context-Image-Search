# modified from https://github.com/LiuLang/python3-keybinder/blob/master/examples/keybinder_demo.py

import logging

from Xlib import X
from Xlib import XK
from Xlib.ext import record
from Xlib.protocol import rq

from keybinder import keybinder


def lookup_keysym(keysym):
    for name in dir(XK):
        if name[:3] == 'XK_' and getattr(XK, name) == keysym:
            return name[3:]
    return '[%d]' % keysym


def recorder(reply, mousemove_fn, keyrelease_fn):
    if reply.category != record.FromServer:
        return
    if reply.client_swapped:
        logging.warning('* received swapped protocol data, cowardly ignored')
        return
    if len(reply.data) == 0 or reply.data[0] < 2:
        # not an event
        return

    data = reply.data
    while len(data) > 0:
        event, data = rq.EventField(None).parse_binary_value(data,
                keybinder.record_dpy.display, None, None)

        if event.type == X.KeyRelease:

            keysym = keybinder.local_dpy.keycode_to_keysym(event.detail, 0)
            if not keysym:
                keyrelease_fn(event.detail)
            else:
                keyrelease_fn(lookup_keysym(keysym))

        elif event.type == X.MotionNotify:
            mousemove_fn(event.root_x, event.root_y)


def listen(mousemove_fn, keyrelease_fn):
    keybinder.bind(lambda e: recorder(e, mousemove_fn, keyrelease_fn))


def stop():
    keybinder.unbind()
