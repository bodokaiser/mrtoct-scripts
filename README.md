# MRtoCT

Preprocessing script for MRI to CT synthesis.

1. Downloads and unpacks `CT` and `MR_T1` [RIRE][RIRE] data
2. Coregisters `MR_T1` with `CT` and saves them as `NIfTI-1`

## Usage

Install the requirements

    pip install -r requirements.txt

and execute `python main.py`.

[RIRE]: http://www.insight-journal.org/rire
