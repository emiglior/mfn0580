# script to read an ascii file and perform a time-analysis of the acquired data
# run the script with the command:
# usage: python TimeInfo.py --help
import ROOT
import array
import numpy
import math
import os

import ascii_helpers as AH

from optparse import OptionParser

parser = OptionParser()
parser.add_option("-f", "--file",
                     action="store", type="string", dest="input_filename", default='DATA1.txt',
                     help="input data file")
parser.add_option("-v", "--verbose",
                     action="store_true", dest="verbose", default=False,
                     help="verbose print-out")

(options, args) = parser.parse_args()

times = array.array('d')
codes = array.array('d')

# input ASCII file (from Arduino DAQ)
topdir = '/Users/migliore/Documents/didattica/2022/Laboratorio Elettronica/mfn0580/ElettronicaDigitale'
times, codes = AH.read_file(os.path.join(topdir,options.input_filename))

root_output_file = ROOT.TFile('/tmp/TimeInfo.root','RECREATE')

# estimated sampling period of this data taking from the timestamp of the first 20 measurements skipping the first
n = max(20, len(times))
time_sampling = (times[n-1]-times[1])/(n-2.)
print(1./time_sampling, 'Hz', time_sampling, 's')

h1_dTime_coarse = ROOT.TH1F('h1_dTime_coarse', 'h1_dTime_coarse', 1500, 0., 15.5*time_sampling)
h1_dTime_fine   = ROOT.TH1F('h1_dTime_fine',   'h1_dTime_fine',   27, time_sampling-(0.065e-3), time_sampling+(0.065e-3))
h1_dTime_gap    = ROOT.TH1F('h1_dTime_gap',    'h1_dTime_gap', 1000, 0., 5.)
t_last = times[0]
for t2, t1 in zip(times[1:], times):
    # dT between consecutive records
    h1_dTime_coarse.Fill(t2-t1)
    h1_dTime_fine.Fill(t2-t1)
    # if dT != time_sampling, fill the time elapsed from the previous mis-reading
    if t2-t1 > 1.5 * time_sampling:
        h1_dTime_gap.Fill(t2-t_last)
        t_last = t2
h1_dTime_coarse.GetXaxis().SetTitle('[s]')
h1_dTime_fine.GetXaxis().SetTitle('[s]')
h1_dTime_gap.GetXaxis().SetTitle('[s]')

root_output_file.Write()
root_output_file.Close()
