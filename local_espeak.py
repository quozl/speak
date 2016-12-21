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

import subprocess

try:
    from sugar3.speech import SpeechManager
    _HAS_SPEECH_MANAGER = True
except ImportError:
    import gi
    gi.require_version("Gst", "1.0")

    from gi.repository import Gst
    Gst.init([])

    _HAS_SPEECH_MANAGER = False

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
        self.quiet = True

    def restart_sound_device(self):
        self.quiet = False

        self.pipeline.set_state(Gst.State.NULL)
        self.pipeline.set_state(Gst.State.PLAYING)

    def stop_sound_device(self):
        if self.pipeline is None:
            return

        self.pipeline.set_state(Gst.State.NULL)
        # Shut theirs mouths down
        self._new_buffer('')

        self.quiet = True

    def make_pipeline(self, cmd):
        if self.pipeline is not None:
            self.stop_sound_device()
            del self.pipeline

        # build a pipeline that reads the given file
        # and sends it to both the real audio output
        # and a fake one that we use to draw from
        self.pipeline = Gst.parse_launch(
                cmd + ' ' \
                '! decodebin use-buffering=true ' \
                '! capsfilter caps="audio/x-raw, format=(string)S16LE, ' \
                    'layout=(string)interleaved, rate=(int)22050, ' \
                    'channels=(int)1"' \
                '! audioconvert ' \
                '! tee name=t ' \
                '! queue2 name=appsink_queue max-size-bytes=0 ' \
                    'max-size-buffers=0  max-size-time=0 ' \
                '! appsink caps="audio/x-raw, format=(string)S16LE, ' \
                    'layout=(string)interleaved, rate=(int)22050, '\
                    'channels=(int)1" drop=false max-buffers=10 sync=true ' \
                    'emit-signals=true t. ' \
                '! queue2 name=autoaudio_queue max-size-bytes=0 ' \
                    'max-size-buffers=0 max-size-time=0 '\
                '! audioresample '\
                '! autoaudiosink sync=true')

        def on_buffer(element, buffer, pad):
            # we got a new buffer of data, ask for another
            GObject.timeout_add(100, self._new_buffer, str(buffer))
            return True

        # sink = self.pipeline.get_by_name('sink')
        # sink.props.signal_handoffs = True
        # sink.connect('handoff', on_buffer)

        def gst_message_cb(bus, message):
            self._was_message = True

            if message.type == Gst.MessageType.WARNING:
                def check_after_warnings():
                    if not self._was_message:
                        self.stop_sound_device()
                    return True

                logger.debug(message.type)
                self._was_message = False
                GObject.timeout_add(500, self._new_buffer, str(buffer))

            elif  message.type in (Gst.MessageType.EOS, Gst.MessageType.ERROR):
                logger.debug(message.type)
                self.stop_sound_device()

        self._was_message = False
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', gst_message_cb)

    def _new_buffer(self, buf):
        if not self.quiet:
            # pass captured audio to anyone who is interested
            self.emit("new-buffer", buf)
        return False

# load proper espeak plugin

if _HAS_SPEECH_MANAGER:
    from espeak_speech import AudioGrabSpeech as AudioGrab
    from espeak_speech import *
    logger.info('user sugar-speech')
else:
    try:
        from gi.repository import Gst
        Gst.ElementFactory.make('espeak')
        from espeak_gst import AudioGrabGst as AudioGrab
        from espeak_gst import *
        logger.info('use gst-plugins-espeak')
    except Exception, e:
        logger.info('disable gst-plugins-espeak: %s' % e)
        if subprocess.call('which espeak', shell=True) == 0:
            from espeak_cmd import AudioGrabCmd as AudioGrab
            from espeak_cmd import *
        else:
            logger.info('disable espeak_cmd')
            supported = False
