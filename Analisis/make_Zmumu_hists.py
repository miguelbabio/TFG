import ROOT
import math
from podio.reading import get_reader
from edm4hep import utils
p4 = utils.p4
UseEnergy = utils.UseEnergy

def main(args):
    reader = get_reader(args.inputfile)
    events = reader.get("events")
    histfile = ROOT.TFile(args.outputfile, "recreate")

    # Masa
    Z_mass        = ROOT.TH1D("Z_mass",        ";M_{Z} [GeV];Entries",                          100,  70.0, 110.0)
    Z_mass_p4     = ROOT.TH1D("Z_p4",          ";M_{#mu#mu} [GeV];Entries",                     100,  70.0, 110.0)
    Z_mass_prefit = ROOT.TH1D("Z_mass_prefit", ";M_{#mu#mu} (prefit) [GeV];Entries",            100,  50.0, 130.0)
    fit_delta_m   = ROOT.TH1D("fit_delta_m",   ";M_{#mu#mu} (postfit-prefit) [GeV];Entries",    100, -10.0,  10.0)

    # pT
    Z_pt  = ROOT.TH1D("Z_pt",  ";p_{T}^{Z} [GeV];Entries",   100, 0.0, 100.0)
    mu_pt = ROOT.TH1D("mu_pt", ";p_{T}^{#mu} [GeV];Entries", 100, 0.0, 100.0)

    # eta
    Z_eta  = ROOT.TH1D("Z_eta",  ";#eta^{Z};Entries",   100, -5.0, 5.0)
    mu_eta = ROOT.TH1D("mu_eta", ";#eta^{#mu};Entries", 100, -5.0, 5.0)

    # TOF
    tof_mu_10ps  = ROOT.TH1D("tof_mu_10ps",  ";TOF_{#mu} (10ps) [ns];Entries",  100, 0.0, 15.0)
    tof_mu_50ps  = ROOT.TH1D("tof_mu_50ps",  ";TOF_{#mu} (50ps) [ns];Entries",  100, 0.0, 15.0)
    tof_mu_100ps = ROOT.TH1D("tof_mu_100ps", ";TOF_{#mu} (100ps) [ns];Entries", 100, 0.0, 15.0)

    # ECAL hit time
    ecal_hit_time = ROOT.TH1D("ecal_hit_time", ";t_{ECAL hit} [ns];Entries", 100, 0.0, 50.0)

    for event in events:
        # Mapas PFO id -> TOF
        tof_map_10ps, tof_map_50ps, tof_map_100ps = {}, {}, {}

        for t in event.get("PandoraPFOs_PID_TOFEstimators10ps"):
            tval = list(t.getParameters())[0]
            if tval > 0:
                tof_map_10ps[t.getParticle().id()] = tval

        for t in event.get("PandoraPFOs_PID_TOFEstimators50ps"):
            tval = list(t.getParameters())[0]
            if tval > 0:
                tof_map_50ps[t.getParticle().id()] = tval

        for t in event.get("PandoraPFOs_PID_TOFEstimators100ps"):
            tval = list(t.getParameters())[0]
            if tval > 0:
                tof_map_100ps[t.getParticle().id()] = tval

        # ECAL hit times
        try:
            for hit in event.get("EcalBarrelCollectionRec"):
                ecal_hit_time.Fill(hit.getTime())
        except Exception:
            pass

        # Z candidates
        for Z in event.get("Zs_New"):
            Z_mass.Fill(Z.getMass())
            Z_p4_vec = p4(Z, UseEnergy)
            Z_mass_p4.Fill(Z_p4_vec.M())

            px = Z.getMomentum().x
            py = Z.getMomentum().y
            pz = Z.getMomentum().z
            pt = math.sqrt(px*px + py*py)
            Z_pt.Fill(pt)
            Z_eta.Fill(math.asinh(pz / pt) if pt > 0 else 0.0)

            if Z.getParticles().size() >= 2:
                mu1 = Z.getParticles()[0]
                mu2 = Z.getParticles()[1]

                mu1_p4 = p4(mu1, UseEnergy)
                mu2_p4 = p4(mu2, UseEnergy)
                Z_mass_prefit.Fill((mu1_p4 + mu2_p4).M())
                fit_delta_m.Fill(Z_p4_vec.M() - (mu1_p4 + mu2_p4).M())

                for mu in [mu1, mu2]:
                    mpx = mu.getMomentum().x
                    mpy = mu.getMomentum().y
                    mpz = mu.getMomentum().z
                    mpt = math.sqrt(mpx*mpx + mpy*mpy)
                    mu_pt.Fill(mpt)
                    mu_eta.Fill(math.asinh(mpz / mpt) if mpt > 0 else 0.0)

                    mu_id = mu.id()
                    if mu_id in tof_map_10ps:  tof_mu_10ps.Fill(tof_map_10ps[mu_id])
                    if mu_id in tof_map_50ps:  tof_mu_50ps.Fill(tof_map_50ps[mu_id])
                    if mu_id in tof_map_100ps: tof_mu_100ps.Fill(tof_map_100ps[mu_id])

    for h in [Z_mass, Z_mass_p4, Z_mass_prefit, fit_delta_m,
              Z_pt, mu_pt, Z_eta, mu_eta,
              tof_mu_10ps, tof_mu_50ps, tof_mu_100ps, ecal_hit_time]:
        h.Write()
    histfile.Close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile")
    parser.add_argument("outputfile", nargs="?", default="Z_histograms.root")
    args = parser.parse_args()
    main(args)
