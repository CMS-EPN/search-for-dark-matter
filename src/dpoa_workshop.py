import numpy as np
import awkward as ak

import json

nanoaod_filenames = {}



#nanoaod_filenames['signal_M2000'] = ['https://opendata.cern.ch/record/75156/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_ZprimeToTT_M2000_W20_TuneCP2_PSweights_13TeV-madgraph-pythiaMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_270000_file_index.txt',
#                             'https://opendata.cern.ch/record/75156/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_ZprimeToTT_M2000_W20_TuneCP2_PSweights_13TeV-madgraph-pythiaMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_280000_file_index.txt'
#                            ]

#nanoaod_filenames['Wjets'] = ['https://opendata.cern.ch/record/69747/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_270000_file_index.txt', 
#                              'https://opendata.cern.ch/record/69747/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_280000_file_index.txt',
#                              'https://opendata.cern.ch/record/69747/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_70000_file_index.txt'
#                             ]

#nanoaod_filenames['tthadronic'] = ['https://opendata.cern.ch/record/67841/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTToHadronic_TuneCP5_13TeV-powheg-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_130000_file_index.txt', 
#                                   'https://opendata.cern.ch/record/67841/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTToHadronic_TuneCP5_13TeV-powheg-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_270000_file_index.txt', 
#                                   'https://opendata.cern.ch/record/67841/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTToHadronic_TuneCP5_13TeV-powheg-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_280000_file_index.txt',
#                                   'https://opendata.cern.ch/record/67841/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTToHadronic_TuneCP5_13TeV-powheg-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_70000_file_index.txt'
#                                  ]

#nanoaod_filenames['ttleptonic'] = ['https://opendata.cern.ch/record/67801/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_120000_file_index.txt', 
#                               'https://opendata.cern.ch/record/67801/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_130000_file_index.txt',
#                               'https://opendata.cern.ch/record/67801/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_270000_file_index.txt',
#                               'https://opendata.cern.ch/record/67801/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_280000_file_index.txt',
#                               'https://opendata.cern.ch/record/67801/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_70000_file_index.txt'
#                              ]

nanoaod_filenames['met'] = ['https://opendata.cern.ch/record/30559/file_index/CMS_Run2016H_MET_NANOAOD_UL2016_MiniAODv2_NanoAODv9-v1_120000_file_index.txt',
                                'https://opendata.cern.ch/record/30559/file_index/CMS_Run2016H_MET_NANOAOD_UL2016_MiniAODv2_NanoAODv9-v1_280000_file_index.txt',
                                'https://opendata.cern.ch/record/30559/file_index/CMS_Run2016H_MET_NANOAOD_UL2016_MiniAODv2_NanoAODv9-v1_70000_file_index.txt'
                                 ]

nanoaod_filenames['SingleMuon'] = ['https://opendata.cern.ch/record/30563/file_index/CMS_Run2016H_SingleMuon_NANOAOD_UL2016_MiniAODv2_NanoAODv9-v1_120000_file_index.txt',
                               'https://opendata.cern.ch/record/30563/file_index/CMS_Run2016H_SingleMuon_NANOAOD_UL2016_MiniAODv2_NanoAODv9-v1_1210000_file_index.txt',
                               'https://opendata.cern.ch/record/30563/file_index/CMS_Run2016H_SingleMuon_NANOAOD_UL2016_MiniAODv2_NanoAODv9-v1_130000_file_index.txt',
                               'https://opendata.cern.ch/record/30563/file_index/CMS_Run2016H_SingleMuon_NANOAOD_UL2016_MiniAODv2_NanoAODv9-v1_280000_file_index.txt',
                               'https://opendata.cern.ch/record/30563/file_index/CMS_Run2016H_SingleMuon_NANOAOD_UL2016_MiniAODv2_NanoAODv9-v1_70000_file_index.txt'
                                 ]

nanoaod_filenames['SingleElectron'] = ['https://opendata.cern.ch/record/30562/file_index/CMS_Run2016H_SingleElectron_NANOAOD_UL2016_MiniAODv2_NanoAODv9-v1_120000_file_index.txt',
                               'https://opendata.cern.ch/record/30562/file_index/CMS_Run2016H_SingleElectron_NANOAOD_UL2016_MiniAODv2_NanoAODv9-v1_270000_file_index.txt',
                               'https://opendata.cern.ch/record/30562/file_index/CMS_Run2016H_SingleElectron_NANOAOD_UL2016_MiniAODv2_NanoAODv9-v1_280000_file_index.txt',
                               'https://opendata.cern.ch/record/30562/file_index/CMS_Run2016H_SingleElectron_NANOAOD_UL2016_MiniAODv2_NanoAODv9-v1_70000_file_index.txt'
                                 ]


