from Gaudi.Configuration import INFO
from k4FWCore import ApplicationMgr, IOSvc
from Configurables import (
    RecoParticleFilter,
    GammaGammaCandidateFinder,
    EventDataSvc,
    AuditorSvc,
    AlgTimingAuditor,
)

iosvc = IOSvc()

# Filter electrons
electron_filter = RecoParticleFilter("ElectronFilter")
electron_filter.PDG = 11                          # Electron PDG ID
electron_filter.MinE = 1.0                        # Minimo energia en GeV
electron_filter.InputCollection = ["PandoraPFOs"]
electron_filter.OutputCollection = ["FilteredElectrons"]

# Use GammaGammaCandidateFinder as generic pair finder, fed with electrons
electron_electron_finder = GammaGammaCandidateFinder("ElectronElectronFinder")
electron_electron_finder.InputCollection = electron_filter.OutputCollection
electron_electron_finder.OutputCollection = ["ElectronElectronCandidates_Z_New"]
electron_electron_finder.ResonancePDG = 23        # Z PDG ID
electron_electron_finder.ResonanceMass = 91.1879  # Masa del Z en GeV
electron_electron_finder.MaxDeltaM = 10.0
electron_electron_finder.MinFitProbability = 0.001
electron_electron_finder.Fitter = "OPALFitter"

# Filter Z->ee candidates
Z_ee_filter = RecoParticleFilter("ZeeFilter")
Z_ee_filter.PDG = 23
Z_ee_filter.InputCollection = electron_electron_finder.OutputCollection
Z_ee_filter.OutputCollection = ["Zee_New"]

iosvc.Output = "HZZ_ee_candidates.root"
iosvc.outputCommands = [
    "drop *",
    "keep PandoraPFOs",
    "keep ElectronElectron*",
    "keep FilteredElectrons",
    "keep *_New",
    "keep MCParticles",
    "drop *_startVertices",
    "drop *Eta*",
]

auditorSvc = AuditorSvc()
auditorSvc.Auditors = [AlgTimingAuditor()]

app_mgr = ApplicationMgr(
    TopAlg=[electron_filter, electron_electron_finder, Z_ee_filter],
    EvtSel="NONE",
    EvtMax=-1,
    ExtSvc=[EventDataSvc(), auditorSvc],
    OutputLevel=INFO,
)
app_mgr.AuditAlgorithms = True
app_mgr.AuditTools = True
app_mgr.AuditServices = True
