import ROOT
from podio import root_io
import sys
import os

if len(sys.argv) < 2:
    print("Uso: python3 plot_toa.py <archivo.edm4hep.root>")
    sys.exit(1)

archivo_input = sys.argv[1]
if not os.path.exists(archivo_input):
    print(f"Error: El archivo '{archivo_input}' no existe.")
    sys.exit(1)

try:
    reader = root_io.Reader(archivo_input)
except Exception as e:
    print(f"Error al abrir el archivo con podio: {e}")
    sys.exit(1)

ROOT.gROOT.SetBatch(True)

# Histogramas antes de corrección
h_before = ROOT.TH1F("h_before", "TOA - T_{Geant4} despues de la correccion;#Delta T [ns];Hits",
                     100, -1.0, 1.0)
# Histograma después de corrección
h_after  = ROOT.TH1F("h_after",  "TOA - T_{Geant4} DESPUES de correccion;#Delta T [ns];Hits",
                     100, -1.0, 1.0)
# Perfil TOA-t vs TOT (para ver el time walk y el ajuste)
h_profile = ROOT.TProfile("h_profile", "Perfil TOA - T_{Geant4} vs TOT;TOT [ns];#Delta T [ns]",
                           50, 0.0, 10.0, -1.0, 1.0)
# Scatter antes
g_before = ROOT.TGraph()
g_before.SetTitle("TOA - T_{Geant4} vs TOT ANTES;TOT [ns];TOA - T_{Geant4} [ns]")

# Scatter después
g_after = ROOT.TGraph()
g_after.SetTitle("TOA - T_{Geant4} vs TOT DESPUES;TOT [ns];TOA - T_{Geant4} [ns]")

print("Recopilando hits...")
tots  = []
deltas = []
num_eventos = 0
num_hits = 0

for frame in reader.get("events"):
    num_eventos += 1
    hits = frame.get("VXDTrackerHits")
    if hits:
        for hit in hits:
            toa  = hit.getTime()
            t_g4 = hit.getEDep()
            tot  = hit.getEDepError()
            delta = toa - t_g4
            if t_g4 > 0 and tot > 0:
                tots.append(tot)
                deltas.append(delta)
                h_before.Fill(delta)
                h_profile.Fill(tot, delta)
                num_hits += 1

print(f"Procesados {num_eventos} eventos, {num_hits} hits.")

# Ajuste del perfil para obtener la corrección
# Usamos f(TOT) = a/sqrt(TOT) + b  (modelo físico del time walk)
#f_timewalk = ROOT.TF1("f_timewalk", "[0]/sqrt(x) + [1]", 0.1, 10.0)
#f_timewalk = ROOT.TF1("f_timewalk", "[0] + [1] * x + [2] * x*x + [3] * x * x * x", 0.1, 10.0)
#f_timewalk = ROOT.TF1("f_timewalk", "[0] + [1] * x + [2] * x*x", 0.1, 10.0)
f_timewalk = ROOT.TF1("f_timewalk", "[0] + [1] * x + [2] * x*x + [3] * x * x * x +[4] * x * x * x*x", 0.1, 10.0)



#f_timewalk.SetParameters(0.5, 0.0)
f_timewalk.SetParameters(0.1, -10.0, -1.0, 0.01, 0.001)
#f_timewalk.SetParameters(0.1, -10.0, -1.0)

h_profile.Fit(f_timewalk, "RWQ")

a = f_timewalk.GetParameter(0)
b = f_timewalk.GetParameter(1)
c = f_timewalk.GetParameter(2)
d = f_timewalk.GetParameter(3)
e = f_timewalk.GetParameter(4)


print(f"Ajuste time walk: a={a:.4f}, b={b:.4f}")
print(f"  f(TOT) = {a:.4f}/sqrt(TOT) + {b:.4f}")

# Aplicar corrección y llenar histogramas corregidos
for i, (tot, delta) in enumerate(zip(tots, deltas)):
    if tot > 0:
        #correccion = a + b * tot  + c * tot*tot + d *tot*tot*tot
        #correccion = a + b * tot  + c * tot*tot 
        correccion = a + b * tot  + c * tot*tot + d *tot*tot*tot + e *tot*tot*tot*tot


        delta_corr = delta - correccion
        h_after.Fill(delta_corr)
        g_before.SetPoint(i, tot, delta)
        g_after.SetPoint(i, tot, delta_corr)

ROOT.gStyle.SetOptStat(111111)

# --- PNG 1: histogramas antes y después superpuestos ---
ROOT.gStyle.SetOptStat(0)
c1 = ROOT.TCanvas("c1", "Correccion Time Walk", 800, 600)
h_before.SetLineColor(ROOT.kRed)
h_before.SetLineWidth(2)
h_after.SetLineColor(ROOT.kBlue)
h_after.SetLineWidth(2)
ymax = max(h_before.GetMaximum(), h_after.GetMaximum()) * 1.2
h_before.SetMaximum(ymax)
h_before.Draw()
h_after.Draw("SAME")
legend = ROOT.TLegend(0.65, 0.75, 0.9, 0.85)
legend.AddEntry(h_before, "Antes de la correccion", "l")
legend.AddEntry(h_after,  "Despues de la correccion", "l")
legend.Draw()
c1.SaveAs("timewalk_correction.png")
print("Guardado: timewalk_correction.png")

# --- PNG 2: perfil con ajuste ---
ROOT.gStyle.SetOptStat(0)
c2 = ROOT.TCanvas("c2", "Perfil Time Walk", 800, 600)
h_profile.SetLineColor(ROOT.kBlack)
h_profile.SetMarkerStyle(20)
h_profile.Draw()
f_timewalk.SetLineColor(ROOT.kRed)
f_timewalk.Draw("SAME")
legend2 = ROOT.TLegend(0.5, 0.7, 0.9, 0.85)
legend2.AddEntry(h_profile, "Perfil TOA-T_{G4} vs TOT", "p")
legend2.AddEntry(f_timewalk, f"Ajuste: {a:.3f}/sqrt(TOT)+{b:.3f}", "l")
legend2.Draw()
c2.SaveAs("timewalk_profile.png")
print("Guardado: timewalk_profile.png")

# --- PNG 3: scatter antes ---
c3 = ROOT.TCanvas("c3", "Scatter antes", 800, 600)
g_before.SetMarkerStyle(6)
g_before.SetMarkerColor(ROOT.kRed)
g_before.GetXaxis().SetRangeUser(0, 10)
g_before.GetYaxis().SetRangeUser(-1, 1)
g_before.Draw("AP")
c3.SaveAs("scatter_antes.png")
print("Guardado: scatter_antes.png")

# --- PNG 4: scatter después ---
c4 = ROOT.TCanvas("c4", "Scatter despues", 800, 600)
g_after.SetMarkerStyle(6)
g_after.SetMarkerColor(ROOT.kBlue)
g_after.GetXaxis().SetRangeUser(0, 10)
g_after.GetYaxis().SetRangeUser(-1, 1)
g_after.Draw("AP")
c4.SaveAs("scatter_despues.png")
print("Guardado: scatter_despues.png")
