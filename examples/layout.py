import clutter, gtk.gdk
import sys

class SpectrumDisplay:
  def __init__(self):
    self.slide = clutter.Group()
    self.slide.visible = True
    a = clutter.Rectangle()
    a.set_width(16)
    a.set_height(9)
    a.set_color(clutter.color_parse('red'))
    a.set_position(0,0)
    a.visible = True
    self.slide.add(a)
    self.slide._timeline = clutter.Timeline(30, 25)
    self.slide._timeline.set_loop(True)
    alpha = clutter.Alpha(self.slide._timeline, clutter.ramp_func)
    self.slide._behaviour = clutter.BehaviourOpacity(0xdd, 0, alpha)
    self.slide._behaviour.apply(a)
    self.slide._timeline.start()

slide = SpectrumDisplay().slide
