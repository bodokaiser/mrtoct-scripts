import os
import io
import json
import scrapy
import requests
import tarfile

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
        key = l.css('::text').extract_first()
        value = l.css('::attr(href)').extract_first()

        files[key] = f'{resp.url}/../{value}'

      yield {name: files}


ARCHIVES = ['ct.tar.gz', 'mr_T1.tar.gz']


def main():
  answer = input('Did you read and accept the RIRE licence aggreement? (y/n)')

  if answer != 'y':
    exit()

  jsonfile = 'cache.json'

  if not os.path.exists(jsonfile):
    process = CrawlerProcess({
        'FEED_FORMAT': 'json',
        'FEED_URI': jsonfile,
    })
    process.crawl(RIRE)
    process.start()

  with open(jsonfile) as f:
    data = json.loads(f.read())

  for d in data:
    for pname, links in d.items():
      if not os.path.exists(pname):
        os.makedirs(pname)

      for aname in ARCHIVES:
        dirname = os.path.join(pname, aname.split('.')[0])

        if not os.path.exists(dirname) and aname in links:
          response = requests.get(links[aname], stream=True)
          archive = tarfile.open(fileobj=io.BytesIO(response.content))
          archive.extractall(pname)


if __name__ == '__main__':
  main()
