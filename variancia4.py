import ROOT
from podio import root_io
import sys
import os

ROOT.gROOT.SetBatch(True)

archivos = {
    10: "/eos/user/m/mbabioel/outputs_reco/k1e6th10.edm4hep.root",
    15: "/eos/user/m/mbabioel/outputs_reco/k1e6th15.edm4hep.root",
    20: "/eos/user/m/mbabioel/outputs_reco/k1e6th20.edm4hep.root",
    25: "/eos/user/m/mbabioel/outputs_reco/k1e6th25.edm4hep.root",
    30: "/eos/user/m/mbabioel/outputs_reco/k1e6th30.edm4hep.root",
}

colecciones = ["VXDTrackerHits"]

thresholds    = []
sigmas_before = []
sigmas_after  = []
n_hits_list   = []

for thresh, archivo in sorted(archivos.items()):
    if not os.path.exists(archivo):
        print(f"Archivo no encontrado: {archivo}")
        continue

    print(f"\nProcesando threshold={thresh}, archivo={archivo}")

    try:
        reader = root_io.Reader(archivo)
    except Exception as e:
        print(f"Error: {e}")
        continue

    h_before  = ROOT.TH1F(f"h_before_{thresh}",  f"Threshold={thresh};#Delta T [ns];Hits",       100, -1.0, 1.0)
    h_after   = ROOT.TH1F(f"h_after_{thresh}",   f"Threshold={thresh} corregido;#Delta T [ns];Hits", 100, -1.0, 1.0)
    h_profile = ROOT.TProfile(f"h_prof_{thresh}", f"Perfil threshold={thresh};TOT [ns];#Delta T [ns]", 50, 0.0, 10.0, -1.0, 1.0)

    tots   = []
    deltas = []
    num_hits = 0

    for frame in reader.get("events"):
        for col_name in colecciones:
            hits = frame.get(col_name)
            if hits:
                for hit in hits:
                    toa   = hit.getTime()
                    t_g4  = hit.getEDep()
                    tot   = hit.getEDepError()
                    delta = toa - t_g4
                    if t_g4 > 0 and tot > 0:
                        tots.append(tot)
                        deltas.append(delta)
                        h_before.Fill(delta)
                        h_profile.Fill(tot, delta)
                        num_hits += 1

    print(f"  Hits validos: {num_hits}")

    # Ajuste polinomico grado 4
    f_tw = ROOT.TF1(f"f_tw_{thresh}",
                    "[0] + [1]*x + [2]*x*x + [3]*x*x*x + [4]*x*x*x*x",
                    0.1, 10.0)
    f_tw.SetParameters(0.1, -0.1, 0.01, -0.001, 0.0001)
    h_profile.Fit(f_tw, "RWQ")

    a = f_tw.GetParameter(0)
    b = f_tw.GetParameter(1)
    c = f_tw.GetParameter(2)
    d = f_tw.GetParameter(3)
    e = f_tw.GetParameter(4)
    print(f"  Ajuste grado 4: a={a:.4f} b={b:.4f} c={c:.4f} d={d:.4f} e={e:.6f}")
    print(f"  Chi2/NDF = {f_tw.GetChisquare():.2f} / {f_tw.GetNDF()}")

    # Aplicar corrección polinómica grado 4
    for tot, delta in zip(tots, deltas):
        if tot > 0:
            corr = a + b*tot + c*tot**2 + d*tot**3 + e*tot**4
            h_after.Fill(delta - corr)

    # Ajuste gaussiano antes
    f_gaus_before = ROOT.TF1(f"gaus_before_{thresh}", "gaus", -1.0, 1.0)
    h_before.Fit(f_gaus_before, "RQ")
    sigma_before = abs(f_gaus_before.GetParameter(2))

    # Ajuste gaussiano después
    f_gaus_after = ROOT.TF1(f"gaus_after_{thresh}", "gaus", -0.5, 0.5)
    h_after.Fit(f_gaus_after, "RQ")
    sigma_after = abs(f_gaus_after.GetParameter(2))

    print(f"  Sigma antes:   {sigma_before*1000:.1f} ps")
    print(f"  Sigma despues: {sigma_after*1000:.1f} ps")

    thresholds.append(thresh)
    sigmas_before.append(sigma_before * 1000)
    sigmas_after.append(sigma_after * 1000)
    n_hits_list.append(num_hits)

    # Histograma antes/después por threshold
    c_ind = ROOT.TCanvas(f"c_{thresh}", f"Threshold {thresh}", 800, 600)
    h_before.SetLineColor(ROOT.kRed)
    h_before.SetLineWidth(2)
    h_after.SetLineColor(ROOT.kBlue)
    h_after.SetLineWidth(2)
    ymax = max(h_before.GetMaximum(), h_after.GetMaximum()) * 1.2
    h_before.SetMaximum(ymax)
    h_before.SetTitle(f"TOA - T_{{Geant4}} despues de la correccion (threshold={thresh});#Delta T [ns];Hits")
    h_before.Draw()
    h_after.Draw("SAME")
    f_gaus_after.SetLineColor(ROOT.kCyan+1)
    f_gaus_after.SetLineWidth(2)
    f_gaus_after.Draw("SAME")
    leg = ROOT.TLegend(0.6, 0.72, 0.92, 0.88)
    leg.AddEntry(h_before,       "Antes correccion",   "l")
    leg.AddEntry(h_after,        "Despues correccion", "l")
    leg.AddEntry(f_gaus_after,   f"Gauss: #sigma={sigma_after*1000:.1f} ps", "l")
    leg.Draw()
    ROOT.gStyle.SetOptStat(111111)
    c_ind.SaveAs(f"timewalk_threshold{thresh}.png")
    print(f"  Guardado: timewalk_threshold{thresh}.png")

