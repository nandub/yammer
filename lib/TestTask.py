from TaskKit.Task import Task

class TestTask(Task):
  def run(self):
    print self.name(), "mommy, I'm running"
