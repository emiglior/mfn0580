#!/usr/bin/env python
# version for python 3.9

import csv
import io  # needed from UTF encoding
import os  # needed for path

import ROOT
import array
import math

from optparse import OptionParser

INPUT_CSVFILE = 'Gruppo6_OpAmp_I2.csv'

def fcn_lowpass_gain(xx, par):
    # par[0]: GainMB
    # par[1]: f3dB   [Hz]
    return par[0]/math.sqrt( 1. + (xx[0]/par[1])**2 )

def fcn_broken_linear(xx, par):
    # par[0]: GainMB [dB]
    # par[1]: f3dB   [Hz]
    # par[2]: slope
    if xx[0] < par[1]:
        return par[0]
    else:
        return -par[2]*(xx[0]-par[1])+par[0]

def main():
    """ add a comment """

    desc   = """ This is a description of %prog."""
    parser = OptionParser(description=desc,version='%prog version 0.1')
    parser.add_option('--logX', help='logX', dest='logX',  action='store_true', default=False)
    (opts, args) = parser.parse_args()

    freq_array        = array.array('d',[])
    err_freq_array    = array.array('d',[])
    freq_log10_array  = array.array('d',[])

    gain_array        = array.array('d',[])
    err_gain_array    = array.array('d',[])

    gain_dB_array     = array.array('d',[])
    err_gain_dB_array = array.array('d',[])

    # gain_fixed_array = array.array('d',[])
    # err_gain_fixed_array = array.array('d',[])

    with io.open(os.path.join('/Users/migliore/Documents/didattica/2022/Laboratorio Elettronica', INPUT_CSVFILE), encoding='utf-8-sig', errors='ignore') as csvfile_data:
        reader = csv.DictReader(csvfile_data, delimiter=';')
        for row in reader:
            if int(row['status']) == 1:
                # frequency
                freq_array.append( float( row['f [Hz]'].replace(",", ".") ) )
                freq_log10_array.append( math.log10(freq_array[-1]) )
                err_freq_array.append(0.)
                # Vin, Vout and uncertainties
                vin_tmp = float( row['Vs [V]'].replace(",", ".") )
                err_vin_tmp = float( row['sVs [V]'].replace(",", ".") )
                vout_tmp = float( row['Vout [V]'].replace(",", ".") )
                err_vout_tmp = float( row['sVout [V]'].replace(",", ".") )
                # conpute gain and uncertainty
                gain_tmp = vout_tmp/vin_tmp
                err_gain_tmp = gain_tmp * math.sqrt( (err_vout_tmp/vout_tmp)**2  + (err_vin_tmp/vin_tmp)**2 )
                gain_array.append(gain_tmp)
                err_gain_array.append(err_gain_tmp)

                gain_dB_array.append( 20.*math.log10(gain_array[-1])  )# convert to dB
                err_gain_dB_array.append( err_gain_array[-1]*20./(math.log(10.)*gain_array[-1]) )# der [20*log10(x)] = 20/(x*log(10))

    ### GAIN LINEAR SCALE

    # Fill and fit TGraphErrors
    tge_lin = ROOT.TGraphErrors(len(freq_array), freq_array, gain_array, err_freq_array, err_gain_array)
    tge_lin.SetMarkerStyle(ROOT.kOpenTriangleUp)
    tge_lin.SetMarkerSize(0.6)
    fit_lowpass = ROOT.TF1('fit_lowpass', fcn_lowpass_gain, 1.0, 1e7, 2)
    fit_lowpass.SetNpx(10000)
    fit_lowpass.SetParameters(gain_array[0], 100e3)
    fit_lowpass.SetLineColor(ROOT.kRed)
    fit_lowpass.SetParName(0,'A_{MB}')
    fit_lowpass.SetParName(1,'f_{3dB}')
    tge_lin.Fit('fit_lowpass', 'R') # first argument is the name of the TF1 (e.g. char) not of the variable

    print('>>> GBP: ', fit_lowpass.GetParameter(0) * fit_lowpass.GetParameter(1) )

    # Compute residuals from best fit
    fit_array = array.array('d',map(fit_lowpass.Eval, freq_array))
    residuals_array =  array.array('d', map(lambda x, y, z: (x - y)/z, gain_array, fit_array, err_gain_array))
    tg_lin = ROOT.TGraph(len(freq_array), freq_array, residuals_array)
    tg_lin.SetMarkerStyle(ROOT.kOpenTriangleUp)
    tg_lin.SetMarkerSize(0.6)

    #
    ROOT.gStyle.SetOptFit(1)
    ROOT.gStyle.SetFitFormat('4.3g')

    # draw data+fit and residuals (based on https://root.cern/doc/master/ratioplotOld_8C.html)
    c1_lin = ROOT.TCanvas('c1_lin','c1_lin',600,800)

    # Upper plot will be in pad1_lin
    pad1_lin = ROOT.TPad('pad1_lin', 'pad1_lin', 0, 0.3, 1, 1.0)
    pad1_lin.SetBottomMargin(0) # Upper and lower plot are joined
    pad1_lin.Draw()             # Draw the upper pad: pad1_lin
    pad1_lin.cd()               # pad1_lin becomes the current pad
    if opts.logX:
        pad1_lin.SetLogx()
    tge_lin.SetTitle(INPUT_CSVFILE)
    tge_lin.Draw('AP')          # Draw tge_lin
    tge_lin.GetHistogram().GetYaxis().SetLabelSize(0.03)
    tge_lin.GetHistogram().GetYaxis().SetTitle('gain')
    pad1_lin.Update()

    # Lower plot will be in pad2_lin
    c1_lin.cd()          # Go back to the main canvas before defining pad2_lin
    pad2_lin = ROOT.TPad('pad2_lin', 'pad2_lin', 0, 0.05, 1, 0.3)
    pad2_lin.SetTopMargin(0)
    pad2_lin.SetBottomMargin(0.2)
    pad2_lin.Draw()
    pad2_lin.cd()       # pad2_lin becomes the current pad   # Upper plot will be in pad1_lin
    if opts.logX:
        pad2_lin.SetLogx()
    pad2_lin.SetGridy() # horizontal grid

    tg_lin.SetTitle('')
    tg_lin.GetHistogram().SetMinimum(-3.)
    tg_lin.GetHistogram().SetMaximum(+3.)

    tg_lin.GetHistogram().GetXaxis().SetLabelSize(0.07)
    tg_lin.GetHistogram().GetXaxis().SetTitle('f [Hz]')
    tg_lin.GetHistogram().GetXaxis().SetTitleSize(0.07)

    tg_lin.GetHistogram().GetYaxis().SetLabelSize(0.07)
    tg_lin.GetHistogram().GetYaxis().SetTitle('(value-fit)/err')
    tg_lin.GetHistogram().GetYaxis().SetTitleSize(0.09)
    tg_lin.GetHistogram().GetYaxis().SetTitleOffset(0.5)
    tg_lin.Draw('AP')

    c1_lin.SaveAs('/tmp/c1_lin.root')

    ### GAIN LOG SCALE [dB]

    # Fill and fit TGraphErrors
    tge_log10 = ROOT.TGraphErrors(len(freq_log10_array), freq_log10_array, gain_dB_array, err_freq_array, err_gain_dB_array)
    tge_log10.SetMarkerStyle(ROOT.kOpenTriangleUp)
    tge_log10.SetMarkerSize(0.6)

    fit_broken_line = ROOT.TF1('fit_broken_line', fcn_broken_linear, 0.0, 7.0,  3)
    fit_broken_line.SetNpx(10000)
    fit_broken_line.SetParameters(gain_dB_array[0], 3.0, 20.0)
    fit_broken_line.SetLineColor(ROOT.kRed)
    fit_broken_line.SetParName(0,'A_{MB}')
    fit_broken_line.SetParName(1,'f_{3dB}')
    fit_broken_line.SetParName(2,'slope')
    tge_log10.Fit('fit_broken_line', 'R') # first argument is the name of the TF1 (e.g. char) not of the variable

    print('>>> GBP: ', math.pow(10., fit_broken_line.GetParameter(0)/20.) * math.pow(10., fit_broken_line.GetParameter(1)) )
    print('>>> AMB : ', math.pow(10., fit_broken_line.GetParameter(0)/20.) )
    print('>>> f3dB: ', math.pow(10., fit_broken_line.GetParameter(1)) )

    # Compute residuals from best fit
    fit_dB_array = array.array('d',map(fit_broken_line.Eval, freq_log10_array))
    residuals_dB_array =  array.array('d', map(lambda x, y, z: (x - y)/z, gain_dB_array, fit_dB_array, err_gain_dB_array))
    tg_log10 = ROOT.TGraph(len(freq_log10_array), freq_log10_array, residuals_dB_array)
    tg_log10.SetMarkerStyle(ROOT.kOpenTriangleUp)
    tg_log10.SetMarkerSize(0.6)

    # draw data+fit and residuals (based on https://root.cern/doc/master/ratioplotOld_8C.html)
    c1_log10 = ROOT.TCanvas('c1_log10','c1_log10',600,800)

    # Upper plot will be in pad1_log10
    pad1_log10 = ROOT.TPad('pad1_log10', 'pad1_log10', 0, 0.3, 1, 1.0)
    pad1_log10.SetBottomMargin(0) # Upper and lower plot are joined
    pad1_log10.Draw()             # Draw the upper pad: pad1_log10
    pad1_log10.cd()               # pad1_log10 becomes the current pad
    tge_log10.SetTitle(INPUT_CSVFILE)
    tge_log10.Draw('AP')          # Draw tge_log10
    tge_log10.GetHistogram().GetYaxis().SetLabelSize(0.03)
    tge_log10.GetHistogram().GetYaxis().SetTitle('gain [dB]')
    pad1_log10.Update()

    # Lower plot will be in pad2_log10
    c1_log10.cd()          # Go back to the main canvas before defining pad2_log10
    pad2_log10 = ROOT.TPad('pad2_log10', 'pad2_log10', 0, 0.05, 1, 0.3)
    pad2_log10.SetTopMargin(0)
    pad2_log10.SetBottomMargin(0.2)
    pad2_log10.Draw()
    pad2_log10.cd()       # pad2_log10 becomes the current pad   # Upper plot will be in pad1_log10
    pad2_log10.SetGridy() # horizontal grid

    tg_log10.SetTitle('')
    tg_log10.GetHistogram().SetMinimum(-3.)
    tg_log10.GetHistogram().SetMaximum(+3.)

    tg_log10.GetHistogram().GetXaxis().SetLabelSize(0.07)
    tg_log10.GetHistogram().GetXaxis().SetTitle('log_{10} (f/Hz)')
    tg_log10.GetHistogram().GetXaxis().SetTitleSize(0.07)

    tg_log10.GetHistogram().GetYaxis().SetLabelSize(0.07)
    tg_log10.GetHistogram().GetYaxis().SetTitle('(value-fit)/err')
    tg_log10.GetHistogram().GetYaxis().SetTitleSize(0.09)
    tg_log10.GetHistogram().GetYaxis().SetTitleOffset(0.5)
    tg_log10.Draw('AP')

    c1_log10.SaveAs('/tmp/c1_log10.root')

##################################
if __name__ == "__main__":
    main()
