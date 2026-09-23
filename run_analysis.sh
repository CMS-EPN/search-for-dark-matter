#!/usr/bin/env bash
# Execute the analysis notebooks, resuming automatically after network drops.
#
# Why this exists: a full run pulls tens of GB from the CERN XRootD redirector
# over minutes to hours. dpoa_io retries individual files (6 attempts, ~310 s of
# exponential backoff), but an outage longer than that fails a whole dataset and
# aborts the notebook. Because every processed dataset is cached to
# output_raw/*.parquet, simply re-running the notebook resumes where it stopped
# -- so the right response to an abort is to run it again, not to start over.
#
# Usage:  ./run_analysis.sh [Single_Lepton] [All_Hadronic] ...
#         MAX_ATTEMPTS=10 ./run_analysis.sh Single_Lepton
set -u
cd "$(dirname "$0")"

MAX_ATTEMPTS="${MAX_ATTEMPTS:-8}"
COOLDOWN="${COOLDOWN:-120}"          # seconds to wait for the link to recover
PORT_WAIT="${PORT_WAIT:-14400}"      # max seconds to wait for XRootD to be reachable

# XRootD speaks TCP 1094. Many networks (corporate, hotel, some ISPs) drop
# everything outside the usual web ports, and then every single file open fails
# after its full retry budget -- burning ~15 minutes of attempts to rediscover
# that the network is down. Check the port first and simply wait for it, so an
# attempt is only spent when there is a real chance of it working, and the run
# restarts within a minute of the connection coming back.
wait_for_xrootd() {
  local waited=0
  if timeout 10 bash -c 'exec 3<>/dev/tcp/eospublic.cern.ch/1094' 2>/dev/null; then
    return 0
  fi
  echo "--- XRootD (eospublic.cern.ch:1094) is not reachable."
  if timeout 10 bash -c 'exec 3<>/dev/tcp/eospublic.cern.ch/443' 2>/dev/null; then
    echo "--- but port 443 to the same host answers: this is a network/firewall"
    echo "--- block on port 1094, not an outage at CERN. See README.md."
  else
    echo "--- port 443 is unreachable too: the connection itself is down."
  fi
  echo "--- waiting for it (checking every 60 s, up to ${PORT_WAIT}s)..."
  while [ "$waited" -lt "$PORT_WAIT" ]; do
    sleep 60; waited=$((waited + 60))
    if timeout 10 bash -c 'exec 3<>/dev/tcp/eospublic.cern.ch/1094' 2>/dev/null; then
      echo "--- XRootD reachable again after ${waited}s ($(date -Is)); resuming."
      return 0
    fi
  done
  echo "--- still unreachable after ${PORT_WAIT}s; giving up." >&2
  return 1
}
NOTEBOOKS=("${@:-Single_Lepton All_Hadronic}")
[ $# -gt 0 ] && NOTEBOOKS=("$@")

for nb in "${NOTEBOOKS[@]}"; do
  echo "=================================================================="
  echo "### $nb -- started $(date -Is)"
  echo "=================================================================="
  cp "$nb.ipynb" "_run_$nb.ipynb"
  ok=0
  for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
    echo "--- attempt $attempt/$MAX_ATTEMPTS  $(date -Is)"
    wait_for_xrootd || { echo "### aborting: no XRootD connectivity" >&2; exit 2; }
    # systemd-inhibit keeps the machine awake: an earlier run died because the
    # laptop suspended mid-dataset.
    systemd-inhibit --what=idle:sleep:handle-lid-switch \
        --why="CMS Open Data analysis run" --mode=block \
      jupyter nbconvert --to notebook --execute --inplace \
        --ExecutePreprocessor.timeout=28800 "_run_$nb.ipynb"
    rc=$?
    if [ $rc -eq 0 ]; then ok=1; break; fi
    n=$(ls output_raw/*.parquet 2>/dev/null | wc -l)
    echo "--- attempt $attempt failed (exit $rc); $n datasets cached so far."
    if [ "$attempt" -lt "$MAX_ATTEMPTS" ]; then
      echo "--- waiting ${COOLDOWN}s for the connection, then resuming."
      sleep "$COOLDOWN"
    fi
  done
  mv "_run_$nb.ipynb" "runs/${nb}_run.ipynb"
  if [ $ok -eq 1 ]; then
    echo "### $nb OK at $(date -Is)"
  else
    echo "### $nb STILL FAILING after $MAX_ATTEMPTS attempts at $(date -Is)" >&2
    exit 1
  fi
done
echo "ALL DONE $(date -Is)"
