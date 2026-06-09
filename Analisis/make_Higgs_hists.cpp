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
 * Analysis executable to produce histograms for H -> gamma gamma candidates.
 * Produces: M(gg) post-fit, M(gg) pre-fit, pT and eta of the Higgs and the two photons.
 */
int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cout << "Usage: ./make_Higgs_hists <input.root> <collection_name> [output.root]" << std::endl;
        std::cout << "  collection_name: typically 'Higgs_New'" << std::endl;
        return 1;
    }
    std::string inputfile  = argv[1];
    std::string colName    = argv[2];
    std::string outputfile = (argc >= 4) ? argv[3] : "Higgs_histograms_output.root";

    podio::ROOTReader reader;
    try {
        reader.openFile(inputfile);
    } catch (const std::exception& e) {
        std::cerr << "Error opening file: " << e.what() << std::endl;
        return 1;
    }

    auto hfile = std::make_unique<TFile>(outputfile.c_str(), "RECREATE");

    // --- Masa M(gg) ---
    auto h_mass     = new TH1D("h_mass",     "Post-fit M(#gamma#gamma);M_{H} [GeV];Entries",                  100, 110.0, 140.0);
    auto h_prefit   = new TH1D("h_prefit",   "Pre-fit M(#gamma#gamma) (Daughter Sum);M_{#gamma#gamma} [GeV];Entries", 100,  90.0, 160.0);
    auto h_gen_mass = new TH1D("h_gen_mass", "Generated (MC Truth) Mass;M_{H} [GeV];Entries",                 100, 110.0, 140.0);
    auto h_res      = new TH1D("h_res",      "Mass Resolution;M_{reco} - M_{gen} [GeV];Entries",              100, -15.0,  15.0);

    // --- pT del Higgs ---
    auto h_pt       = new TH1D("h_pt",       "Higgs Transverse Momentum;p_{T}^{H} [GeV];Entries",             100,   0.0, 200.0);
    // --- pT de cada foton hijo ---
    auto h_gamma_pt = new TH1D("h_gamma_pt", "Photon Transverse Momentum;p_{T}^{#gamma} [GeV];Entries",       100,   0.0, 150.0);

    // --- Pseudorapidez del Higgs ---
    auto h_eta       = new TH1D("h_eta",      "Higgs Pseudorapidity;#eta^{H};Entries",                        100,  -5.0,   5.0);
    // --- Pseudorapidez de cada foton hijo ---
    auto h_gamma_eta = new TH1D("h_gamma_eta","Photon Pseudorapidity;#eta^{#gamma};Entries",                   100,  -5.0,   5.0);

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

                // --- 1. Masa post-fit ---
                double recoMass = p.getMass();
                h_mass->Fill(recoMass);

                // --- 2. pT y eta del Higgs ---
                double px  = p.getMomentum().x;
                double py  = p.getMomentum().y;
                double pz  = p.getMomentum().z;
                double pt  = std::sqrt(px*px + py*py);
                double eta = (pt > 0) ? std::asinh(pz / pt) : 0.0;
                h_pt->Fill(pt);
                h_eta->Fill(eta);

                // --- 3. Masa pre-fit y cinematica de los fotones hijos ---
                auto daughters = p.getParticles();
                if (daughters.size() >= 2) {
                    auto p1 = edm4hep::utils::p4(daughters[0], edm4hep::utils::UseEnergy);
                    auto p2 = edm4hep::utils::p4(daughters[1], edm4hep::utils::UseEnergy);
                    double prefitMass = (p1 + p2).M();
                    h_prefit->Fill(prefitMass);

                    // pT y eta de cada foton
                    for (int d = 0; d < 2; ++d) {
                        double gpx  = daughters[d].getMomentum().x;
                        double gpy  = daughters[d].getMomentum().y;
                        double gpz  = daughters[d].getMomentum().z;
                        double gpt  = std::sqrt(gpx*gpx + gpy*gpy);
                        double geta = (gpt > 0) ? std::asinh(gpz / gpt) : 0.0;
                        h_gamma_pt->Fill(gpt);
                        h_gamma_eta->Fill(geta);
                    }
                }

                // --- 4. MC Truth y resolucion ---
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
    std::cout << "  - Post-fit entries:   " << h_mass->GetEntries()     << std::endl;
    std::cout << "  - Pre-fit entries:    " << h_prefit->GetEntries()   << std::endl;
    std::cout << "  - MC Truth entries:   " << h_gen_mass->GetEntries() << std::endl;
    std::cout << "  - Higgs pT entries:   " << h_pt->GetEntries()       << std::endl;
    std::cout << "  - Higgs eta entries:  " << h_eta->GetEntries()      << std::endl;

    h_mass->Write();
    h_prefit->Write();
    h_gen_mass->Write();
    h_res->Write();
    h_pt->Write();
    h_gamma_pt->Write();
    h_eta->Write();
    h_gamma_eta->Write();
    hfile->Close();
    return 0;
}
