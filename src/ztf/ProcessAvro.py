from urllib.parse import unquote_plus
import boto3
import os

S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', None)

s3_client = boto3.client('s3')


def lambda_hanlder(event, context):
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
    print ("Procesing AVRO file s3://%s/%s" % (bucket, key))
  return {
      "statusCode": 200,
  }
