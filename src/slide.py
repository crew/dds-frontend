from clutter import Group

class Slide(Group):

  def __init__(self, transition):
    self.transition = transition
    Group.__init__(self)

