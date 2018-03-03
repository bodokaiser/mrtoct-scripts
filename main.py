import os
import io
import json
import scrapy
import requests
import tarfile
import tempfile
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
        key = l.css('::text').extract_first()
        value = l.css('::attr(href)').extract_first()

        files[key] = f'{resp.url}/../{value}'

      yield {name: files}


def main():
  answer = input('Did you read and accept the RIRE licence aggreement? (y/n)')

  if answer != 'y':
    exit()

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

  with open(jsonfile) as f:
    data = json.loads(f.read())

  for d in data:
    for pname, links in d.items():
      pdir = os.path.join(tempdir, pname)

      if not os.path.exists(pdir):
        os.makedirs(pdir)

      for aname in ['ct.tar.gz', 'mr_T1.tar.gz']:
        adir = os.path.join(pdir, aname.split('.')[0])

        if not os.path.exists(adir) and aname in links:
          response = requests.get(links[aname])

          archive = tarfile.open(fileobj=io.BytesIO(response.content))
          archive.extractall(pdir)

          print(f'extracted {pname}/{aname}')

        iname = os.path.join(adir, 'image.bin')
        if not os.path.exists(iname):
          os.system(f'gunzip {iname}.Z')

          print(f'uncompressed {pname}/{aname}')

  rmethod = sitk.ImageRegistrationMethod()
  rmethod.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
  rmethod.SetMetricSamplingStrategy(rmethod.RANDOM)
  rmethod.SetMetricSamplingPercentage(0.01)
  rmethod.SetInterpolator(sitk.sitkLinear)
  rmethod.SetOptimizerAsGradientDescent(learningRate=1.0,
                                        numberOfIterations=100,
                                        convergenceMinimumValue=1e-6,
                                        convergenceWindowSize=10)
  rmethod.SetOptimizerScalesFromPhysicalShift()
  rmethod.SetShrinkFactorsPerLevel(shrinkFactors=[4, 2, 1])
  rmethod.SetSmoothingSigmasPerLevel(smoothingSigmas=[2, 1, 0])
  rmethod.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

  for d in data:
    for pname in d.keys():
      pdir = os.path.join(tempdir, pname)

      fimage_path = os.path.join(pdir, f'ct/{pname}_ct.mhd')
      mimage_path = os.path.join(pdir, f'mr_T1/{pname}_mr_T1.mhd')

      if not os.path.exists(fimage_path) or not os.path.exists(mimage_path):
        continue

      fimage = sitk.ReadImage(fimage_path, sitk.sitkFloat32)
      mimage = sitk.ReadImage(mimage_path, sitk.sitkFloat32)

      itransform = sitk.CenteredTransformInitializer(
          fimage, mimage, sitk.Euler3DTransform(),
          sitk.CenteredTransformInitializerFilter.GEOMETRY)

      rmethod.SetInitialTransform(itransform, inPlace=False)
      ftransform = rmethod.Execute(fimage, mimage)

      mresample = sitk.Resample(
          mimage, fimage, ftransform, sitk.sitkLinear, .0, mimage.GetPixelID())

      sitk.WriteImage(fimage, f'{pname}_ct.nii')
      sitk.WriteImage(mresample, f'{pname}_mr_T1.nii')

      print(f'registered {pname}')


if __name__ == '__main__':
  main()
