# script to read an ascii file and perform a DNL-analysis of the acquired data
# run the script with the command:
# usage: python DNLramp.py --help
import ROOT
import array
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

root_output_file = ROOT.TFile('/tmp/DNL.root','RECREATE')

h_dnl_codes = ROOT.TH1I("codes", "", 16, -0.5, 15.5)
h_dnl_bits  = ROOT.TH1I("bits",  "",  4, -0.5,  3.5)

for code in codes:
    h_dnl_codes.Fill(code)
    if code != 0 and code != 15:
        bits = [int(x) for x in list('{0:04b}'.format(int(code)))] # from int to list of bits [MSB,...,LSB] with 0-padding
        for index, value in enumerate(bits[::-1]): # re-order from LSB to MSB
            if value !=0:
                h_dnl_bits.Fill(index)

h_dnl_codes.SetStats(ROOT.kFALSE)
h_dnl_codes.GetXaxis().SetTitle('code')
h_dnl_codes.GetYaxis().SetTitle('frequenze assolute')
h_dnl_codes.GetYaxis().SetRangeUser(0, h_dnl_codes.GetMaximum()*1.2)

h_dnl_bits.SetStats(ROOT.kFALSE)
h_dnl_bits.GetXaxis().SetTitle('bit')
h_dnl_bits.GetYaxis().SetTitle('frequenze assolute')
h_dnl_bits.GetYaxis().SetRangeUser(0, h_dnl_bits.GetMaximum()*1.2)

root_output_file.Write()
root_output_file.Close()
