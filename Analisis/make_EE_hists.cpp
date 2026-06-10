#include <podio/Frame.h>
#include <podio/ROOTReader.h>
#include <edm4hep/ReconstructedParticleCollection.h>
#include <edm4hep/RecoMCParticleLinkCollection.h>
#include <edm4hep/utils/kinematics.h>
#include <TFile.h>
#include <TH1D.h>
#include <iostream>
#include <memory>
#include <string>
#include <cmath>

/**
 * Analysis executable for H -> ZZ* -> eeX reconstruction.
 * Produces: M(ee), pT and eta of the Z->ee and of each electron.
 */
int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cout << "Usage: ./make_HZZ_ee_hists <input.root> <collection_name> [output.root]" << std::endl;
        std::cout << "  collection_name: typically 'Zee_New'" << std::endl;
        return 1;
    }
    std::string inputfile  = argv[1];
    std::string colName    = argv[2];
    std::string outputfile = (argc >= 4) ? argv[3] : "HZZ_ee_histograms_output.root";

    podio::ROOTReader reader;
    try {
        reader.openFile(inputfile);
    } catch (const std::exception& e) {
        std::cerr << "Error opening file: " << e.what() << std::endl;
        return 1;
    }

    auto hfile = std::make_unique<TFile>(outputfile.c_str(), "RECREATE");

    // M(ee)
    auto h_mass      = new TH1D("h_mass",      "Post-fit M(ee);M_{ee} [GeV];Entries",              100, 50.0, 120.0);
    auto h_prefit    = new TH1D("h_prefit",     "Pre-fit M(ee);M_{ee} (prefit) [GeV];Entries",      100, 30.0, 130.0);
    auto h_gen_mass  = new TH1D("h_gen_mass",   "MC Truth M(Z);M_{Z} [GeV];Entries",                100, 50.0, 120.0);
    auto h_res       = new TH1D("h_res",        "Mass Resolution;M_{reco}-M_{gen} [GeV];Entries",   100,-10.0,  10.0);

    // pT
    auto h_pt        = new TH1D("h_pt",         "Z->ee Transverse Momentum;p_{T}^{Z} [GeV];Entries",  100,  0.0, 100.0);
    auto h_elec_pt   = new TH1D("h_elec_pt",    "Electron Transverse Momentum;p_{T}^{e} [GeV];Entries",100, 0.0,  80.0);

    // eta
    auto h_eta       = new TH1D("h_eta",        "Z->ee Pseudorapidity;#eta^{Z};Entries",            100, -5.0,   5.0);
    auto h_elec_eta  = new TH1D("h_elec_eta",   "Electron Pseudorapidity;#eta^{e};Entries",         100, -5.0,   5.0);

    unsigned int nEvents = reader.getEntries("events");
    std::cout << "[INFO] Processing " << nEvents << " events from collection '" << colName << "'..." << std::endl;

    for (unsigned int i = 0; i < nEvents; ++i) {
        auto event = podio::Frame(reader.readEntry("events", i));
        try {
            const auto& particles = event.get<edm4hep::ReconstructedParticleCollection>(colName);

            const edm4hep::RecoMCParticleLinkCollection* associations = nullptr;
            try {
                associations = &event.get<edm4hep::RecoMCParticleLinkCollection>("RecoMCTruthLink");
            } catch (...) {}

            for (const auto& p : particles) {
                // Post-fit masa
                double recoMass = p.getMass();
                h_mass->Fill(recoMass);

                // pT y eta del Z->ee
                double px  = p.getMomentum().x;
                double py  = p.getMomentum().y;
                double pz  = p.getMomentum().z;
                double pt  = std::sqrt(px*px + py*py);
                double eta = (pt > 0) ? std::asinh(pz / pt) : 0.0;
                h_pt->Fill(pt);
                h_eta->Fill(eta);

                // Pre-fit y cinematica de los electrones
                auto daughters = p.getParticles();
                if (daughters.size() >= 2) {
                    auto p1 = edm4hep::utils::p4(daughters[0], edm4hep::utils::UseEnergy);
                    auto p2 = edm4hep::utils::p4(daughters[1], edm4hep::utils::UseEnergy);
                    double prefitMass = (p1 + p2).M();
                    h_prefit->Fill(prefitMass);

                    for (int d = 0; d < 2; ++d) {
                        double epx  = daughters[d].getMomentum().x;
                        double epy  = daughters[d].getMomentum().y;
                        double epz  = daughters[d].getMomentum().z;
                        double ept  = std::sqrt(epx*epx + epy*epy);
                        double eeta = (ept > 0) ? std::asinh(epz / ept) : 0.0;
                        h_elec_pt->Fill(ept);
                        h_elec_eta->Fill(eeta);
                    }
                }

                // MC Truth y resolucion
                if (associations) {
                    for (const auto& assoc : *associations) {
                        if (assoc.getFrom() == p) {
                            double genMass = assoc.getTo().getMass();
                            h_gen_mass->Fill(genMass);
                            h_res->Fill(recoMass - genMass);
                            break;
                        }
                    }
                }
            }
        } catch (const std::exception& e) {
            continue;
        }
    }

    std::cout << "[SUCCESS] Analysis finished." << std::endl;
    std::cout << "  - Post-fit entries:   " << h_mass->GetEntries()    << std::endl;
    std::cout << "  - Pre-fit entries:    " << h_prefit->GetEntries()  << std::endl;
    std::cout << "  - MC Truth entries:   " << h_gen_mass->GetEntries()<< std::endl;
    std::cout << "  - Z pT entries:       " << h_pt->GetEntries()      << std::endl;
    std::cout << "  - Z eta entries:      " << h_eta->GetEntries()     << std::endl;

    h_mass->Write();
    h_prefit->Write();
    h_gen_mass->Write();
    h_res->Write();
    h_pt->Write();
    h_elec_pt->Write();
    h_eta->Write();
    h_elec_eta->Write();
    hfile->Close();
    return 0;
}
