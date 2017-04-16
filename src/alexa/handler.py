from alexa.response import AlexaResponse
from jawbone.api import APIRequest


class AlexaHandlerFactory(object):

  def __init__(self, intent, access_token, request_date, session_end=True):
    for cls in HandlerAbstract.__subclasses__():
      if cls.check_handler_type(intent):
        self.__class__ = cls
        self.__init__(access_token, request_date, session_end)
        break


class HandlerAbstract(object):

  def __init__(self, access_token, request_date, session_end=True):
    self.access_token = access_token
    self.request_date = request_date
    self.session_end = session_end
    self.data = None

  @classmethod
  def check_handler_type(cls, handler_type):
    pass

  def process_intent(self):
    pass

  def fetch_data_from_api(self, uri_type):
    jawbone_request = APIRequest(self.access_token, self.request_date)
    if jawbone_request.set_endpoint(uri_type):
      self.data = jawbone_request.fetch_data()
      if self.data:
        return True
      return False
    return False


class HelpHandler(HandlerAbstract):

  response = '''Ask me questions, such as:
                        How did I sleep last night?
                        What is my resting heartrate?
                        How many steps did I take on December 23, 2016? '''

  def __init__(self, access_token, request_date, session_end=True):
    super(HelpHandler, self).__init__(access_token, request_date, session_end)

  @classmethod
  def check_handler_type(cls, handler_type):
    return handler_type == 'GetHelp'

  def process_intent(self):
    return AlexaResponse.build_response(self.response, end_session=self.session_end)


class ExitHandler(HandlerAbstract):

  def __init__(self, access_token, request_date, session_end=True):
    super(ExitHandler, self).__init__(access_token, request_date, session_end)
    self.response = ''
    if not session_end:
      self.response = 'Jawbone powering down.'
    self.session_end = True

  @classmethod
  def check_handler_type(cls, handler_type):
    return handler_type == 'GetExit'

  def process_intent(self):
    return AlexaResponse.build_response(self.response)


class HeartrateHandler(HandlerAbstract):

  response_errored = 'There was an error communicating with the Jawbone servers.'
  response_success = 'Your resting heartrate was {} beats per minute.'
  response_failure = 'I could not find a resting heartrate.'

  def __init__(self, access_token, request_date, session_end=True):
    super(HeartrateHandler, self).__init__(access_token, request_date, session_end)

  @classmethod
  def check_handler_type(cls, handler_type):
    return handler_type == 'GetHeartrate'

  def process_intent(self):
    if self.fetch_data_from_api('heartrate'):
      recent_heartrate = self.process_data()
      if recent_heartrate:
        return AlexaResponse.build_response(self.response_success.format(recent_heartrate), end_session=self.session_end)
      else:
        return AlexaResponse.build_response(self.response_failure, end_session=self.session_end)
    else:
      return AlexaResponse.build_response(self.response_errored)

  def process_data(self):
    heartrate = ''
    print self.data
    print self.data['data']
    print self.data['data']['items']
    for item in self.data['data']['items']:
        if item.get('resting_heartrate'):
          heartrate = item['resting_heartrate']
          break
    return heartrate


class StepsHandler(HandlerAbstract):

  response_errored = 'There was an error communicating with the Jawbone servers.'
  response_success = 'You took {} steps of your {} step goal. {}'
  response_success_completed = 'Good Job!'

  def __init__(self, access_token, request_date, session_end=True):
    super(StepsHandler, self).__init__(access_token, request_date, session_end)

  @classmethod
  def check_handler_type(cls, handler_type):
    return handler_type == 'GetSteps'

  def process_intent(self):
    if self.fetch_data_from_api('goals'):
      message = self.process_data()
      return AlexaResponse.build_response(message, end_session=self.session_end)
    else:
      return AlexaResponse.build_response(self.response_errored)

  def process_data(self):
    steps_goal = self.data['data']['move_steps']
    steps_left = self.data['data']['remaining_for_day']['move_steps_remaining']
    steps_total = steps_goal - steps_left
    steps_congrats = 'Good Job!' if steps_goal < steps_total else ''
    return self.response_success.format(steps_total, steps_goal, steps_congrats)


class SleepHandler(HandlerAbstract):

  response_errored = 'There was an error communicating with the Jawbone servers'
  response_success = 'You slept for a total of {} hours and {} minutes and woke up {} throughout the night.'
  response_failure = 'I could not find any sleep data, did you wear your up band while sleeping?'

  def __init__(self, access_token, request_date, session_end=True):
    super(SleepHandler, self).__init__(access_token, request_date, session_end)

  @classmethod
  def check_handler_type(cls, handler_type):
    return handler_type == 'GetSleep'

  def process_intent(self):
    if self.fetch_data_from_api('sleeps'):
      if self.data['data'].get('items'):
        message = self.process_data()
        return AlexaResponse.build_response(message, end_session=self.session_end)
      else:
        return AlexaResponse.build_response(self.response_failure, end_session=self.session_end)
    else:
      return AlexaResponse.build_response(self.response_errored)

  def process_data(self):
    sleep_data = self.data['data']['items'][0]['details']
    sleep_total_minutes, _ = divmod(sleep_data['duration'] - sleep_data['awake'], 60)
    sleep_total_hours, sleep_total_minutes = divmod(sleep_total_minutes, 60)
    sleep_awakenings = sleep_data['awakenings']
    if sleep_awakenings != 1:
      sleep_awakenings_string = "{} times".format(sleep_awakenings)
    else:
      sleep_awakenings_string = "{} time".format(sleep_awakenings)
    return self.response_success.format(sleep_total_hours, sleep_total_minutes, sleep_awakenings_string)
