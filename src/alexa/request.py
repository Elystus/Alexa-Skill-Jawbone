from alexa.handler import AlexaHandlerFactory
from alexa.response import AlexaResponse
import logging


class AlexaRequestFactory(object):

  def __init__(self, request_type, event, context):
    for cls in RequestAbstract.__subclasses__():
      if cls.check_request_type(request_type):
        self.__class__ = cls
        self.__init__(event, context)
        return
    self.__class__ = RequestError
    self.__init__(event, context)


class RequestAbstract(object):

  def __init__(self, event, context):
    self.event = event
    self.context = context

  def process(self):
    pass


class RequestIntent(RequestAbstract):

  response_error_message = 'Sorry, I was not able to finish your request.'

  def __init__(self, event, context):
    super(RequestIntent, self).__init__(event, context)

  @classmethod
  def check_request_type(cls, request_type):
    return request_type == 'IntentRequest'

  def process(self):
    try:
      user_intent = self.event['request']['intent'].get('name')
      user_access_token = self.event['session']['user'].get('accessToken')
      user_session_new = self.event['session'].get('new')
      user_request_date = None
      if self.event['request']['intent']['slots'].get('RequestDate'):
        user_request_date = self.event['request']['intent']['slots']['RequestDate'].get('value')
      intent_handler = AlexaHandlerFactory(user_intent, user_access_token, user_request_date, user_session_new)
      return intent_handler.process_intent()
    except Exception as e:
      logging.error('There as an error processing this request. '
                    '\nEvent: {} '
                    '\nContext: {}'.format(self.event, self.context))
      return AlexaResponse.build_response(self.response_error_message)



class RequestLaunch(RequestAbstract):

  response_message = 'Jawbone. Everything is looking up!'

  def __init__(self, event, context):
    super(RequestLaunch, self).__init__(event, context)

  @classmethod
  def check_request_type(cls, request_type):
    return request_type == 'LaunchRequest'

  def process(self):
    return AlexaResponse.build_response(self.response_message, end_session=False)


class RequestEnd(RequestAbstract):

  response_message = 'Jawbone powering down. Goodbye!'

  def __init__(self, event, context):
    super(RequestEnd, self).__init__(event, context)

  @classmethod
  def check_request_type(cls, request_type):
    return request_type == 'SessionEndedRequest'

  def process(self):
    return AlexaResponse.build_response(self.response_message)


class RequestError(RequestAbstract):

  response_message = 'Sorry, I was not able to finish your request.'

  def __init__(self, event, context):
    super(RequestError, self).__init__(event, context)

  @classmethod
  def check_request_type(cls, request_type):
    return request_type == ''

  def process(self):
    logging.error('There as an error processing this request. \nEvent: {} \nContext: {}'.format(self.event, self.context))
    return AlexaResponse.build_response('I was unable to process your request.')