# --- ttbar ---
nanoaod_filenames['ttbar-semileptonic'] = [
  "https://opendata.cern.ch/record/67993/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_120000_file_index.txt",
  "https://opendata.cern.ch/record/67993/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_130000_file_index.txt",
  "https://opendata.cern.ch/record/67993/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_270000_file_index.txt",
  "https://opendata.cern.ch/record/67993/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_280000_file_index.txt",
  "https://opendata.cern.ch/record/67993/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_70000_file_index.txt"
]



#nanoaod_filenames['ttbar-hadronic'] = ['https://opendata.cern.ch/record/67841/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTToHadronic_TuneCP5_13TeV-powheg-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_130000_file_index.txt', 
                                   #'https://opendata.cern.ch/record/67841/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTToHadronic_TuneCP5_13TeV-powheg-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_270000_file_index.txt', 
                    #               'https://opendata.cern.ch/record/67841/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTToHadronic_TuneCP5_13TeV-powheg-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_280000_file_index.txt',
                                  # 'https://opendata.cern.ch/record/67841/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTToHadronic_TuneCP5_13TeV-powheg-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_70000_file_index.txt'
                                #  ]


# --- single top ---
nanoaod_filenames['t-channel-top'] = [
  "https://opendata.cern.ch/record/64763/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_ST_t-channel_top_4f_InclusiveDecays_TuneCP5CR2_13TeV-powheg-madspin-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_100000_file_index.txt",
  "https://opendata.cern.ch/record/64763/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_ST_t-channel_top_4f_InclusiveDecays_TuneCP5CR2_13TeV-powheg-madspin-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_230000_file_index.txt",
  "https://opendata.cern.ch/record/64763/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_ST_t-channel_top_4f_InclusiveDecays_TuneCP5CR2_13TeV-powheg-madspin-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_2430000_file_index.txt",
  "https://opendata.cern.ch/record/64763/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_ST_t-channel_top_4f_InclusiveDecays_TuneCP5CR2_13TeV-powheg-madspin-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_2500000_file_index.txt",
  "https://opendata.cern.ch/record/64763/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_ST_t-channel_top_4f_InclusiveDecays_TuneCP5CR2_13TeV-powheg-madspin-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_250000_file_index.txt"
]


#nanoaod_filenames['t-channel-antitop'] = [
 # "https://opendata.cern.ch/record/64669/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_ST_t-channel_antitop_4f_InclusiveDecays_TuneCP5up_13TeV-powheg-madspin-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_100000_file_index.txt",
  #"https://opendata.cern.ch/record/64669/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_ST_t-channel_antitop_4f_InclusiveDecays_TuneCP5up_13TeV-powheg-madspin-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_230000_file_index.txt",
  #"https://opendata.cern.ch/record/64669/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_ST_t-channel_antitop_4f_InclusiveDecays_TuneCP5up_13TeV-powheg-madspin-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_2430000_file_index.txt",
  #"https://opendata.cern.ch/record/64669/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_ST_t-channel_antitop_4f_InclusiveDecays_TuneCP5up_13TeV-powheg-madspin-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_2500000_file_index.txt",
  #"https://opendata.cern.ch/record/64669/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_ST_t-channel_antitop_4f_InclusiveDecays_TuneCP5up_13TeV-powheg-madspin-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_250000_file_index.txt"
#]


nanoaod_filenames["t-channel-antitop"] = [
"https://opendata.cern.ch/record/64663/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_ST_t-channel_antitop_4f_InclusiveDecays_TuneCP5CR2_13TeV-powheg-madspin-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_2500000_file_index.txt"
]


#--Falla--
#nanoaod_filenames['tW-top'] = [
 # "https://opendata.cern.ch/record/64895/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_ST_tW_top_5f_NoFullyHadronicDecays_TuneCP5_13TeV-powheg-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_2520000_file_index.txt"
#]



# --- ttV ---
nanoaod_filenames['ttW'] = [
  "https://opendata.cern.ch/record/68073/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTWJetsToLNu_TuneCP5_13TeV-amcatnloFXFX-madspin-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_130000_file_index.txt",
  "https://opendata.cern.ch/record/68073/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTWJetsToLNu_TuneCP5_13TeV-amcatnloFXFX-madspin-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_270000_file_index.txt",
  "https://opendata.cern.ch/record/68073/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTWJetsToLNu_TuneCP5_13TeV-amcatnloFXFX-madspin-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_280000_file_index.txt",
  "https://opendata.cern.ch/record/68073/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTWJetsToLNu_TuneCP5_13TeV-amcatnloFXFX-madspin-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_70000_file_index.txt"
]

