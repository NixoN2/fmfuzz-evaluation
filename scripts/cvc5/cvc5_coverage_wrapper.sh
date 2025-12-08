#!/bin/bash
# Wrapper script for cvc5 that ensures coverage agent is loaded via LD_PRELOAD.
# This is necessary because typefuzz (yinyang) spawns solvers with STRIPPED
# environment, which drops LD_PRELOAD and all custom env vars.
#
# CRITICAL: LD_PRELOAD requires ABSOLUTE paths - relative paths fail because
# the dynamic linker resolves them relative to cvc5's working directory at exec time.

set -euo pipefail

# Resolve absolute paths based on wrapper location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Try to find project root (wrapper is in scripts/cvc5/)
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"  # scripts/cvc5 -> scripts -> root

# Try multiple possible locations for cvc5 and agent
CVC5_BINARY=""
AGENT=""

for CVC5_CANDIDATE in \
    "${SCRIPT_DIR}/../build/bin/cvc5" \
    "${PROJECT_ROOT}/cvc5/build/bin/cvc5" \
    "./build/bin/cvc5" \
    "../cvc5/build/bin/cvc5"
do
    if [ -f "$CVC5_CANDIDATE" ]; then
        CVC5_BINARY="$(cd "$(dirname "$CVC5_CANDIDATE")" && pwd)/$(basename "$CVC5_CANDIDATE")"
        break
    fi
done

for AGENT_CANDIDATE in \
    "${SCRIPT_DIR}/../build/libcov_agent.so" \
    "${PROJECT_ROOT}/cvc5/build/libcov_agent.so" \
    "./build/libcov_agent.so" \
    "../cvc5/build/libcov_agent.so"
do
    if [ -f "$AGENT_CANDIDATE" ]; then
        AGENT="$(cd "$(dirname "$AGENT_CANDIDATE")" && pwd)/$(basename "$AGENT_CANDIDATE")"
        break
    fi
done

# Sanity checks
if [ -z "$CVC5_BINARY" ] || [ ! -f "$CVC5_BINARY" ]; then
    echo "[WRAPPER] ERROR: cvc5 not found at $CVC5_BINARY" >&2
    exit 1
fi

if [ -z "$AGENT" ] || [ ! -f "$AGENT" ]; then
    echo "[WRAPPER] ERROR: agent not found at $AGENT" >&2
    exit 1
fi

# CRITICAL: Use ABSOLUTE path in LD_PRELOAD (relative paths fail!)
export LD_PRELOAD="$AGENT${LD_PRELOAD:+:$LD_PRELOAD}"

# Preserve COVERAGE_SHM_NAME (typefuzz does propagate this one)
[ -n "${COVERAGE_SHM_NAME:-}" ] || export COVERAGE_SHM_NAME="fallback_$(date +%s)"

# Debug logging
echo "[WRAPPER] PID=$$ LD_PRELOAD=$LD_PRELOAD COVERAGE_SHM_NAME=$COVERAGE_SHM_NAME $CVC5_BINARY $@" >> /tmp/wrapper_calls.log

exec "$CVC5_BINARY" "$@"

