import ROOT
import argparse

def main(args):
    histfile = ROOT.TFile(args.inputfile, "READ")
    if histfile.IsZombie():
        print(f"Error: cannot open {args.inputfile}")
        return

    h_mass     = histfile.Get("h_mass")
    h_prefit   = histfile.Get("h_prefit")
    h_gen_mass = histfile.Get("h_gen_mass")
    h_res      = histfile.Get("h_res")
    h_pt       = histfile.Get("h_pt")
    h_elec_pt  = histfile.Get("h_elec_pt")
    h_eta      = histfile.Get("h_eta")
    h_elec_eta = histfile.Get("h_elec_eta")

    for name, obj in [
        ("h_mass", h_mass), ("h_prefit", h_prefit),
        ("h_gen_mass", h_gen_mass), ("h_res", h_res),
        ("h_pt", h_pt), ("h_elec_pt", h_elec_pt),
        ("h_eta", h_eta), ("h_elec_eta", h_elec_eta),
    ]:
        if not obj or obj.IsA().GetName() == "TObject":
            print(f"ERROR: histogram '{name}' not found in {args.inputfile}")
            histfile.Close()
            return

    ROOT.gStyle.SetOptStat(1)

    # --- M(ee): post-fit vs pre-fit ---
    c1 = ROOT.TCanvas("c1", "M(ee)", 800, 600)
    c1.Divide(1, 2)
    c1.cd(1)
    h_mass.SetLineColor(ROOT.kBlue)
    h_mass.SetLineWidth(2)
    h_mass.Draw("HIST")
    c1.cd(2)
    h_prefit.SetLineColor(ROOT.kRed)
    h_prefit.SetLineWidth(2)
    h_prefit.Draw("HIST")
    c1.SaveAs("HZZ_ee_mass.png")

    # --- MC Truth ---
    c2 = ROOT.TCanvas("c2", "MC Truth", 800, 600)
    h_gen_mass.SetLineColor(ROOT.kGreen+2)
    h_gen_mass.SetLineWidth(2)
    h_gen_mass.Draw("HIST")
    c2.SaveAs("HZZ_ee_gen_mass.png")

    # --- Resolucion ---
    c3 = ROOT.TCanvas("c3", "Resolution", 800, 600)
    h_res.SetLineColor(ROOT.kBlack)
    h_res.SetLineWidth(2)
    h_res.Draw("HIST")
    c3.SaveAs("HZZ_ee_resolution.png")

    # --- pT: Z arriba, electrones abajo ---
    c4 = ROOT.TCanvas("c4", "pT", 800, 600)
    c4.Divide(1, 2)
    c4.cd(1)
    h_pt.SetLineColor(ROOT.kBlue)
    h_pt.SetLineWidth(2)
    h_pt.Draw("HIST")
    c4.cd(2)
    h_elec_pt.SetLineColor(ROOT.kRed)
    h_elec_pt.SetLineWidth(2)
    h_elec_pt.Draw("HIST")
    c4.SaveAs("HZZ_ee_pt.png")

    # --- eta: Z arriba, electrones abajo ---
    c5 = ROOT.TCanvas("c5", "eta", 800, 600)
    c5.Divide(1, 2)
    c5.cd(1)
    h_eta.SetLineColor(ROOT.kBlue)
    h_eta.SetLineWidth(2)
    h_eta.Draw("HIST")
    c5.cd(2)
    h_elec_eta.SetLineColor(ROOT.kRed)
    h_elec_eta.SetLineWidth(2)
    h_elec_eta.Draw("HIST")
    c5.SaveAs("HZZ_ee_eta.png")

    print("Plots saved:")
    print("  - HZZ_ee_mass.png        (M(ee) post-fit azul, pre-fit rojo)")
    print("  - HZZ_ee_gen_mass.png    (MC truth)")
    print("  - HZZ_ee_resolution.png  (resolucion de masa)")
    print("  - HZZ_ee_pt.png          (pT Z arriba, pT electrones abajo)")
    print("  - HZZ_ee_eta.png         (eta Z arriba, eta electrones abajo)")
    print(f"  - Post-fit entries:   {int(h_mass.GetEntries())}")
    print(f"  - Pre-fit entries:    {int(h_prefit.GetEntries())}")
    print(f"  - Z pT entries:       {int(h_pt.GetEntries())}")
    print(f"  - Z eta entries:      {int(h_eta.GetEntries())}")

    histfile.Close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Make plots from H->ZZ*->eeX histogram ROOT file"
    )
    parser.add_argument("inputfile", help="The histogram ROOT file (output of make_HZZ_ee_hists)")
    args = parser.parse_args()
    main(args)
