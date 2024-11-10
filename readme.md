# CreditCard Statement Tool

Parse PDF e-statements from banks, convert into `pandas` dataframe

Currently supporting only `.xls` from UOB Singapore.

## Quickstart

1. Clone: `git clone git@github.com:jakelime/cc-calculator.git`
1. Install python dependencies `pip install -r requirements.txt`
1. Download `CreditCard Statements` using Chrome/Edge/Safar
1. i.e. `CC_TXN_History_07082023064628.xls` will be stored in `~/Downloads`
1. Run `python ccc/main.py`

## To do

1. Parse PDF statements
1. Support more banks
