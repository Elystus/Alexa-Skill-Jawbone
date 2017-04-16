

class AlexaResponse(object):

  @classmethod
  def build_response(cls, message, end_session=True):
    response_speech = cls.build_json_response_speech(message)
    response_json = cls.build_json_response(response_speech, end_session=end_session)
    return cls.build_json(response_json)

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
