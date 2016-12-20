# Copyright (C) 2016, Cristian Garcia
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

import re
import subprocess

from gi.repository import GObject

from sugar3.speech import SpeechManager

import logging
logger = logging.getLogger('speak')

import local_espeak as espeak

supported = True

PITCH_MAX = SpeechManager.MAX_PITCH
RATE_MAX = SpeechManager.MAX_RATE

class AudioGrabSpeech(espeak.BaseAudioGrab):

    def __init__(self):
        espeak.BaseAudioGrab.__init__(self)
        self.speech = SpeechManager()

    def restart_sound_device(self):
        self.speech.restart()

    def stop_sound_device(self):
        self.speech.stop()

    def speak(self, status, text):
        lang = status.voice.language
        if len(lang) > 2 and "-" in lang:
            lang = lang[:2] + "_" + lang[3:]

        self.speech.say_text(text, pitch=status.pitch, rate=status.rate,
                lang_code=lang)

def voices():
    out = []
    speech = SpeechManager()
    languages = speech.get_all_voices()

    for language in languages:
        out.append((language, languages[language]))

    return out
