from datetime import datetime, timedelta
from os.path import basename
import json
import os
import requests
import smart_open

URL_TMPL = "https://ztf.uw.edu/alerts/public/ztf_public_%s.tar"

S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', None)
S3_PREFIX = os.environ.get('S3_PREFIX', 'Alerts')

def get_url(event):
    url = None
    if bool(event.get('body', None)):
        body = json.loads(event['body'])
        if 'url' in body:
            url = body['url']
            print ("Override default url with %s" % url)
        elif 'date' in body:
            url = URL_TMPL % body['date']
            print ("Override default date with %s" % url)
    if not bool(url):
        url = URL_TMPL % (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        print ("Using default url %s" % url)
    return url

def download_alerts(url: str):
  s3_filename = 's3://%s/%s/%s' % (S3_BUCKET_NAME, S3_PREFIX, basename(url))
  try:
    print ('Downloading %s to %s ...' % (url, s3_filename))
    r = requests.get(url, allow_redirects=True, stream=True)
    with smart_open.open(s3_filename, 'wb') as fout:
      for ch in r:
        fout.write(ch)
    print ('Successfully downloaded %s ...' % url)
  except requests.RequestException as e:
    print(e)
    raise e
  return s3_filename

def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    s3_filename = download_alerts(get_url(event))
    return {
        "statusCode": 200,
        "body": json.dumps({
            "s3_filename": s3_filename
        })
    }
