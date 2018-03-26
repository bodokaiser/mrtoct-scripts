import os
import argparse
import SimpleITK as sitk


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


def coregister(rootdir, fixed_modality, moving_modality):
  rmethod = sitk.ImageRegistrationMethod()
  rmethod.SetMetricAsMattesMutualInformation(numberOfHistogramBins=100)
  rmethod.SetMetricSamplingStrategy(rmethod.RANDOM)
  rmethod.SetMetricSamplingPercentage(.01)
  rmethod.SetInterpolator(sitk.sitkLinear)
  rmethod.SetOptimizerAsGradientDescent(learningRate=1.0,
                                        numberOfIterations=200,
                                        convergenceMinimumValue=1e-6,
                                        convergenceWindowSize=10)
  rmethod.SetOptimizerScalesFromPhysicalShift()
  rmethod.SetShrinkFactorsPerLevel(shrinkFactors=[4, 2, 1])
  rmethod.SetSmoothingSigmasPerLevel(smoothingSigmas=[2, 1, 0])
  rmethod.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

  filetree = _parse(rootdir)

  for subject, modalities in filetree.items():
    print(f'{subject}:')

    if fixed_modality not in modalities or moving_modality not in modalities:
      print('-> incomplete')
      continue

    fixed_path = os.path.join(rootdir, modalities[fixed_modality])
    moving_path = os.path.join(rootdir, modalities[moving_modality])

    fixed_image = sitk.ReadImage(fixed_path, sitk.sitkFloat32)
    moving_image = sitk.ReadImage(moving_path, sitk.sitkFloat32)

    initial_transform = sitk.CenteredTransformInitializer(
        fixed_image, moving_image, sitk.Euler3DTransform(),
        sitk.CenteredTransformInitializerFilter.GEOMETRY)
    rmethod.SetInitialTransform(initial_transform, inPlace=False)
    final_transform = rmethod.Execute(fixed_image, moving_image)
    print('-> coregistered')

    moving_image = sitk.Resample(
        moving_image, fixed_image, final_transform, sitk.sitkLinear, .0,
        moving_image.GetPixelID())
    moving_image = sitk.Cast(moving_image, sitk.sitkInt16)
    print('-> resampled')

    sitk.WriteImage(moving_image, moving_path)
    print('-> exported')


def main(args):
  coregister(args.rootdir, args.fixed, args.moving)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('rootdir')
  parser.add_argument('--fixed', default='ct')
  parser.add_argument('--moving', default='t1')

  main(parser.parse_args())
