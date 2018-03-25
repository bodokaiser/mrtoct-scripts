# MRtoCT

Preprocessing script for MRI to CT synthesis [RIRE][RIRE] dataset.

## Usage

Install the requirements

    pip install -r requirements.txt

and execute `python download.py <workdir>`.

To coregister use `python coregister.py <workdir>`. To remove background
noise use `python denoise.py <workdir>`.

[RIRE]: http://www.insight-journal.org/rire
