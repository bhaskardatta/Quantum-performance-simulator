#!/bin/zsh
# Helper script to run PQC tests with the correct library path

export DYLD_LIBRARY_PATH=/usr/local/lib:$DYLD_LIBRARY_PATH
python test_pqc_channel.py
