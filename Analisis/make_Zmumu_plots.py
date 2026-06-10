import ROOT
import argparse

def main(args):
    histfile = ROOT.TFile(args.inputfile, "READ")
    if histfile.IsZombie():
        print(f"Error: cannot open {args.inputfile}")
        return

    # Cargar histogramas con los nombres exactos del .cpp
    hists = {
        "h_mass":    histfile.Get("h_mass"),
        "h_prefit":  histfile.Get("h_prefit"),
        "h_gen_mass":histfile.Get("h_gen_mass"),
        "h_res":     histfile.Get("h_res"),
        "h_pt":      histfile.Get("h_pt"),
        "h_mu_pt":   histfile.Get("h_mu_pt"),
        "h_eta":     histfile.Get("h_eta"),
        "h_mu_eta":  histfile.Get("h_mu_eta"),
    }

    # Verificar que todos existen
    for name, obj in hists.items():
        if not obj or obj.IsA().GetName() == "TObject":
            print(f"ERROR: histogram '{name}' not found in {args.inputfile}")
            histfile.Close()
            return

    ROOT.gStyle.SetOptStat(1)

    # --- Masa post-fit vs pre-fit ---
    c1 = ROOT.TCanvas("c1", "Z Mass", 800, 600)
    c1.Divide(1, 2)
    c1.cd(1)
    hists["h_mass"].SetLineColor(ROOT.kBlue)
    hists["h_mass"].SetLineWidth(2)
    hists["h_mass"].Draw("HIST")
    c1.cd(2)
    hists["h_prefit"].SetLineColor(ROOT.kRed)
    hists["h_prefit"].SetLineWidth(2)
    hists["h_prefit"].Draw("HIST")
    c1.SaveAs("Z_mass_comparison.png")

    # --- MC Truth ---
    c2 = ROOT.TCanvas("c2", "MC Truth Mass", 800, 600)
    hists["h_gen_mass"].SetLineColor(ROOT.kGreen+2)
    hists["h_gen_mass"].SetLineWidth(2)
    hists["h_gen_mass"].Draw("HIST")
    c2.SaveAs("Z_gen_mass.png")

    # --- Resolucion ---
    c3 = ROOT.TCanvas("c3", "Mass Resolution", 800, 600)
    hists["h_res"].SetLineColor(ROOT.kBlack)
    hists["h_res"].SetLineWidth(2)
    hists["h_res"].Draw("HIST")
    c3.SaveAs("Z_resolution.png")

    # --- pT: Z arriba, muones abajo ---
    c4 = ROOT.TCanvas("c4", "Transverse Momentum", 800, 600)
    c4.Divide(1, 2)
    c4.cd(1)
    hists["h_pt"].SetLineColor(ROOT.kBlue)
    hists["h_pt"].SetLineWidth(2)
    hists["h_pt"].Draw("HIST")
    c4.cd(2)
    hists["h_mu_pt"].SetLineColor(ROOT.kRed)
    hists["h_mu_pt"].SetLineWidth(2)
    hists["h_mu_pt"].Draw("HIST")
    c4.SaveAs("Z_pt.png")

    # --- eta: Z arriba, muones abajo ---
    c5 = ROOT.TCanvas("c5", "Pseudorapidity", 800, 600)
    c5.Divide(1, 2)
    c5.cd(1)
    hists["h_eta"].SetLineColor(ROOT.kBlue)
    hists["h_eta"].SetLineWidth(2)
    hists["h_eta"].Draw("HIST")
    c5.cd(2)
    hists["h_mu_eta"].SetLineColor(ROOT.kRed)
    hists["h_mu_eta"].SetLineWidth(2)
    hists["h_mu_eta"].Draw("HIST")
    c5.SaveAs("Z_eta.png")

    print("Plots saved:")
    print("  - Z_mass_comparison.png  (post-fit azul, pre-fit rojo)")
    print("  - Z_gen_mass.png         (MC truth)")
    print("  - Z_resolution.png       (resolucion de masa)")
    print("  - Z_pt.png               (pT Z arriba, pT muones abajo)")
    print("  - Z_eta.png              (eta Z arriba, eta muones abajo)")
    print(f"  - Post-fit entries:  {int(hists['h_mass'].GetEntries())}")
    print(f"  - Pre-fit entries:   {int(hists['h_prefit'].GetEntries())}")
    print(f"  - Z pT entries:      {int(hists['h_pt'].GetEntries())}")
    print(f"  - Z eta entries:     {int(hists['h_eta'].GetEntries())}")

    histfile.Close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Make plots from Z histogram ROOT file"
    )
    parser.add_argument("inputfile", help="The histogram ROOT file (output of make_Z_hists)")
    args = parser.parse_args()
    main(args)
