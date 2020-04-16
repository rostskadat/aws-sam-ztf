from astropy.io import fits
from astropy.time import Time
from avro.datafile import DataFileReader
from avro.io import DatumReader
from os.path import basename, join, dirname
from urllib.parse import unquote_plus
import boto3
import gzip
import io
import json
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd

S3_PREFIX = os.environ.get('S3_PREFIX', 'Plots')

s3_client = boto3.client('s3')


def plot_cutout(stamp, fig=None, subplot=None, **kwargs):
  import aplpy
  with gzip.open(io.BytesIO(stamp), 'rb') as f:
    with fits.open(io.BytesIO(f.read())) as hdul:
      if fig is None:
        fig = plt.figure(figsize=(4, 4))
      if subplot is None:
        subplot = (1, 1, 1)
      ffig = aplpy.FITSFigure(hdul[0], figure=fig, subplot=subplot, **kwargs)
      ffig.show_grayscale(stretch='arcsinh')
  return ffig


def plot_lightcurve(lightcurve_path, dflc, days_ago=True):
  filter_color = {1: 'green', 2: 'red', 3: 'pink'}
  if days_ago:
    now = Time.now().jd
    t = dflc.jd - now
    xlabel = 'Days Ago'
  else:
    t = dflc.jd
    xlabel = 'Time (JD)'

  plt.figure()
  for fid, color in filter_color.items():
    # plot detections in this filter:
    w = (dflc.fid == fid) & ~dflc.magpsf.isnull()
    if np.sum(w):
      plt.errorbar(t[w], dflc.loc[w, 'magpsf'],
                   dflc.loc[w, 'sigmapsf'], fmt='.', color=color)
    wnodet = (dflc.fid == fid) & dflc.magpsf.isnull()
    if np.sum(wnodet):
      plt.scatter(t[wnodet], dflc.loc[wnodet, 'diffmaglim'],
                  marker='v', color=color, alpha=0.25)

  plt.gca().invert_yaxis()
  plt.xlabel(xlabel)
  plt.ylabel('Magnitude')
  plt.savefig(lightcurve_path)

def plot_stamps(stamps_path, packet):
  fig = plt.figure(figsize=(12, 4))
  for i, cutout in enumerate(['Science', 'Template', 'Difference']):
    stamp = packet['cutout{}'.format(cutout)]['stampData']
    ffig = plot_cutout(stamp, fig=fig, subplot=(1, 3, i + 1))
    ffig.set_title(cutout)
  fig.savefig(stamps_path)

def make_dataframe(packet):
  df = pd.DataFrame(packet['candidate'], index=[0])
  df_prv = pd.DataFrame(packet['prv_candidates'])
  return pd.concat([df, df_prv], ignore_index=True)


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
    download_path = '/tmp/%s' % (basename(key))
    print ("Downloading s3://%s/%s ..." % (bucket, key))
    s3_client.download_file(bucket, key, download_path)

    with open(download_path, "rb") as f_avro:
      reader = DataFileReader(f_avro, DatumReader())
      #reader = reader = fastavro.reader(f_avro)
      for packet in reader:
        lightcurve_path = download_path.replace('.avro', '.lightcurve.png')
        plot_lightcurve(lightcurve_path, make_dataframe(packet))
        upload_key = '%s/%s' % (S3_PREFIX, basename(lightcurve_path))
        print("Uploading s3://%s/%s" % (bucket, upload_key))
        s3_client.upload_file(lightcurve_path, bucket, upload_key)

        #stamps_path = download_path.replace('.avro', '.stamps.png')
        #plot_stamps(stamps_path, packet)
        #upload_key = '%s/%s' % (S3_PREFIX, basename(stamps_path))
        #print("Uploading s3://%s/%s" % (bucket, upload_key))
        #s3_client.upload_file(stamps_path, bucket, upload_key)
      reader.close()

  return {
      "statusCode": 200,
  }


if __name__ == "__main__":
  with open(join(dirname(__file__), '../../events/ProcessAvro.json'), "r") as f:
    event = json.load(f)
  lambda_handler(event, "")