#--Falla--
#nanoaod_filenames['ttZ'] = [
#  "https://opendata.cern.ch/record/68195/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTZToLLNuNu_M-10_TuneCP5up_13TeV-amcatnlo-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v2_2520000_file_index.txt",
#  "https://opendata.cern.ch/record/68195/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_TTZToLLNuNu_M-10_TuneCP5up_13TeV-amcatnlo-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v2_2530000_file_index.txt"
#]




# --- W+jets ---
nanoaod_filenames['WJets-HT400to600'] = [
  "https://opendata.cern.ch/record/69729/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_HT-400To600_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_120000_file_index.txt",
  "https://opendata.cern.ch/record/69729/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_HT-400To600_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_130000_file_index.txt",
  "https://opendata.cern.ch/record/69729/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_HT-400To600_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_270000_file_index.txt",
  "https://opendata.cern.ch/record/69729/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_HT-400To600_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_280000_file_index.txt",
  "https://opendata.cern.ch/record/69729/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_HT-400To600_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_70000_file_index.txt"
]




nanoaod_filenames['WJets-HT100to200'] = [

  "https://opendata.cern.ch/record/69721/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_HT-100To200_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_120000_file_index.txt",

  "https://opendata.cern.ch/record/69721/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_HT-100To200_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_130000_file_index.txt",

  "https://opendata.cern.ch/record/69721/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_HT-100To200_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_270000_file_index.txt",

  "https://opendata.cern.ch/record/69721/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_HT-100To200_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_280000_file_index.txt",

  "https://opendata.cern.ch/record/69721/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_HT-100To200_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_70000_file_index.txt"
]


nanoaod_filenames['WJets-HT200to400'] = [

  "https://opendata.cern.ch/record/69725/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_HT-200To400_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_120000_file_index.txt",

  "https://opendata.cern.ch/record/69725/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_HT-200To400_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_130000_file_index.txt",

  "https://opendata.cern.ch/record/69725/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_HT-200To400_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_270000_file_index.txt",

  "https://opendata.cern.ch/record/69725/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_HT-200To400_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_280000_file_index.txt",

  "https://opendata.cern.ch/record/69725/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_HT-200To400_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_70000_file_index.txt"
]

nanoaod_filenames['WJets-HT70to100'] = [

  "https://opendata.cern.ch/record/69733/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_HT-70To100_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_120000_file_index.txt",

  "https://opendata.cern.ch/record/69733/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_HT-70To100_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_130000_file_index.txt",

  "https://opendata.cern.ch/record/69733/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_HT-70To100_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_270000_file_index.txt",

  "https://opendata.cern.ch/record/69733/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_HT-70To100_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_280000_file_index.txt",

  "https://opendata.cern.ch/record/69733/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WJetsToLNu_HT-70To100_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_70000_file_index.txt"
]



# --- Z(ll) ---
#nanoaod_filenames['DYJets-inclusive'] = [
 # "https://opendata.cern.ch/record/35541/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_DY2JetsToLL_M-50_MatchEWPDG20_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_120000_file_index.txt",
 # "https://opendata.cern.ch/record/35541/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_DY2JetsToLL_M-50_MatchEWPDG20_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_130000_file_index.txt",
 # "https://opendata.cern.ch/record/35541/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_DY2JetsToLL_M-50_MatchEWPDG20_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_270000_file_index.txt",
 # "https://opendata.cern.ch/record/35541/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_DY2JetsToLL_M-50_MatchEWPDG20_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_280000_file_index.txt",
 # "https://opendata.cern.ch/record/35541/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_DY2JetsToLL_M-50_MatchEWPDG20_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_70000_file_index.txt"
#]




nanoaod_filenames['DYJets-Zpt200'] = [
  "https://opendata.cern.ch/record/35675/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_DYJetsToLL_M-50_Zpt-200toInf_BPSFilter_TuneCP5_13TeV-madgraphMLM-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v2_260000_file_index.txt"
]


nanoaod_filenames['WW'] = [
  "https://opendata.cern.ch/record/72696/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WW_TuneCP5_13TeV-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_130000_file_index.txt",
  "https://opendata.cern.ch/record/72696/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WW_TuneCP5_13TeV-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_270000_file_index.txt",
  "https://opendata.cern.ch/record/72696/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WW_TuneCP5_13TeV-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_280000_file_index.txt",
  "https://opendata.cern.ch/record/72696/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_WW_TuneCP5_13TeV-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_70000_file_index.txt"
]

