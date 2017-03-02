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

# This code is a stripped down version of the waveform view from Measure

import cairo
from mouth import Mouth

class WaveformMouth(Mouth):

    def __init__(self, audio, fill_color):
        Mouth.__init__(self, audio, fill_color)
        audio.connect_wave(self.__wave_cb)
        audio.connect_idle(self.__idle_cb)
        self.wave = []

    def __wave_cb(self, audio, wave):
        self.wave = wave
        self.queue_draw()

    def __idle_cb(self, audio):
        self.wave = [0] * len(self.wave)
        self.queue_draw()

    def draw_cb(self, widget, cr):
        bounds = self.get_allocation()

        # disable antialiasing
        cr.set_antialias(cairo.ANTIALIAS_NONE)

        # background
        cr.set_source_rgba(*self.fill_color.get_rgba())
        cr.rectangle(0, 0, bounds.width, bounds.height)
        cr.fill()

        # prepare for drawing
        cr.set_line_width(min(bounds.height / 10.0, 10))
        cr.set_source_rgb(0, 0, 0)

        # draw waveform
        p1 = bounds.height / 32768.0  # signed 16-bit integer data maximum
        p2 = bounds.height / 2.0
        y_mag_bias = 1
        y_mag = 0.7
        count = 0
        for value in self.wave:
            peak = float(p1 * value * y_mag) + y_mag_bias * p2
            peak = min(bounds.height, peak)
            peak = max(0, peak)

            cr.line_to(count * bounds.width / len(self.wave),
                       bounds.height - peak)

            count += 1

        cr.stroke()
