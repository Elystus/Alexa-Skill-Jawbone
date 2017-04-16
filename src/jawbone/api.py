import requests
import logging
import time
import json

class APIRequest(object):

  api_url = 'https://jawbone.com/nudge/api/v.1.1'
  api_uri_list = {
    'heartrate': '/users/@me/heartrates?date={}',
    'sleeps': '/users/@me/sleeps?date={}',
    'goals': '/users/@me/goals?date={}'
  }

  def __init__(self, access_token, request_date):
    self.request_date = self.setup_request_date(request_date)
    self.access_token = access_token
    self.current_url = None

  def set_endpoint(self, uri_name):
    if uri_name in self.api_uri_list.keys():
      self.current_url = '{}{}'.format(self.api_url, self.api_uri_list.get(uri_name).format(self.request_date))
      return True
    else:
      self.current_url = None
      return False

  def setup_request_date(self, user_request_date):
    if user_request_date:
      request_date = user_request_date.replace("-", "")
    else:
      request_date = time.strftime("%Y%m%d")
    logging.error("Error: {}".format(request_date))
    return request_date

  def fetch_data(self):
    data = {}
    try:
      http_headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer {}'.format(self.access_token)
      }
      response = requests.get(self.current_url, headers=http_headers)
      print self.current_url
      print self.access_token
      print response.content
      print response.status_code
      if response.status_code == requests.codes.ok:
        data = json.loads(response.content)
    except Exception as e:
      logging.error('Unable to correctly poll data from Jawbone API. URL: {} Error: {}'.format(self.current_url, e))
    return data
