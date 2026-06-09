import ROOT
from podio.reading import get_reader
from edm4hep import utils
p4 = utils.p4
UseEnergy = utils.UseEnergy

def main(args):
    """Main"""
    reader = get_reader(args.inputfile)
    events = reader.get("events")

    histfile = ROOT.TFile(args.outputfile, "recreate")

    # M(gg)
    Higgs_mass = ROOT.TH1D("Higgs_mass", ";M_{H} [GeV];Entries",                        100, 110.0, 140.0)
    Higgs_mass_p4 = ROOT.TH1D("Higgs_p4", ";M_{#gamma#gamma} [GeV];Entries",            100, 110.0, 140.0)
    Higgs_mass_prefit = ROOT.TH1D(
        "Higgs_mass_prefit", ";M_{#gamma#gamma} (prefit) [GeV];Entries",                 100,  90.0, 160.0
    )
    fit_delta_m = ROOT.TH1D(
        "fit_delta_m",
        ";M_{#gamma#gamma} (postfit) - M_{#gamma#gamma} (prefit) [GeV];Entries",
        100, -15.0, 15.0,
    )

    # pT
    Higgs_pt    = ROOT.TH1D("Higgs_pt",    ";p_{T}^{H} [GeV];Entries",                  100,   0.0, 200.0)
    gamma_pt    = ROOT.TH1D("gamma_pt",    ";p_{T}^{#gamma} [GeV];Entries",              100,   0.0, 150.0)

    # eta
    Higgs_eta   = ROOT.TH1D("Higgs_eta",   ";#eta^{H};Entries",                          100,  -5.0,   5.0)
    gamma_eta   = ROOT.TH1D("gamma_eta",   ";#eta^{#gamma};Entries",                     100,  -5.0,   5.0)

    for event in events:
        Higgs = event.get("Higgs_New")
        for H in Higgs:
            # Masa
            Higgs_mass.Fill(H.getMass())
            H_p4 = p4(H, UseEnergy)
            Higgs_mass_p4.Fill(H_p4.M())

            # pT y eta del Higgs
            import math
            px  = H.getMomentum().x
            py  = H.getMomentum().y
            pz  = H.getMomentum().z
            pt  = math.sqrt(px*px + py*py)
            eta = math.asinh(pz / pt) if pt > 0 else 0.0
            Higgs_pt.Fill(pt)
            Higgs_eta.Fill(eta)

            # Pre-fit y cinematica de los fotones hijos
            gamma1_p4 = p4(H.getParticles()[0], UseEnergy)
            gamma2_p4 = p4(H.getParticles()[1], UseEnergy)
            prefit_H = gamma1_p4 + gamma2_p4
            Higgs_mass_prefit.Fill(prefit_H.M())
            fit_delta_m.Fill(H_p4.M() - prefit_H.M())

            # pT y eta de cada foton
            for gamma in [H.getParticles()[0], H.getParticles()[1]]:
                gpx  = gamma.getMomentum().x
                gpy  = gamma.getMomentum().y
                gpz  = gamma.getMomentum().z
                gpt  = math.sqrt(gpx*gpx + gpy*gpy)
                geta = math.asinh(gpz / gpt) if gpt > 0 else 0.0
                gamma_pt.Fill(gpt)
                gamma_eta.Fill(geta)

    Higgs_mass.Write()
    Higgs_mass_p4.Write()
    Higgs_mass_prefit.Write()
    fit_delta_m.Write()
    Higgs_pt.Write()
    gamma_pt.Write()
    Higgs_eta.Write()
    gamma_eta.Write()
    histfile.Close()

if __name__ == "__main__":
    import argparse
    import math
    parser = argparse.ArgumentParser(
        description="Small script to make Higgs -> gg histograms via python bindings and ROOT"
    )
    parser.add_argument("inputfile", help="The input file with the data")
    parser.add_argument(
        "outputfile",
        nargs="?",
        default="Higgs_histograms.root",
        help="The output file into which the histograms will be stored",
    )
    args = parser.parse_args()
    main(args)
