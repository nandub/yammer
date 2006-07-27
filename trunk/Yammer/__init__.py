import TicketExceptionHandler
def contextInitialize(app, ctxPath):
  app._exceptionHandlerClass= \
    TicketExceptionHandler.TicketExceptionHandler
  print "running yammer context initialization"
