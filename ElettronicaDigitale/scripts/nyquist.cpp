#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <cstdlib> 

#include <TCanvas.h>
#include <TGraphErrors.h>
#include <TF1.h>
#include <TMath.h>

using namespace std;

//Minimo e massimo dell'intervallo di frequenze in cui cercare quella campionata
const double START_FREQ = 1;
const double MAX_FREQ = 140.;

/*  Effettua fit sinusoidali sui dati contenuti nel file specificato.
    Leggere le frequenze rilevate al parametro p1, ignorando quelle il cui fit non converge.
    Attenzione: il fit converge solo per impostazioni molto precise del parametro frequenza;
    se nessun fit converge, provare a cambiare START_FREQ da 1. a 1.125 o viceversa.
    Comando da terminale:
    root -l
    .x nyquist.cpp+("nome_del_file.txt")
*/
void nyquist(const char *nomeFile)
{
    //LETTURA DEI DATI DAL FILE DI TESTO IN DUE VECTOR
    string valore;
    vector<double> tempi, codici;
    char delim = ',';
    try
    {
        ifstream file(nomeFile);
        while (getline(file, valore, delim))
        {
            if (delim == ',')
            {
                tempi.push_back(atof(valore.c_str()));
                delim = '\n';
            }
            else
            {
                codici.push_back(atof(valore.c_str()));
                delim = ',';
            }
        }
        file.close();
    }
    catch (...)
    {
        cout << "File non trovato o formato del file non supportato" << endl;
        return;
    }
    
    //CREAZIONE DEGLI ARRAY DELLE INCERTEZZE SULLE MISURE
    double err_codici[tempi.size()], err_tempi[tempi.size()], zeri[tempi.size()];
    for (unsigned int i = 0; i < tempi.size(); i++)
    {
        err_codici[i] = 0.5;
        err_tempi[i] = 0.0001; //secondi
        zeri[i] = 0.;
    }

    //GRAFICO E FIT DEI DATI, ASSUMENDO ERRORI NULLI SUI TEMPI
    TGraphErrors *g0 = new TGraphErrors(tempi.size(), &tempi[0], &codici[0], zeri, &err_codici[0]);
    const char *func = "[0]*TMath::Sin(TMath::TwoPi()*[1]*x+[2])+[3]";
    TF1 *fit = new TF1("fit", func, 0., TMath::MaxElement(tempi.size(), &tempi[0]) + 1);
    fit->SetNpx(10 * tempi.size()); //Miglioramento risoluzione del grafico
    double codiceMinimo = TMath::MinElement(codici.size(), &codici[0]);
    double codiceMassimo = TMath::MaxElement(codici.size(), &codici[0]);
    double ampiezza = (codiceMassimo - codiceMinimo) * 0.5;
    double offset = (codiceMassimo + codiceMinimo) * 0.5, frequenza = START_FREQ;
    vector<double> frequenzeMigliori;
    while (frequenza <= MAX_FREQ) //Prova frequenze tra START_FREQ e MAX_FREQ a step di 0.25Hz
    {
        fit->SetParameters(ampiezza, frequenza, 0., offset);
        g0->Fit("fit", "RQ");
        cout << "Frequenza [Hz]:" << frequenza << "; Chi^2 fit: " << fit->GetChisquare() << "\n";
        if (fit->GetProb() >= 0.95) frequenzeMigliori.push_back(frequenza);
        frequenza += 0.25;
    }

    //GRAFICI E FIT CON FREQUENZE MIGLIORI, CON AGGIUNTA DI ERRORI SUI TEMPI
    for (unsigned int i = 0; i < frequenzeMigliori.size(); i++)
    {
        string nomeCanvas = string(nomeFile) + "_" + to_string(i + 1);
        TCanvas *c = new TCanvas(nomeCanvas.c_str(), nomeCanvas.c_str(), 200, 10, 600, 400);
        TGraphErrors *g = new TGraphErrors(tempi.size(), &tempi[0], &codici[0], &err_tempi[0], &err_codici[0]);
        fit->SetParameters(ampiezza, frequenzeMigliori[i], 0, offset);
        g->Fit("fit", "RM+");
        g->SetMarkerStyle(7); //Punto di media dimensione
        g->SetTitle("");
        g->Draw("AP");
        cout << "BEST FIT" << endl << "Frequenza [Hz]:" << fit->GetParameter(1) << endl << "Chi^2:" << endl << "Ndf: " << fit->GetNDF() << "     p-value: " << fit->GetProb() << endl;
    }
}