nanoaod_filenames['ZZ'] = [
  "https://opendata.cern.ch/record/75593/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_ZZ_TuneCP5_13TeV-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_130000_file_index.txt",
  "https://opendata.cern.ch/record/75593/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_ZZ_TuneCP5_13TeV-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_270000_file_index.txt",
  "https://opendata.cern.ch/record/75593/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_ZZ_TuneCP5_13TeV-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_280000_file_index.txt",
  "https://opendata.cern.ch/record/75593/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_ZZ_TuneCP5_13TeV-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_70000_file_index.txt"
]

nanoaod_filenames['Zvv'] = [
  "https://opendata.cern.ch/record/36174/file_index/CMS_mc_RunIISummer20UL16NanoAODv9_ggH_HToSSTo4l_lowctau_MH-500_MS-150_ctauS-100_TuneCP5_13TeV-powheg-pythia8_NANOAODSIM_106X_mcRun2_asymptotic_v17-v1_30000_file_index.txt"
]


#########################################################################################
def build_lumi_mask(lumifile, tree, verbose=False):
    # lumifile should be the name/path of the file
    good_luminosity_sections = ak.from_json(open(lumifile, 'rb'))

    # Pull out the good runs as integers
    good_runs = np.array(good_luminosity_sections.fields).astype(int)
    #good_runs

    # Get the good blocks as an awkward array
    # First loop over to get them as a list
    all_good_blocks = []
    for field in good_luminosity_sections.fields:
        all_good_blocks.append(good_luminosity_sections[field])

    # Turn the list into an awkward array
    all_good_blocks = ak.Array(all_good_blocks)
    all_good_blocks[11]

    # Assume that tree is a NanoAOD Events tree
    nevents = tree.num_entries
    if verbose:
        print(f"nevents: {nevents}")
        print()
        print("All good runs")
        print(good_runs)
        print()
        print("All good blocks")
        print(all_good_blocks)
        print()

    # Get the runs and luminosity blocks from the tree
    run = tree['run'].array()
    lumiBlock = tree['luminosityBlock'].array()

    if verbose:
        print("Runs from the tree")
        print(run)
        print()
        print("Luminosity blocks from the tree")
        print(lumiBlock)
        print()

    # ChatGPT helped me with this part!
    # Find index of values in arr2 if those values appear in arr1

    def find_indices(arr1, arr2):
        index_map = {value: index for index, value in enumerate(arr1)}
        return [index_map.get(value, -1) for value in arr2]

    # Get the indices that say where the good runs are in the lumi file
    # for the runs that appear in the tree
    good_runs_indices = find_indices(good_runs, run)

    # For each event, calculate the difference between the luminosity block for that event
    # and the good luminosity blocks for that run for that event
    diff = lumiBlock - all_good_blocks[good_runs_indices]

    if verbose:
        print("difference between event lumi blocks and the good lumi blocks")
        print(diff)
        print()

    # If the lumi block appears between any of those good block numbers, 
    # then one difference will be positive and the other will be negative
    # 
    # If it it outside of the range, both differences will be positive or 
    # both negative.
    #
    # The product will be negagive if the lumi block is in the range
    # and positive if it is not in the range
    prod_diff = ak.prod(diff, axis=2)

    if verbose:
        print("product of the differences")
        print(prod_diff)
        print()

    mask = ak.any(prod_diff<=0, axis=1)

    return mask

#############################################################################

def get_files_for_dataset(dataset, random=False, n=0):
    
    filelist_filename = f'FILE_LIST_{dataset}.txt'
    
    infile = open(filelist_filename)
    filenames = infile.readlines()
    
    if n<1:
        return filenames
    
    else:
        if random:
            subset = np.random.choice(filenames, n)
    
        else:
            subset = filenames[0:n]
        
        return subset
    
###############################################################################

def pretty_print(fields, fmt='40s', require=None, ignore=None):
    
    output = ""
    
    for f in fields:
        PASSED = True
        if require is not None:
            if type(require) != list:
                require = [require]
            PASSED = True
            for r in require:
                if f.find(r) < 0:
                    PASSED = False
        
        # Did not find a string and so skip
        if PASSED is False:
            continue
        
        if ignore is not None:
            if f.find(ignore) >= 0:
                continue
        
        if len(output) + len(f) <= 80:
            output += f"{f:{fmt}} "
        else:
            print(output)
            output = f"{f:{fmt}} "
    
    print(output)

