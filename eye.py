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
# Speak.activity is free software: you can redistribute it and/or modify
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

import math

from gi.repository import Gtk


class Eye(Gtk.DrawingArea):
    def __init__(self, fill_color):
        Gtk.DrawingArea.__init__(self)
        self.connect("draw", self._draw_cb)
        self.x, self.y = 0, 0
        self.fill_color = fill_color

    def has_padding(self):
        return True

    def has_left_center_right(self):
        return False

    def look_at(self, x, y):
        self.x = x
        self.y = y
        self.queue_draw()

    def look_ahead(self):
        self.x = None
        self.y = None
        self.queue_draw()

    # Thanks to xeyes :)
    def computePupil(self):
        a = self.get_allocation()

        if self.x is None or self.y is None:
            # look ahead, but not *directly* in the middle
            pw = self.get_parent().get_allocation().width
            if a.x + a.width / 2 < pw / 2:
                cx = a.width * 0.6
            else:
                cx = a.width * 0.4
            return cx, a.height * 0.6

        EYE_X, EYE_Y = self.translate_coordinates(
            self.get_toplevel(), a.width / 2, a.height / 2)
        EYE_HWIDTH = a.width
        EYE_HHEIGHT = a.height
        BALL_DIST = EYE_HWIDTH / 4

        dx = self.x - EYE_X
        dy = self.y - EYE_Y

        if dx or dy:
            angle = math.atan2(dy, dx)
            cosa = math.cos(angle)
            sina = math.sin(angle)
            h = math.hypot(EYE_HHEIGHT * cosa, EYE_HWIDTH * sina)
            x = (EYE_HWIDTH * EYE_HHEIGHT) * cosa / h
            y = (EYE_HWIDTH * EYE_HHEIGHT) * sina / h
            dist = BALL_DIST * math.hypot(x, y)

            if dist < math.hypot(dx, dy):
                dx = dist * cosa
                dy = dist * sina

        return a.width / 2 + dx, a.height / 2 + dy

    def _draw_cb(self, widget, cr):
        bounds = self.get_allocation()

        eyeSize = min(bounds.width, bounds.height)
        outlineWidth = eyeSize / 20.0
        pupilSize = eyeSize / 10.0
        pupilX, pupilY = self.computePupil()
        dX = pupilX - bounds.width / 2.
        dY = pupilY - bounds.height / 2.
        distance = math.sqrt(dX * dX + dY * dY)
        limit = eyeSize / 2 - outlineWidth * 2 - pupilSize
        if distance > limit:
            pupilX = bounds.width / 2 + dX * limit / distance
            pupilY = bounds.height / 2 + dY * limit / distance

        # background
        cr.set_source_rgba(*self.fill_color.get_rgba())
        cr.rectangle(0, 0, bounds.width, bounds.height)
        cr.fill()

        # eye ball
        cr.arc(bounds.width / 2, bounds.height / 2,
               eyeSize / 2 - outlineWidth / 2, 0, 2 * math.pi)
        cr.set_source_rgb(1, 1, 1)
        cr.fill()

        # outline
        cr.set_line_width(outlineWidth)
        cr.arc(bounds.width / 2, bounds.height / 2,
               eyeSize / 2 - outlineWidth / 2, 0, 2 * math.pi)
        cr.set_source_rgb(0, 0, 0)
        cr.stroke()

        # pupil
        cr.arc(pupilX, pupilY, pupilSize, 0, 2 * math.pi)
        cr.set_source_rgb(0, 0, 0)
        cr.fill()

        return True
