import clutter
import logging
import baseslide

class PitcamSlide(baseslide.BaseSlide):
  def __init__ (self):
    baseslide.BaseSlide.__init__(self)

    slideTitle = clutter.Text()
    slideTitle.set_text('Pitcam, foo')
    slideTitle.set_font_name('serif 71')
    slideTitle.set_color(clutter.color_from_string("gold"))
    slideTitle.set_size(1920, 100)
    slideTitle.set_position(200, 100)
    self.group.add(slideTitle)

    self.newcam = None
    self.oldcam = None
    self.getnew()
    self.getold()

  def setupslide():
    self.update()

  def update(self):
    self.getnew()
    self.getold()

  def getold(self):
    self.oldcam = self.GetTextureFromURL('http://pitcam.ccs.neu.edu/'
                                          'old.jpeg', self.oldcam)
    self.oldcam.set_position(940, 300)
    self.oldcam.set_size(640,480)
    self.oldcam.visible = True
    self.oldcam.show()
    self.group.add(self.oldcam)
    logging.info('Done fetching pitcam old')

  def getnew(self):
    self.newcam = self.GetTextureFromURL('http://pitcam.ccs.neu.edu/'
                                          'new.jpeg', self.newcam)
    self.newcam.set_position(140, 300)
    self.newcam.set_size(640,480)
    self.newcam.visible = True
    self.newcam.show()
    self.group.add(self.newcam)

    logging.info('Done fetching pitcam new')

app = PitcamSlide()
slide = app.group
