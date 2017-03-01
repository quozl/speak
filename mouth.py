# Speak.activity
# A simple front end to the espeak text-to-speech engine on the XO laptop
# http://wiki.laptop.org/go/Speak
#
# Copyright (C) 2008  Joshua Minor
# This file is part of Speak.activity
#
# Parts of Speak.activity are based on code from Measure.activity
# Copyright (C) 2007  Arjun Sarwal - arjun@laptop.org
# 
#     Speak.activity is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     Speak.activity is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with Speak.activity.  If not, see <http://www.gnu.org/licenses/>.

# This code is a super-stripped down version of the waveform view from Measure

import sys
import time
import cairo
from struct import unpack
import numpy.core

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from gi.repository import GObject


class Mouth(Gtk.DrawingArea):
    def __init__(self, audio, fill_color):

        #print >>sys.stderr, '%.3f Mouth.__init__' % (time.time())
        Gtk.DrawingArea.__init__(self)

        def __realize_cb(widget):
            #print >>sys.stderr, '%.3f Mouth.__realize_cb' % (time.time())
            widget.connect("draw", self.__expose_cb)
        self.connect("realize", __realize_cb)

        self.volume = 0
        self.buffer = []
        self.bytes = 2756
        self.fill_color = fill_color

        self._audio = audio
        self._new_buffer_hid = self._audio.connect("new-buffer",
                                                   self.__new_buffer_cb)
        GObject.timeout_add(100, self.__timeout_cb)

    def disconnect_audio(self):
        #print >>sys.stderr, '%.3f Mouth.disconnect_audio' % (time.time())
        self._audio.disconnect(self._new_buffer_hid)
        self._new_buffer_hid = None

    def __new_buffer_cb(self, obj, buf):
        # accumulate buffer and dequeue at 22050 bps
        if len(buf) > 0:
            mine = list(unpack(str(len(buf) / 2) + 'h', buf))
            self.buffer += mine
            #print >>sys.stderr, '%.3f Mouth.__new_buffer_cb total=%r' % \
            #    (time.time(), len(self.buffer))
        else:
            self.volume = 0
            #print >>sys.stderr, '%.3f Mouth.__new_buffer_cb stop' % \
            #    (time.time())
            self.queue_draw()

    def __timeout_cb(self):
        if len(self.buffer) < self.bytes:
            return True

        chunk = self.buffer[0:self.bytes]
        del self.buffer[0:self.bytes]

        self.volume = numpy.core.max(chunk)
        self.queue_draw()
        #print >>sys.stderr, '%.3f Mouth.__timeout_cb volume=%r total=%r' % \
        #    (time.time(), self.volume, len(self.buffer))

        return True

    def __expose_cb(self, widget, cr):
        """This function is the "expose" event handler and does all the drawing."""
        #print >>sys.stderr, '%.3f Mouth.__expose_cb volume=%r' % \
        #    (time.time(), self.volume)
        bounds = self.get_allocation()

        # disable antialiasing
        cr.set_antialias(cairo.ANTIALIAS_NONE)

        # background
        cr.set_source_rgba(*self.fill_color.get_rgba())
        cr.rectangle(0, 0, bounds.width, bounds.height)
        cr.fill()

        # Draw the mouth
        volume = self.volume / 30000.
        mouthH = volume * bounds.height
        mouthW = volume**2 * (bounds.width / 2.) + bounds.width / 2.
        #        T
        #  L          R
        #        B
        Lx, Ly = bounds.width / 2 - mouthW / 2, bounds.height / 2
        Tx, Ty = bounds.width / 2, bounds.height / 2 - mouthH / 2
        Rx, Ry = bounds.width / 2 + mouthW / 2, bounds.height / 2
        Bx, By = bounds.width / 2, bounds.height / 2 + mouthH / 2
        cr.set_line_width(min(bounds.height / 10.0, 10))
        cr.move_to(Lx, Ly)
        cr.curve_to(Tx, Ty, Tx, Ty, Rx, Ry)
        cr.curve_to(Bx, By, Bx, By, Lx, Ly)
        cr.set_source_rgb(0, 0, 0)
        cr.close_path()
        cr.stroke()

        return False
