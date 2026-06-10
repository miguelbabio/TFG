import ROOT
import math
from podio.reading import get_reader
from edm4hep import utils
p4 = utils.p4
UseEnergy = utils.UseEnergy

def main(args):
    """Main"""
    reader = get_reader(args.inputfile)
    events = reader.get("events")

    histfile = ROOT.TFile(args.outputfile, "recreate")

    # M(ee) — Z on-shell peak esperado en ~91 GeV
    Z_ee_mass       = ROOT.TH1D("Z_ee_mass",       ";M_{ee} [GeV];Entries",                        100, 50.0, 120.0)
    Z_ee_mass_p4    = ROOT.TH1D("Z_ee_p4",         ";M_{ee} (4-vector) [GeV];Entries",             100, 50.0, 120.0)
    Z_ee_mass_prefit= ROOT.TH1D("Z_ee_mass_prefit", ";M_{ee} (prefit) [GeV];Entries",              100, 30.0, 130.0)
    fit_delta_m     = ROOT.TH1D("fit_delta_m",      ";M_{ee} (postfit-prefit) [GeV];Entries",      100, -10.0, 10.0)

    # pT del Z->ee
    Z_ee_pt         = ROOT.TH1D("Z_ee_pt",          ";p_{T}^{Z#rightarrowee} [GeV];Entries",       100,  0.0, 100.0)
    # pT de cada electron
    electron_pt     = ROOT.TH1D("electron_pt",      ";p_{T}^{e} [GeV];Entries",                    100,  0.0,  80.0)

    # eta del Z->ee
    Z_ee_eta        = ROOT.TH1D("Z_ee_eta",         ";#eta^{Z#rightarrowee};Entries",               100, -5.0,   5.0)
    # eta de cada electron
    electron_eta    = ROOT.TH1D("electron_eta",     ";#eta^{e};Entries",                            100, -5.0,   5.0)

    for event in events:
        Zees = event.get("Zee_New")
        for Z in Zees:
            # Masa
            Z_ee_mass.Fill(Z.getMass())
            Z_p4 = p4(Z, UseEnergy)
            Z_ee_mass_p4.Fill(Z_p4.M())

            # pT y eta del Z->ee
            px  = Z.getMomentum().x
            py  = Z.getMomentum().y
            pz  = Z.getMomentum().z
            pt  = math.sqrt(px*px + py*py)
            eta = math.asinh(pz / pt) if pt > 0 else 0.0
            Z_ee_pt.Fill(pt)
            Z_ee_eta.Fill(eta)

            # Pre-fit y cinematica de los electrones hijos
            if Z.getParticles().size() >= 2:
                e1_p4 = p4(Z.getParticles()[0], UseEnergy)
                e2_p4 = p4(Z.getParticles()[1], UseEnergy)
                prefit_Z = e1_p4 + e2_p4
                Z_ee_mass_prefit.Fill(prefit_Z.M())
                fit_delta_m.Fill(Z_p4.M() - prefit_Z.M())

                # pT y eta de cada electron
                for elec in [Z.getParticles()[0], Z.getParticles()[1]]:
                    epx  = elec.getMomentum().x
                    epy  = elec.getMomentum().y
                    epz  = elec.getMomentum().z
                    ept  = math.sqrt(epx*epx + epy*epy)
                    eeta = math.asinh(epz / ept) if ept > 0 else 0.0
                    electron_pt.Fill(ept)
                    electron_eta.Fill(eeta)

    Z_ee_mass.Write()
    Z_ee_mass_p4.Write()
    Z_ee_mass_prefit.Write()
    fit_delta_m.Write()
    Z_ee_pt.Write()
    electron_pt.Write()
    Z_ee_eta.Write()
    electron_eta.Write()
    histfile.Close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Histograms for H->ZZ*->eeX reconstruction"
    )
    parser.add_argument("inputfile", help="The input file with the data")
    parser.add_argument(
        "outputfile",
        nargs="?",
        default="HZZ_ee_histograms.root",
        help="The output file into which the histograms will be stored",
    )
    args = parser.parse_args()
    main(args)
