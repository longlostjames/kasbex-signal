# KASBEX Signal Processing

This repository contains the signal processing and radar control scripts for the KASBEX campaign.

## Overview

The KASBEX project involves radar scanning operations with automated storm tracking and default operational modes. This codebase provides:

- **Automated radar control** based on command files
- **Storm tracking and RHI scanning** capabilities
- **Default operational modes** when no active targets are detected
- **Signal processing integration** with the METEK radar system

## Files

### Main Scripts

- `kasbex_iop_signal.py` - Main Python control script for automated radar operations
- `kepler_scan` - Perl script for executing different types of radar scans (PPI, RHI, FIX, etc.)

## Usage

### Running the Main Control Script

```bash
python kasbex_iop_signal.py
```

The script will:
1. Monitor for command files in `/home/data/kasbex/kasbex-command/`
2. Execute storm tracking RHI scans when "scan" commands are detected
3. Run default FIX scans when no active targets are present
4. Handle signal interruption for clean process termination

### Manual Radar Scanning

The `kepler_scan` script can be used for manual radar operations:

```bash
# RHI scan
./kepler_scan --scan RHI --min_angle 0 --angle_span 90 --fixed_angle 246 --deg_per_sec 2.0 --nave 2

# PPI scan
./kepler_scan --scan PPI --min_angle 200 --angle_span 115 --fixed_angle 0 --deg_per_sec 2.0 --nave 2

# Fixed pointing scan
./kepler_scan --scan FIX --fixed_angle 0 --dwelltime 300 --nave 270
```

## Configuration

### Key Parameters

- `scan_rate` - Default scanning speed (deg/sec)
- `max_range` - Maximum operational range (km)
- `north_angle` - Calibration offset for true north (55.7°)
- `cmd_path` - Path to command files directory

### Signal Processing

The system integrates with METEK M36S radar hardware through:
- `ttaerotech` Perl library for hardware control
- `get_datasavingNprocessing` for data acquisition
- `kill_datasaving` for stopping data collection

## Dependencies

### Python
- numpy
- threading
- subprocess
- logging
- signal handling

### Perl
- Getopt::Long
- ttaerotech (custom library)

## Author

Chris Walden, STFC/NCAS
Last modified: 14-07-2025

## Campaign Information

This code was developed for the KASBEX campaign, building on experience from:
- CCREST-M campaign (February 2024)
- Previous WOEST operations

The north angle calibration (55.7°) was established during the CCREST-M campaign in February 2024.
