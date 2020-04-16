from urllib.parse import unquote_plus
import boto3
import gzip
import json
import os
import shutil
import tarfile
import uuid

S3_PREFIX = os.environ.get('S3_PREFIX', 'Avro')

s3_client = boto3.client('s3')


def expand_archive(download_path: str, output_dir):
  if not os.path.isdir(output_dir):
    os.makedirs(output_dir)
  if download_path.endswith("tar.gz"):
    gunzip_file = download_path.replace(".tar.gz", ".tar")
    with gzip.open(download_path, 'rb') as f_in:
      with open(gunzip_file, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
        os.fsync(f_out)
    tar_file = gunzip_file
  elif download_path.endswith("tar"):
    tar_file = download_path
  else:
    raise ValueError('Unknown archive format: %' % download_path)
  with tarfile.open(tar_file, "r") as f_tar:
    f_tar.extractall(path=output_dir)

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
    download_path = '/tmp/%s-%s' % (uuid.uuid4(), os.path.basename(key))
    
    print ("Downloading s3://%s/%s ..." % (bucket, key))
    s3_client.download_file(bucket, key, download_path)
    print ("Expanding %s ..." % download_path)
    output_dir = '/tmp/expanded-%s' % os.path.basename(download_path)
    expand_archive(download_path, output_dir)
    avrofiles = []
    for (_, _, filenames) in os.walk(output_dir):
      avrofiles.extend(filenames)
    for avro in avrofiles:
      upload_key = '%s/%s' % (S3_PREFIX, os.path.basename(avro))
      print ("Uploading %s ..." % avro)
      s3_client.upload_file(os.path.join(output_dir, avro), bucket, upload_key)
  return {
      "statusCode": 200,
      "body": json.dumps({
        "upload_prefix": S3_PREFIX
        })
  }
