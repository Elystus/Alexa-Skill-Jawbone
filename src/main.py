from alexa.request import AlexaRequestFactory

def jawbone_entry(event, context):
  request_type = event['request'].get('type')
  request_handler = AlexaRequestFactory(request_type, event, context)
  return request_handler.process()


