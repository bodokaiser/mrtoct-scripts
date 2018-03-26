import os
import argparse
import numpy as np
import nibabel as nib

from scipy import ndimage
from skimage import filters


def _parse(rootdir):
  filenames = [f for f in os.listdir(rootdir) if f.endswith('.nii')]
  filenames.sort()
  filetree = {}

  for filename in filenames:
    subject, modality = filename.split('.').pop(0).split('_')[:2]

    if subject not in filetree:
      filetree[subject] = {}
    filetree[subject][modality] = filename

  return filetree


def clean(rootdir, source_modality, target_modality):
  filetree = _parse(rootdir)

  for subject, modalities in filetree.items():
    print(f'{subject}:')

    if source_modality not in modalities or target_modality not in modalities:
      print('-> incomplete')
      continue

    source_path = os.path.join(rootdir, modalities[source_modality])
    target_path = os.path.join(rootdir, modalities[target_modality])

    source_image = nib.load(source_path)
    target_image = nib.load(target_path)

    source_volume = source_image.get_data()
    target_volume = target_image.get_data()
    binary_volume = np.zeros_like(source_volume)

    for i in range(binary_volume.shape[-1]):
      source_slice = source_volume[:, :, i]

      if source_slice.min() == source_slice.max():
        binary_volume[:, :, i] = np.zeros_like(source_slice)
      else:
        threshold = filters.threshold_li(source_slice)

        binary_volume[:, :, i] = ndimage.morphology.binary_fill_holes(
            source_slice > threshold)

    source_volume = np.where(binary_volume, source_volume, np.ones_like(
        source_volume) * source_volume.min())
    target_volume = np.where(binary_volume, target_volume, np.ones_like(
        target_volume) * target_volume.min())

    source_image = nib.Nifti2Image(
        source_volume, source_image.affine, source_image.header)
    target_image = nib.Nifti2Image(
        target_volume, target_image.affine, target_image.header)

    nib.save(source_image, source_path)
    print(f'-> denoised {source_modality}')

    nib.save(target_image, target_path)
    print(f'-> denoised {target_modality}')


def main(args):
  clean(args.rootdir, args.source, args.target)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('rootdir')
  parser.add_argument('--source', default='t1')
  parser.add_argument('--target', default='ct')

  main(parser.parse_args())
