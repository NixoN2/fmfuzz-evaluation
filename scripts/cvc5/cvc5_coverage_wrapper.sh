#!/bin/bash
# Wrapper script for cvc5 that ensures coverage agent is loaded via LD_PRELOAD.
# This is necessary because typefuzz (yinyang) spawns solvers with empty/stripped
# environment, which drops LD_PRELOAD.
#
# Usage: Set CVC5_REAL_PATH and COV_AGENT_PATH before running typefuzz
#   export CVC5_REAL_PATH=/path/to/cvc5
#   export COV_AGENT_PATH=/path/to/libcov_agent.so
#   typefuzz --solver /path/to/cvc5_coverage_wrapper.sh ...

# Get the real cvc5 path (set by fuzzer, or default to cvc5 in same dir)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CVC5_BINARY="${CVC5_REAL_PATH:-${SCRIPT_DIR}/build/bin/cvc5}"

# Get coverage agent path
AGENT="${COV_AGENT_PATH:-${SCRIPT_DIR}/build/libcov_agent.so}"

# Ensure LD_PRELOAD includes our agent
if [ -f "$AGENT" ]; then
    if [ -n "$LD_PRELOAD" ]; then
        export LD_PRELOAD="${AGENT}:${LD_PRELOAD}"
    else
        export LD_PRELOAD="${AGENT}"
    fi
fi

# COVERAGE_SHM_NAME should already be set by the fuzzer
# Just pass it through (it's inherited from parent if set)

# Execute the real cvc5 with all arguments
exec "$CVC5_BINARY" "$@"

