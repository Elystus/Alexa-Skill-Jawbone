# Todo
# Strip this file down to entry functions, and determine how to create an entry point for Amazon Lambda (Andrew)

import urlparse
import urllib2
import logging
import time
import json


class IntentHandlerAbstract(object):
  def __init__(self, access_token, request_date, session_end=True):
    self.access_token = access_token
    self.request_date = request_date
    self.session_end = session_end
    self.api_url = 'https://jawbone.com/nudge/api/v.1.1'
    self.api_uri_list = {
      'heartrate': '/users/@me/heartrates?date={}',
      'sleeps': '/users/@me/sleeps?date={}',
      'goals': '/users/@me/goals?date={}'
    }

  def process_intent(self):
    pass

  def build_response(self, message):
    speech_json = JSONResponseBuilder.build_json_response_speech(message)
    json_response = JSONResponseBuilder.build_json_response(speech_json, end_session=self.session_end)
    return JSONResponseBuilder.build_json(json_response)

  def build_response_error(self, message, err=''):
    logging.error('An error was encountered. Message: {} Error: {}'.format(message, err))
    speech_json = JSONResponseBuilder.build_json_response_speech(message)
    json_response = JSONResponseBuilder.build_json_response(speech_json, end_session=self.session_end)
    return JSONResponseBuilder.build_json(json_response)

  def fetch_data_from_api(self, url):
    response = {}
    try:
      http_headers = {
        "Accept": "application/json",
        "Authorization": "Bearer {}".format(self.access_token)
      }
      request = urllib2.Request(url, headers=http_headers)
      response = json.loads(urllib2.urlopen(request).read())
    except Exception as e:
      logging.error('Unable to correctly poll data from Jawbone API. URL: {} Error: {}'.format(url, e))
      response = {}
    return response

  def build_api_url(self, api_uri):
    api_url = '{}{}'.format(self.api_url, api_uri)
    api_url = api_url.format(self.request_date)
    logging.error(api_url)
    return self.fetch_data_from_api(api_url)


class GetHelp(IntentHandlerAbstract):
  def __init__(self, access_token, request_date, session_end=True):
    super(GetHelp, self).__init__(access_token, request_date, session_end)
    self.response = '''Ask me questions, such as:
            How did I sleep last night?
            What is my resting heartrate?
            How many steps did I take on December 23, 2016?
        '''

  def process_intent(self):
    return self.build_response(self.response)


class GetExit(IntentHandlerAbstract):
  def __init__(self, access_token, request_date, session_end=True):
    super(GetExit, self).__init__(access_token, request_date, session_end)
    self.response = ''
    if not session_end:
      self.response = 'Jawbone powering down.'
    self.session_end = True

  def process_intent(self):
    return self.build_response(self.response)


class GetHeartrate(IntentHandlerAbstract):
  def __init__(self, access_token, request_date, session_end=True):
    super(GetHeartrate, self).__init__(access_token, request_date, session_end)
    self.response_errored = 'There was an error communicating with the Jawbone servers.'
    self.response_success = 'Your resting heartrate was {} beats per minute.'
    self.response_failure = 'I could not find a resting heartrate.'

  def process_intent(self):
    data = self.build_api_url(self.api_uri_list['heartrate'])
    if data:
      recent_heartrate = None
      logging.error(data)
      for item in data['data']['items']:
        if item['resting_heartrate']:
          recent_heartrate = item['resting_heartrate']
          break
      heartrate_message = ''
      if recent_heartrate:
        return self.build_response(self.response_success.format(recent_heartrate))
      else:
        return self.build_response(self.response_failure)
    else:
      return self.build_response_error(self.response_errored)


class GetSteps(IntentHandlerAbstract):
  def __init__(self, access_token, request_date, session_end=True):
    super(GetSteps, self).__init__(access_token, request_date, session_end)
    self.response_errored = 'There was an error communicating with the Jawbone servers.'
    self.response_success = 'You took {} steps of your {} step goal. {}'

  def process_intent(self):
    response = self.build_api_url(self.api_uri_list['goals'])
    if response:
      steps_goal = response['data']['move_steps']
      steps_left = response['data']['remaining_for_day']['move_steps_remaining']
      steps_total = steps_goal - steps_left
      steps_congrats = 'Good Job!' if steps_goal < steps_total else ''
      return self.build_response(self.response_success.format(steps_total, steps_goal, steps_congrats))
    else:
      return self.build_response_error(self.response_errored)


