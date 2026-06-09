from Gaudi.Configuration import INFO
from k4FWCore import ApplicationMgr, IOSvc
from Configurables import (
    RecoParticleFilter,
    GammaGammaCandidateFinder,    # <- mismo Configurable, distinta configuración
    EventDataSvc,
    AuditorSvc,
    AlgTimingAuditor,
)

iosvc = IOSvc()

# Filter muons
muon_filter = RecoParticleFilter("MuonFilter")
muon_filter.PDG = 13                              # Muon PDG ID
muon_filter.MinE = 0.5
muon_filter.InputCollection = ["PandoraPFOs"]
muon_filter.OutputCollection = ["FilteredMuons"]

# Use GammaGammaCandidateFinder as a generic pair finder, fed with muons
muon_muon_finder = GammaGammaCandidateFinder("MuonMuonFinder")  # nombre de instancia descriptivo
muon_muon_finder.InputCollection = muon_filter.OutputCollection  # entra muones, no fotones
muon_muon_finder.OutputCollection = ["MuonMuonCandidates_Z_New"]
muon_muon_finder.ResonancePDG = 23
muon_muon_finder.ResonanceMass = 91.1879
muon_muon_finder.MaxDeltaM = 10.0
muon_muon_finder.MinFitProbability = 0.001
muon_muon_finder.Fitter = "OPALFitter"

# Filter Z candidates
Z_filter = RecoParticleFilter("ZFilter")
Z_filter.PDG = 23
Z_filter.InputCollection = muon_muon_finder.OutputCollection
Z_filter.OutputCollection = ["Zs_New"]

iosvc.Output = "Z_candidates.root"
iosvc.outputCommands = [
    "drop *",
    "keep PandoraPFOs",
    "keep PandoraPFOs_PID_TOFEstimators*",
    "keep EcalBarrelCollectionRec",
    "keep MuonMuon*",
    "keep FilteredMuons",
    "keep *_New",
    "keep MCParticles",
    "drop *_startVertices",
    "drop *Eta*",
]

auditorSvc = AuditorSvc()
auditorSvc.Auditors = [AlgTimingAuditor()]

app_mgr = ApplicationMgr(
    TopAlg=[muon_filter, muon_muon_finder, Z_filter],
    EvtSel="NONE",
    EvtMax=-1,
    ExtSvc=[EventDataSvc(), auditorSvc],
    OutputLevel=INFO,
)
app_mgr.AuditAlgorithms = True
app_mgr.AuditTools = True
app_mgr.AuditServices = True
