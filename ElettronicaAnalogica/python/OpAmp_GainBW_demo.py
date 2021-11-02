# demo program of OpAmp Gain vs. BW (Bode)
import os
import array
import math
import ROOT

def broken_linear_fcn(xx, par):
    # par[0]: f3dB
    # par[1]: gainMB
    # par[2]: slope
    if xx[0] < par[0]:
        return par[1]
    else:
        return -par[2]*(xx[0]-par[0])+par[1]
    
def gain(freq):
    f3dB = 50e3 # 50 kHz
    AMB = 10.   # 
    return AMB/math.sqrt(1.+math.pow(freq/f3dB,2))

NUM_FREQ = 35

# frequencies
freq_array       = array.array('d',[1.]*NUM_FREQ)
freq_log10_array = array.array('d',[1.]*NUM_FREQ)
for icnt, val in enumerate(freq_array):
    if icnt>0:
        freq_array[icnt] = 1.5*freq_array[icnt-1]
    freq_log10_array[icnt] = math.log10(freq_array[icnt])

err_freq_array = array.array('d',[0.]*len(freq_array))

# gain
gain_array       = array.array('d',[0.]*len(freq_array))
err_gain_array   = array.array('d',[0.]*len(freq_array))
gain_dB_array     = array.array('d',[0.]*len(freq_array))
err_gain_dB_array = array.array('d',[1.]*len(freq_array))

for icnt, val in enumerate(freq_array):
    gain_array[icnt] = gain(val)
    gain_dB_array[icnt] = 20.*math.log10(gain_array[icnt]) # convert to dB
    err_gain_array[icnt] = 0.1*gain(val)

# freq with LogX
tge = ROOT.TGraphErrors(len(freq_array),freq_array, gain_array, err_freq_array, err_gain_array)
tge.SetMarkerStyle(ROOT.kFullDotMedium)

# log10(freq) with linX, gain in dB
tge_log10 = ROOT.TGraphErrors(len(freq_array),freq_log10_array, gain_dB_array, err_freq_array, err_gain_dB_array)
tge_log10.SetMarkerStyle(ROOT.kFullDotMedium)

c1 = ROOT.TCanvas('c1','c1',400,600)
c1.Divide(1,2)

# lin-lin scale
c1.cd(1)
tge.Draw('AP')
tge.GetXaxis().SetTitle('f [Hz]')
tge.GetYaxis().SetTitle('gain')
c1.GetPad(1).SetGridx()
c1.GetPad(1).SetGridy()
c1.GetPad(1).SetLogx()

# log-log scale
c1.cd(2)
fit_broken_line = ROOT.TF1('fit_broken_line', broken_linear_fcn, 1.0, 6.0, 3)   
fit_broken_line.SetNpx(10000)
fit_broken_line.SetParameters(4., 20.0, 10.0)
fit_broken_line.SetLineColor(ROOT.kRed)
tge_log10.Fit('fit_broken_line', 'R') # first argument is the name of the TF1 (e.g. char) not of the variable
tge_log10.Draw('AP')
tge_log10.GetXaxis().SetTitle('log_{10}(f/Hz)')
tge_log10.GetYaxis().SetTitle('[dB]')
c1.GetPad(2).SetGridx()
c1.GetPad(2).SetGridy()

p0 = fit_broken_line.GetParameter(0)
p1 = fit_broken_line.GetParameter(1)
p2 = fit_broken_line.GetParameter(2)


print('f3dB from intersection of the two lines', p0, math.pow(10.,p0), p0*math.pow(10.,p0))
print('f3dB from -3dB in the neg slope line', p0+3.0/p2, math.pow(10.,p0+3.0/p2), (p0+3.0/p2)*math.pow(10.,p0+3.0/p2))

c1.SaveAs(os.path.join('/Users/migliore/Documents/didattica/2016/Laboratorio Elettronica','OpAmp_GainBW.pdf'))