class GetSleep(IntentHandlerAbstract):
  def __init__(self, access_token, request_date, session_end=True):
    super(GetSleep, self).__init__(access_token, request_date, session_end)
    self.response_errored = 'There was an error communicating with the Jawbone servers'
    self.response_success = 'You slept for a total of {} hours and {} minutes and woke up {} throughout the night.'
    self.response_failure = 'I could not find any sleep data, did you wear your Up band while sleeping?'

  def process_intent(self):
    response = self.build_api_url(self.api_uri_list['sleeps'])
    if response:
      if response['data']['items']:
        sleep_data = response['data']['items'][0]['details']

        sleep_total_minutes, _ = divmod(sleep_data['duration'] - sleep_data['awake'], 60)
        sleep_total_hours, sleep_total_minutes = divmod(sleep_total_minutes, 60)
        sleep_awakenings = sleep_data['awakenings']
        sleep_awakenings_string = "{} times".format(sleep_awakenings) if sleep_awakenings != 1 else "{} time".format(
          sleep_awakenings)
        return self.build_response(
          self.response_success.format(sleep_total_hours, sleep_total_minutes, sleep_awakenings_string))
      else:
        return self.build_response(self.response_failure)
    else:
      return IntentHandlerAbstract.build_response_error(self.response_errored)


class JawboneHandler(object):
  def __init__(self, user_access_token, user_request_date, user_session_new):
    self.request_date = self._setup_request_date(user_request_date)
    self.access_token = user_access_token
    self.session_new = user_session_new

  def _setup_request_date(self, user_request_date):
    if user_request_date:
      request_date = user_request_date.replace("-", "")
    else:
      request_date = time.strftime("%Y%m%d")
    logging.error("Error: {}".format(request_date))
    return request_date

  def process_intent(self, user_intent):
    if user_intent == 'GetHeartrate':
      json_return = GetHeartrate(self.access_token, self.request_date, self.session_new).process_intent()
    elif user_intent == 'GetSteps':
      json_return = GetSteps(self.access_token, self.request_date, self.session_new).process_intent()
    elif user_intent == 'GetSleep':
      json_return = GetSleep(self.access_token, self.request_date, self.session_new).process_intent()
    elif user_intent == 'GetHelp':
      json_return = GetHelp(self.access_token, self.request_date, self.session_new).process_intent()
    elif user_intent == 'GetExit':
      json_return = GetExit(self.access_token, self.request_date, self.session_new).process_intent()
    else:
      json_return = None
    return json_return


class JSONResponseBuilder(object):
  @staticmethod
  def build_json(response):
    return {
      "version": "1.0",
      "sessionAttributes": {},
      "response": response
    }

  @staticmethod
  def build_json_response(speech, reprompt=None, card=None, end_session=True):
    return {
      "outputSpeech": speech,
      "reprompt": reprompt,
      "card": card,
      "shouldEndSession": end_session
    }

  @staticmethod
  def build_json_response_reprompt(message):
    return {"outputSpeech": build_json_response_speech(message)}

  @staticmethod
  def build_json_response_speech(message):
    return {
      "type": "PlainText",
      "text": message
    }

  @staticmethod
  def build_json_response_card(card_title, card_message):
    return {
      "type": "Simple",
      "title": card_title,
      "content": card_message
    }


def jawbone_entry(event, context):
  request_type = event['request'].get('type')
  response = None
  if request_type == 'LaunchRequest':
    response = jawbone_launch(event, context)
  elif request_type == 'IntentRequest':
    response = jawbone_intent(event, context)
  elif request_type == 'SessionEndedRequest':
    response = jawbone_ended(event, context)
  else:
    response = jawbone_error(event, context)
  return response


def jawbone_intent(event, context):
  user_intent = event['request']['intent'].get('name')
  user_access_token = event['session']['user'].get('accessToken')
  user_session_new = event['session'].get('new')
  user_request_date = None
  if event['request']['intent']['slots'].get('RequestDate'):
    user_request_date = event['request']['intent']['slots']['RequestDate'].get('value')
  jawbone_handler = JawboneHandler(user_access_token, user_request_date, user_session_new)
  alexa_response = jawbone_handler.process_intent(user_intent)
  if not alexa_response:
    return jawbone_error(event, context)
  else:
    return alexa_response


def jawbone_launch(event, context):
  speech_json = JSONResponseBuilder.build_json_response_speech('Jawbone. Everything is looking Up.')
  json_response = JSONResponseBuilder.build_json_response(speech_json, end_session=False)
  return JSONResponseBuilder.build_json(json_response)


def jawbone_ended(event, context):
  speech_json = JSONResponseBuilder.build_json_response_speech('Jawbone powering down.')
  json_response = JSONResponseBuilder.build_json_response(speech_json)
  return JSONResponseBuilder.build_json(json_response)


def jawbone_error(event, context):
  logging.error('There as an error processing this request. \nEvent: {} \nContext: {}'.format(event, context))
  speech_json = JSONResponseBuilder.build_json_response_speech('I was unable to process your request.')
  json_response = JSONResponseBuilder.build_json_response(speech_json)
  return JSONResponseBuilder.build_json(json_response)

