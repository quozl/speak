# Copyright (C) 2009, Aleksey Lim
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import sys
import time
import subprocess

import gi
gi.require_version("Gst", "1.0")

from gi.repository import Gst

from gi.repository import GObject

import logging
logger = logging.getLogger('speak')

supported = True


class BaseAudioGrab(GObject.GObject):
    __gsignals__ = {
        'new-buffer': (GObject.SIGNAL_RUN_FIRST, None, [GObject.TYPE_PYOBJECT])
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        self.pipeline = None

    def restart_sound_device(self):
        self.pipeline.set_state(Gst.State.NULL)
        self.pipeline.set_state(Gst.State.PLAYING)

    def stop_sound_device(self):
        #print >>sys.stderr, '%.3f BaseAudioGrab.stop_sound_device' % (time.time())
        if self.pipeline is None:
            return

        self.pipeline.set_state(Gst.State.NULL)
        GObject.timeout_add(10, self._new_buffer, '')

        self.pipeline = None

    def make_pipeline(self, cmd):
        if self.pipeline is not None:
            self.stop_sound_device()
            del self.pipeline

        # build a pipeline that makes speech
        # and sends it to both the audio output
        # and a fake one that we use to draw from
        self.pipeline = Gst.parse_launch('espeak name=espeak' \
            ' ! tee name=me' \
            ' me.! queue ! autoaudiosink' \
            ' me.! queue ! fakesink name=sink')

        def on_buffer(element, data_buffer, pad):
            # we got a new buffer of data
            size = data_buffer.get_size()
            if size == 0:
                #print >>sys.stderr, '%.3f BaseAudioGrab.on_buffer' % \
                #    (time.time())
                return True

            data = data_buffer.extract_dup(0, size)
            #print >>sys.stderr, '%.3f BaseAudioGrab.on_buffer size=%r' % \
            #    (time.time(), size)
            GObject.timeout_add(10, self._new_buffer, data)
            return True

        sink = self.pipeline.get_by_name('sink')
        sink.props.signal_handoffs = True
        sink.connect('handoff', on_buffer)

        def gst_message_cb(bus, message):
            self._was_message = True

            if message.type == Gst.MessageType.WARNING:
                def check_after_warnings():
                    if not self._was_message:
                        self.stop_sound_device()
                    return True

                logger.debug(message.type)
                self._was_message = False
                GObject.timeout_add(500, check_after_warnings)

            elif message.type in (Gst.MessageType.EOS, Gst.MessageType.ERROR):
                #print >>sys.stderr, '%.3f EOS' % (time.time())
                logger.debug(message.type)
                self.stop_sound_device()

        self._was_message = False
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', gst_message_cb)

    def _new_buffer(self, buf):
        #print >>sys.stderr, '%.3f BaseAudioGrab._new_buffer size=%r' % \
        #    (time.time(), len(buf))
        # pass captured audio to everyone who is interested
        self.emit("new-buffer", buf)
        return False


from espeak_gst import AudioGrabGst as AudioGrab
from espeak_gst import *
