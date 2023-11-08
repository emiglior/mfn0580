# script to read an ascii file and perform a fit with a sin function
# run the script with the command:
# usage: python NyquistFit.py --help
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
parser.add_option("-s", "--freq_sampling",
                      action="store", type="float", dest="freq_sampling", default=200.,
                      help="sampling frequency [Hz]")
parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="verbose print-out")

(options, args) = parser.parse_args()

times = array.array('d')
codes = array.array('d')

# input ASCII file (from Arduino DAQ)
topdir = '/Users/migliore/Documents/didattica/2022/Laboratorio Elettronica/mfn0580/ElettronicaDigitale'
times, codes = AH.read_file(os.path.join(topdir,options.input_filename))

err_times_null = array.array('d', [0.0]*len(times))
err_times = array.array('d', [0.0001]*len(times)) # 0.1 ms
err_codes = array.array('d', [0.5]*len(times))    # 0.5 ADC counts

if options.verbose:
    print( 'MIN/MAX code {0:3.0f} {1:3.0f} MIN/MAX time {2:10.6f} {3:10.6f}'.format( min(codes), max(codes), min(times), max(times)) )

# book TGraphErrors
gr_null = ROOT.TGraphErrors(len(times), times, codes, err_times_null, err_codes)
gr      = ROOT.TGraphErrors(len(times), times, codes, err_times,      err_codes)

# init parameters
p0 = 0.5 * (max(codes)-min(codes)) # amplitude
p3 = 0.5 * (max(codes)+min(codes)) # offset

# step #1: scan frequency parameter
freq_min =    0. # [Hz]
freq_max =  0.5*options.freq_sampling # [Hz]
freq_bins =   4
freq_list = numpy.linspace( freq_min, freq_max, 1+freq_bins*int(freq_max-freq_min) )
chi2_min = float('inf')

# define TF1 for the fit
tf1_sin = ROOT.TF1( 'tf1_sin', '[0]*TMath::Sin(TMath::TwoPi()*[1]*x+[2])+[3]', min(times),  max(times) )
tf1_sin.SetNpx( 10*len(times) )

# when scanning for best frequency, use null errors on times to avoid funny chi2 computations
for freq in freq_list:
      tf1_sin.SetParameters(p0, freq, 0., p3) # amplitude [counts], frequency [Hz], phase, offset [counts]
      gr_null.Fit('tf1_sin','RQ')

      if tf1_sin.GetChisquare() < chi2_min:
            chi2_min = tf1_sin.GetChisquare()
            freq_chi2min = freq
            if options.verbose:
                print( '{0:7.3f} {1:8.4f}'.format(freq, tf1_sin.GetChisquare()) )

print( 'best freq {0:7.3f} [Hz] chi2 {1:8.4f}'.format(freq_chi2min, chi2_min) )

# step #2: perform final fit with proper errors on times and codes
can = ROOT.TCanvas('can', 'can', 800, 400)
tf1_sin.SetParameters(p0, freq_chi2min, 0., p3)
gr.Fit('tf1_sin','RM+')
print( 'Final fit Chi2/NDF {0:7.3f} / {1:7.3f}'.format( tf1_sin.GetChisquare(), tf1_sin.GetNDF()) )
gr.SetMarkerStyle(ROOT.kFullDotMedium)
gr.Draw('AP')
can.SaveAs('/tmp/can.root')