# --- Graficas resumen ---
n = len(thresholds)
if n > 0:
    ROOT.gStyle.SetOptStat(0)

    g_before = ROOT.TGraph(n)
    g_after  = ROOT.TGraph(n)
    g_hits   = ROOT.TGraph(n)
    g_mejora = ROOT.TGraph(n)

    for i, (th, sb, sa, nh) in enumerate(zip(thresholds, sigmas_before, sigmas_after, n_hits_list)):
        g_before.SetPoint(i, th, sb)
        g_after.SetPoint(i,  th, sa)
        g_hits.SetPoint(i,   th, nh)
        g_mejora.SetPoint(i, th, sb/sa if sa > 0 else 0)

    # Sigma vs threshold
    c_sigma = ROOT.TCanvas("c_sigma", "Sigma vs Threshold", 800, 600)
    c_sigma.SetGrid()
    g_before.SetTitle("Resolucion temporal vs Threshold;Threshold [u.a.];#sigma [ps]")
    g_before.SetMarkerStyle(20)
    g_before.SetMarkerSize(1.2)
    g_before.SetMarkerColor(ROOT.kRed)
    g_before.SetLineColor(ROOT.kRed)
    g_before.SetLineWidth(2)
    g_after.SetMarkerStyle(21)
    g_after.SetMarkerSize(1.2)
    g_after.SetMarkerColor(ROOT.kBlue)
    g_after.SetLineColor(ROOT.kBlue)
    g_after.SetLineWidth(2)
    g_before.GetYaxis().SetRangeUser(0, max(sigmas_before) * 1.3)
    g_before.Draw("APL")
    g_after.Draw("PL SAME")
    leg_sigma = ROOT.TLegend(0.60, 0.75, 0.9, 0.9)
    leg_sigma.AddEntry(g_before, "Antes de correccion",   "pl")
    leg_sigma.AddEntry(g_after,  "Despues de correccion", "pl")
    leg_sigma.Draw()
    c_sigma.SaveAs("sigma_vs_threshold.png")
    print("\nGuardado: sigma_vs_threshold.png")

    # Hits vs threshold
    c_hits = ROOT.TCanvas("c_hits", "Hits vs Threshold", 800, 600)
    c_hits.SetGrid()
    g_hits.SetTitle("Hits validos vs Threshold;Threshold [u.a.];Hits")
    g_hits.SetMarkerStyle(20)
    g_hits.SetMarkerSize(1.2)
    g_hits.SetMarkerColor(ROOT.kBlack)
    g_hits.SetLineColor(ROOT.kBlack)
    g_hits.SetLineWidth(2)
    g_hits.GetYaxis().SetRangeUser(0, max(n_hits_list) * 1.2)
    g_hits.Draw("APL")
    c_hits.SaveAs("hits_vs_threshold.png")
    print("Guardado: hits_vs_threshold.png")

    # Mejora vs threshold
    c_mejora = ROOT.TCanvas("c_mejora", "Mejora vs Threshold", 800, 600)
    c_mejora.SetGrid()
    mejoras = [sigmas_before[i]/sigmas_after[i] if sigmas_after[i] > 0 else 0 for i in range(n)]
    g_mejora.SetTitle("Factor de mejora vs Threshold;Threshold [u.a.];#sigma_{antes}/#sigma_{despues}")
    g_mejora.SetMarkerStyle(20)
    g_mejora.SetMarkerSize(1.2)
    g_mejora.SetMarkerColor(ROOT.kGreen+2)
    g_mejora.SetLineColor(ROOT.kGreen+2)
    g_mejora.SetLineWidth(2)
    g_mejora.GetYaxis().SetRangeUser(0, max(mejoras) * 1.3)
    g_mejora.Draw("APL")
    line = ROOT.TLine(thresholds[0], 1, thresholds[-1], 1)
    line.SetLineStyle(2)
    line.SetLineColor(ROOT.kGray+1)
    line.Draw()
    idx_max = mejoras.index(max(mejoras))
    latex = ROOT.TLatex()
    latex.SetTextSize(0.035)
    latex.SetTextColor(ROOT.kRed)
    c_mejora.SaveAs("mejora_vs_threshold.png")
    print("Guardado: mejora_vs_threshold.png")

    print("\n=== RESUMEN ===")
    print(f"{'Threshold':>10} {'Hits':>10} {'Sigma antes [ps]':>18} {'Sigma despues [ps]':>20} {'Mejora':>8}")
    for th, sb, sa, nh in zip(thresholds, sigmas_before, sigmas_after, n_hits_list):
        print(f"{th:>10} {nh:>10} {sb:>18.1f} {sa:>20.1f} {sb/sa if sa>0 else 0:>8.2f}x")
