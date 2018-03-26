import os
import io
import json
import scrapy
import requests
import tarfile
import tempfile
import argparse
import SimpleITK as sitk

from scrapy.crawler import CrawlerProcess


def _subjectstr(subject):
  prefix, number = subject.split('_')[:2]

  return prefix[0] + number


def _modalitystr(modality):
  return modality.split('_')[-1].lower()


class RIRE(scrapy.Spider):

  name = 'RIRE'

  start_urls = [
      'http://www.insight-journal.org/rire/download_data.php',
      'http://www.insight-journal.org/rire/download_training_data.php',
  ]

  def parse(self, resp):
    for trows in resp.css('table tr'):
      links = trows.css('td a')

      if len(links) < 1:
        continue

      name = links.pop(0).css('::text').extract_first()

      files = {}
      for l in links:
        label = l.css('::text').extract_first().split('.tar.gz')
        value = l.css('::attr(href)').extract_first()

        if len(label) > 0:
          files[label[0]] = f'{resp.url}/../{value}'

      yield {name: files}


def download(rootdir, modalities):
  answer = input('Did you read and accept the RIRE licence aggreement? (y/n)')

  if answer != 'y':
    exit()

  if not os.path.exists(rootdir):
    os.makedirs(rootdir)

    print(f'created {rootdir}')

  tempdir = tempfile.gettempdir()
  jsonfile = os.path.join(tempdir, 'cache.json')

  if not os.path.exists(jsonfile):
    process = CrawlerProcess({
        'LOG_LEVEL': 'ERROR',
        'FEED_FORMAT': 'json',
        'FEED_URI': jsonfile,
    })
    process.crawl(RIRE)
    process.start()

    print(f'crawled data\n')

  with open(jsonfile) as f:
    data = json.loads(f.read())

  for d in data:
    for subject, archives in d.items():
      subjectdir = os.path.join(tempdir, subject)

      if not os.path.exists(subjectdir):
        os.makedirs(subjectdir)
      print(f'{subject}:')

      for modality in archives:
        modalitydir = os.path.join(subjectdir, modality)

        if modality not in modalities:
          continue

        if not os.path.exists(modalitydir):
          response = requests.get(archives[modality])
          print(f'-> downloaded {modality}')

          archive = tarfile.open(fileobj=io.BytesIO(response.content))
          archive.extractall(subjectdir)
          print(f'-> extracted {modality}')

        imagepath = os.path.join(modalitydir, 'image.bin')
        if not os.path.exists(imagepath):
          os.system(f'gunzip {imagepath}.Z')
          print(f'-> unzipped {modality}')

        source_path = os.path.join(modalitydir, f'{subject}_{modality}.mhd')
        target_path = os.path.join(
            rootdir, f'{_subjectstr(subject)}_{_modalitystr(modality)}.nii')

        if not os.path.exists(target_path):
          sitk.WriteImage(sitk.ReadImage(source_path), target_path)
          print(f'-> converted {modality}')


def main(args):
  download(args.rootdir, args.modalities)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('rootdir')
  parser.add_argument('--modalities', default=['ct', 'mr_T1', 'mr_T2'])

  main(parser.parse_args())
