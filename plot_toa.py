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

# Histograma 1: TOA - t_Geant4
h_diff = ROOT.TH1F("h_toa_diff", "Resolucion Temporal: TOA - T_{Geant4};#Delta T [ns];Hits",
                   100, -1.0, 1.0)

# Scatter plot: TOA-t vs TOT
graph = ROOT.TGraph()
graph.SetTitle("TOA - T_{Geant4} vs TOT;TOT [ns];TOA - T_{Geant4} [ns]")

print("Iniciando el analisis de hits...")
num_eventos = 0
num_hits    = 0
num_puntos  = 0


for frame in reader.get("events"):
    num_eventos += 1
    hits = frame.get("VXDTrackerHits")
    if hits:
        for hit in hits:
            toa   = hit.getTime()
            t_g4  = hit.getEDep()
            tot   = hit.getEDepError()
            delta = toa - t_g4
            if t_g4 > 0:
                h_diff.Fill(delta)
                graph.SetPoint(num_puntos, tot, delta)
                num_puntos += 1
                num_hits += 1

print(f"Procesados {num_eventos} eventos, {num_hits} hits validos.")

ROOT.gStyle.SetOptStat(111111)

# --- PNG 1: histograma 1D TOA - t_Geant4 ---
c1 = ROOT.TCanvas("c1", "Resolucion TOA", 800, 600)
h_diff.SetLineColor(ROOT.kBlue)
h_diff.SetLineWidth(2)
h_diff.Draw()
c1.SaveAs("toa_resolution.png")
print("Guardado: toa_resolution.png")

# --- PNG 2: scatter TOA-t vs TOT ---
c2 = ROOT.TCanvas("c2", "TOA vs TOT", 800, 600)
graph.SetMarkerStyle(6)   # punto pequeño
graph.SetMarkerColor(ROOT.kBlue)
graph.GetXaxis().SetRangeUser(0, 10)
graph.GetYaxis().SetRangeUser(-1, 1)
graph.Draw("AP")          # A=ejes, P=puntos
c2.SaveAs("toa_vs_tot.png")
print("Guardado: toa_vs_tot.png")
