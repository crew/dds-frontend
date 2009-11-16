import clutter
import sys
import baseslide
import pywapi

class WeatherDisplay(baseslide.BaseSlide):
  def __init__(self, location):
    """ Initializes the stage and score for this slide. """
    baseslide.BaseSlide.__init__(self)
    self.location = location
    self.icon = None
    self.photo = None
    self.photo2 = None
    self.addweather(location)

  def setupslide(self):
    self.refresh(self.location)

  def refresh(self, location):
    self.group.remove_all()
    self.addweather(location)

  def addweather(self, location):
    """ Adds the weather information to this slide. """
    #rssfeed = feedparser.parse(feedURL)
    #feedtitle = remove_html_tags(rssfeed.feed.title)

    weather = pywapi.get_weather_from_google(location)

    feedtitle = "Weather " + weather['forecast_information']['city']
    feedtitleActor = clutter.Text()
    feedtitleActor.set_text(feedtitle)
    feedtitleActor.set_font_name("serif 71")
    feedtitleActor.set_color(clutter.color_from_string("gold"))
    feedtitleActor.set_size(1920, 100)
    feedtitleActor.set_position(20, 0)
    self.group.add(feedtitleActor)

    feedtemp = clutter.Text()
    feedtemp.set_text(weather['current_conditions']['condition'] + 
      ' ' + weather['current_conditions']['temp_f'] + "F")
    feedtemp.set_font_name("serif 48")
    feedtemp.set_color(clutter.color_from_string("white"))
    feedtemp.set_size(1920, 100)
    feedtemp.set_position(20, 100)
    self.group.add(feedtemp)

    self.icon = self.GetTextureFromURL('http://www.google.com' +
       weather['current_conditions']['icon'], self.icon)
    self.icon.set_position(20, 200)
    self.icon.set_size(256,256)
    self.icon.show()
    self.group.add(self.icon)

    self.photo = self.GetTextureFromURL('http://155.33.227.163:8080/5/webcam.jpg',
                                         self.photo)
    self.photo.set_position(300, 200)
    self.photo.set_size(370, 278)
    self.photo.set_clip(0,0,370,256)
    self.photo.show()
    self.group.add(self.photo)

    self.photo2 = self.GetTextureFromURL('http://155.33.227.163:8080/2/webcam.jpg',
                                          self.photo2)
    self.photo2.set_position(700, 200)
    self.photo2.set_size(370, 278)
    self.photo2.set_clip(0,0,370,256)
    self.photo2.show()
    self.group.add(self.photo2)


    y = 500
    for forecast in weather['forecasts']:
      y += self.add_forecast_group(forecast, y, width=1920) + 20

  def add_forecast_group(self, forecast, starty, width=1920):
    title = clutter.Text()
    title.set_text(forecast['day_of_week']+' ('+
          forecast['low']+'F - '+forecast['high']+'F)')
    title.set_font_name("serif 32")
    title.set_width(width)
    title.set_color(clutter.color_from_string("white"))
    title.set_position(20, starty)
    self.group.add(title)

    content = clutter.Text()
    content.set_text(forecast['condition'])
    content.set_font_name("serif 24")
    content.set_color(clutter.color_from_string("white"))
    content.set_position(20, starty + title.get_height())
    content.set_width(width)
    self.group.add(content)

    return title.get_height() + content.get_height()

def main(args=None):
  app = WeatherDisplay("02120")
  return 0

if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))

# Put the ClutterGroup containing all the slide information
# in the top level, so that DDS can get at it.
app = WeatherDisplay("02120")

slide = app.group
