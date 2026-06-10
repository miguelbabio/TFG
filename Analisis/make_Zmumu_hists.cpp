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
#include <vector>

/**
 * Main analysis executable to produce histograms from EDM4hep files.
 * Reconstructs Z -> mu mu candidates and compares post-fit, pre-fit and MC truth masses.
 */
int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cout << "Usage: ./make_Z_hists <input.root> <collection_name> [output.root]" << std::endl;
        std::cout << "  collection_name: typically 'Zs_New'" << std::endl;
        return 1;
    }
    std::string inputfile  = argv[1];
    std::string colName    = argv[2];
    std::string outputfile = (argc >= 4) ? argv[3] : "Z_histograms_output.root";

    podio::ROOTReader reader;
    try {
        reader.openFile(inputfile);
    } catch (const std::exception& e) {
        std::cerr << "Error opening file: " << e.what() << std::endl;
        return 1;
    }

    // --- Histogram Initialization ---
    auto hfile = std::make_unique<TFile>(outputfile.c_str(), "RECREATE");

    // 1. Post-fit: Mass stored in the ReconstructedParticle object
    auto h_mass     = new TH1D("h_mass",     "Post-fit Mass;M_{Z} [GeV];Entries",                    100, 70.0, 110.0);
    // 2. Pre-fit: Mass calculated manually by summing daughter 4-vectors
    auto h_prefit   = new TH1D("h_prefit",   "Pre-fit Mass (Daughter Sum);M_{#mu#mu} [GeV];Entries", 100, 50.0, 130.0);
    // 3. MC Truth
    auto h_gen_mass = new TH1D("h_gen_mass", "Generated (MC Truth) Mass;M_{Z} [GeV];Entries",        100, 70.0, 110.0);
    // 4. Resolution: difference between reconstructed and true mass
    auto h_res      = new TH1D("h_res",      "Mass Resolution;M_{reco} - M_{gen} [GeV];Entries",     100, -10.0, 10.0);

    unsigned int nEvents = reader.getEntries("events");
    std::cout << "[INFO] Processing " << nEvents << " events from collection '" << colName << "'..." << std::endl;

    for (unsigned int i = 0; i < nEvents; ++i) {
        auto event = podio::Frame(reader.readEntry("events", i));
        try {
            const auto& particles = event.get<edm4hep::ReconstructedParticleCollection>(colName);

            const edm4hep::RecoMCParticleLinkCollection* associations = nullptr;
            try {
                associations = &event.get<edm4hep::RecoMCParticleLinkCollection>("RecoMCTruthLink");
            } catch (...) { /* Associations might not exist in all files */ }

            for (const auto& p : particles) {
                // --- 1. Post-fit mass ---
                double recoMass = p.getMass();
                h_mass->Fill(recoMass);

                // --- 2. Pre-fit mass (sum of muon daughters) ---
                auto daughters = p.getParticles();
                if (daughters.size() >= 2) {
                    auto p1 = edm4hep::utils::p4(daughters[0], edm4hep::utils::UseEnergy);
                    auto p2 = edm4hep::utils::p4(daughters[1], edm4hep::utils::UseEnergy);
                    double prefitMass = (p1 + p2).M();
                    h_prefit->Fill(prefitMass);
                }

                // --- 3 & 4. MC Truth and resolution ---
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
    std::cout << "  - Post-fit Entries:  " << h_mass->GetEntries()    << std::endl;
    std::cout << "  - Pre-fit Entries:   " << h_prefit->GetEntries()   << std::endl;
    std::cout << "  - MC Truth Entries:  " << h_gen_mass->GetEntries() << std::endl;

    h_mass->Write();
    h_prefit->Write();
    h_gen_mass->Write();
    h_res->Write();
    hfile->Close();
    return 0;
}
