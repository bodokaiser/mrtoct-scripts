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


def download(workdir):
  answer = input('Did you read and accept the RIRE licence aggreement? (y/n)')

  if answer != 'y':
    exit()

  if not os.path.exists(workdir):
    os.makedirs(workdir)

    print(f'created {workdir}')

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

    print(f'crawled data')

  with open(jsonfile) as f:
    data = json.loads(f.read())

  for d in data:
    for patient, modalities in d.items():
      pdir = os.path.join(tempdir, patient)

      if not os.path.exists(pdir):
        os.makedirs(pdir)
      print(f'{patient}:')

      for modality in ['ct', 'mr_T1']:
        mdir = os.path.join(pdir, modality)

        if modality not in modalities:
          continue

        if not os.path.exists(mdir):
          response = requests.get(modalities[modality])
          print(f'-> downloaded {modality} archive')

          archive = tarfile.open(fileobj=io.BytesIO(response.content))
          archive.extractall(pdir)
          print(f'-> extracted {modality} archive')

        bin_path = os.path.join(mdir, 'image.bin')
        if not os.path.exists(bin_path):
          os.system(f'gunzip {bin_path}.Z')
          print(f'-> uncompressed {modality} volume')

        source_path = os.path.join(mdir, f'{patient}_{modality}.mhd')
        target_path = os.path.join(workdir, f'{patient}_{modality}.nii')
        if not os.path.exists(target_path):
          sitk.WriteImage(sitk.ReadImage(source_path), target_path)
          print(f'-> converted {modality} mhd to nii')


def main(args):
  download(args.workdir)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('workdir')

  main(parser.parse_args())
