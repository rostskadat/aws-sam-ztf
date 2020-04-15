from urllib.parse import unquote_plus
import boto3
import json
import os
import shutil
import uuid

S3_PREFIX = os.environ.get('S3_PREFIX', 'Avro')

s3_client = boto3.client('s3')


def expand_archive(bucket: str, key: str):
  download_path = '/tmp/%s-%s' % (uuid.uuid4(), os.path.basename(key))
  expanded_path = '/tmp/expanded-%s' % os.path.basename(download_path)
  s3_client.download_file(bucket, key, download_path)
  if not os.path.isdir(expanded_path):
    os.makedirs(expanded_path)
  shutil.unpack_archive(download_path, expanded_path)
  return expanded_path


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
  for record in event['Records']:
    bucket = record['s3']['bucket']['name']
    key = unquote_plus(record['s3']['object']['key'])
    expanded_path = expand_archive(bucket, key)
    for f in expanded_path:
      upload_key = '%s/%s' % (S3_PREFIX, os.path.basename(f))
      s3_client.upload_file(f, bucket, upload_key)
  return {
      "statusCode": 200,
      "body": json.dumps({
        "upload_key": upload_key
        })
  }
