import clutter, gtk.gdk
import sys

class SpectrumDisplay:
  def __init__(self):
    self.stage = clutter.stage_get_default()
    self.stage.fullscreen()
    self.stage.set_color(clutter.color_parse("black"))

    self.spectrum = clutter.Texture('spectrum.png')
    self.spectrum.set_width(self.stage.get_width())
    self.spectrum.set_height(self.stage.get_height())
    self.spectrum.set_position(0,0)
    self.stage.add(self.spectrum)

    self.textsliced = clutter.Texture('text-sliced.png')
    self.textsliced.set_width(self.stage.get_width())
    self.textsliced.set_height(self.stage.get_height())
    self.textsliced.set_position(0,0)
    self.stage.add(self.textsliced)

    self.timeline = clutter.Timeline(30, 25)
    self.timeline.set_loop(True)
    alpha = clutter.Alpha(self.timeline, clutter.ramp_func)
    self.behaviour = clutter.BehaviourOpacity(0xdd, 0, alpha)
    self.behaviour.apply(self.textsliced)

    self.stage.connect('destroy', clutter.main_quit)
    self.stage.connect('key-press-event', on_key_press_event)

    # show the stage and run clutter
  def run(self):
    self.stage.show_all()
    self.timeline.start()
    clutter.main()

def on_key_press_event(stage, event):
  if (event.keyval == 113):
    clutter.main_quit()

def main(args):
  app = SpectrumDisplay()
  app.run()
  return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
