import os
import shutil


def main():
  if os.path.exists('cache.json'):
    os.remove('cache.json')

  for fname in os.listdir():
    if fname.startswith('__') or fname.startswith('.'):
      continue

    if os.path.isdir(fname):
      shutil.rmtree(fname)


if __name__ == '__main__':
  main()
