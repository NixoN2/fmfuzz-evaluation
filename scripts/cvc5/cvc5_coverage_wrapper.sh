#!/bin/bash
# Wrapper script for cvc5 that ensures coverage agent is loaded via LD_PRELOAD.
# This is necessary because typefuzz (yinyang) spawns solvers with STRIPPED
# environment, which drops LD_PRELOAD and all custom env vars.
#
# IMPORTANT: Paths are HARDCODED because typefuzz doesn't pass env vars!

# Debug logging (check /tmp/wrapper*.log after fuzzing)
echo "[WRAPPER] Called at $(date) with args: $@" >> /tmp/wrapper_calls.log
echo "[WRAPPER] CWD: $(pwd)" >> /tmp/wrapper_calls.log
echo "[WRAPPER] COVERAGE_SHM_NAME=${COVERAGE_SHM_NAME:-UNSET}" >> /tmp/wrapper_calls.log

# HARDCODED PATHS - typefuzz strips env vars, so we can't rely on CVC5_REAL_PATH etc.
# These paths are relative to typical GitHub Actions working directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Try multiple possible locations for cvc5 and agent
for CVC5_CANDIDATE in \
    "${SCRIPT_DIR}/build/bin/cvc5" \
    "${SCRIPT_DIR}/../build/bin/cvc5" \
    "./build/bin/cvc5" \
    "../cvc5/build/bin/cvc5" \
    "/home/runner/work/fmfuzz-evaluation/fmfuzz-evaluation/cvc5/build/bin/cvc5"
do
    if [ -f "$CVC5_CANDIDATE" ]; then
        CVC5_BINARY="$CVC5_CANDIDATE"
        break
    fi
done

for AGENT_CANDIDATE in \
    "${SCRIPT_DIR}/build/libcov_agent.so" \
    "${SCRIPT_DIR}/../build/libcov_agent.so" \
    "./build/libcov_agent.so" \
    "../cvc5/build/libcov_agent.so" \
    "/home/runner/work/fmfuzz-evaluation/fmfuzz-evaluation/cvc5/build/libcov_agent.so"
do
    if [ -f "$AGENT_CANDIDATE" ]; then
        AGENT="$AGENT_CANDIDATE"
        break
    fi
done

echo "[WRAPPER] CVC5_BINARY=${CVC5_BINARY:-NOT_FOUND}" >> /tmp/wrapper_calls.log
echo "[WRAPPER] AGENT=${AGENT:-NOT_FOUND}" >> /tmp/wrapper_calls.log

# Validate paths
if [ -z "$CVC5_BINARY" ] || [ ! -f "$CVC5_BINARY" ]; then
    echo "[WRAPPER] ERROR: cvc5 binary not found!" >> /tmp/wrapper_calls.log
    echo "[WRAPPER] ERROR: cvc5 binary not found!" >&2
    exit 1
fi

if [ -z "$AGENT" ] || [ ! -f "$AGENT" ]; then
    echo "[WRAPPER] ERROR: Coverage agent not found!" >> /tmp/wrapper_calls.log
    echo "[WRAPPER] ERROR: Coverage agent not found!" >&2
    exit 1
fi

# Set LD_PRELOAD to load coverage agent
export LD_PRELOAD="${AGENT}:${LD_PRELOAD:-}"
echo "[WRAPPER] LD_PRELOAD set to: $LD_PRELOAD" >> /tmp/wrapper_calls.log

# Execute the real cvc5
echo "[WRAPPER] Executing: $CVC5_BINARY $@" >> /tmp/wrapper_calls.log
exec "$CVC5_BINARY" "$@"

