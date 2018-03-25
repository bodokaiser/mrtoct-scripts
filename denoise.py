import os
import argparse
import numpy as np
import nibabel as nb

from scipy import ndimage
from skimage import filters


def denoise(workdir, source, target, postfix):
  filenames = [f for f in os.listdir(workdir) if f.endswith('.nii')]
  filenames.sort()

  data = {}

  for fname in filenames:
    sparts = fname.split('.').pop(0).split('_')
    patient = '_'.join(sparts[:2])
    modality = '_'.join(sparts[2:])

    if patient not in data:
      data[patient] = {}

    data[patient][modality] = fname

  for patient, modalities in data.items():
    print(f'{patient}:')

    if source not in modalities or target not in modalities:
      print('-> incomplete')
      continue

    s = nb.load(os.path.join(workdir, modalities[source]))
    t = nb.load(os.path.join(workdir, modalities[target]))

    x = s.get_data()
    y = t.get_data()

    m = np.zeros_like(x)

    for i in range(x.shape[-1]):
      slice = x[:, :, i]

      if slice.min() == slice.max():
        m[:, :, i] = np.ones_like(slice) * slice.min()
      else:
        threshold = filters.threshold_li(slice)

        m[:, :, i] = ndimage.morphology.binary_fill_holes(slice > threshold)

    x = np.where(m, x, np.ones_like(x) * x.min())
    y = np.where(m, y, np.ones_like(y) * y.min())

    s = nb.Nifti2Image(x, s.affine, s.header)
    t = nb.Nifti2Image(y, t.affine, t.header)

    nb.save(s, os.path.join(workdir, f'{patient}_{source}_{postfix}.nii'))
    print(f'-> denoised {source}')

    nb.save(t, os.path.join(workdir, f'{patient}_{target}_{postfix}.nii'))
    print(f'-> denoised {target}')


def main(args):
  denoise(args.workdir, args.source, args.target, args.postfix)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('workdir')
  parser.add_argument('--source', default='mr_co')
  parser.add_argument('--target', default='ct')
  parser.add_argument('--postfix', default='dn')

  main(parser.parse_args())
