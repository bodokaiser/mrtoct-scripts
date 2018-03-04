import os
import argparse
import SimpleITK as sitk


def coregister(workdir, fixed, moving, resampled):
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

    if fixed not in modalities or moving not in modalities:
      print('-> incomplete')
      continue

    fpath = os.path.join(workdir, modalities[fixed])
    mpath = os.path.join(workdir, modalities[moving])
    rpath = os.path.join(workdir, f'{patient}_{resampled}.nii')

    fimage = sitk.ReadImage(fpath, sitk.sitkFloat32)
    mimage = sitk.ReadImage(mpath, sitk.sitkFloat32)

    if os.path.exists(rpath):
      print('-> complete')
      continue

    initial_transform = sitk.CenteredTransformInitializer(
        fimage, mimage, sitk.Euler3DTransform(),
        sitk.CenteredTransformInitializerFilter.GEOMETRY)
    rmethod.SetInitialTransform(initial_transform, inPlace=False)
    final_transform = rmethod.Execute(fimage, mimage)
    print('-> coregistered')

    mresampled = sitk.Resample(
        mimage, fimage, final_transform, sitk.sitkLinear, .0,
        mimage.GetPixelID())
    print('-> resampled')

    sitk.WriteImage(mresampled, rpath)
    print('-> exported')


def main(args):
  coregister(args.workdir, args.fixed, args.moving, args.resampled)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('workdir')
  parser.add_argument('--fixed', default='ct')
  parser.add_argument('--moving', default='mr_T1')
  parser.add_argument('--resampled', default='mr_co')

  main(parser.parse_args())
