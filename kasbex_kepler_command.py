#!/usr/bin/env python
"""Write a command for kasbex_iop_signal.py to ingest.

Written to /path/to/dir/kepler-YYYYMMDD-HHMMSS.log

Usage:
python kasbex_kepler_command.py <dir> command:<cmd> <k1>:<v1> ...
cmd: scan, rhi, ppi

Examples:
python kasbex_kepler_command.py /path/to/dir/ command:scan azimuth:22 range:44
python kasbex_kepler_command.py /path/to/dir/ command:rhi start_angle:20 angle_span:10 fixed_angle:2 deg_per_sec:0.5 nave:2
python kasbex_kepler_command.py /path/to/dir/ command:ppi start_angle:20 angle_span:10 fixed_angle:2 deg_per_sec:0.5 nave:2

Optional:
  delay:<seconds>   # Delay (float, in seconds) before issuing the command

Example with delay:
python kasbex_kepler_command.py /path/to/dir/ command:rhi start_angle:20 angle_span:10 fixed_angle:2 deg_per_sec:0.5 nave:2 delay:5
"""
import sys
import datetime as dt
from pathlib import Path


def main():
    output_dir = sys.argv[1]
    pairs = sys.argv[2:]
    now = dt.datetime.now()
    filename = now.strftime("kepler-%Y%m%d-%H%M%S.log")
    filepath = Path(output_dir, filename)
    try:
        # Ensure that args are correct
        cmd_dict = {key.strip(): value.strip() for key, value in (pair.split(':') for pair in pairs)}
        kepler_cmd = cmd_dict.pop("command")
    except:
        raise Exception("Invalid args, note no space between key, colon and value")
    if kepler_cmd == "scan":
        args = ['azimuth', 'range']
    elif kepler_cmd in ["rhi", "ppi"]:
        args = ['start_angle', 'angle_span', 'fixed_angle', 'deg_per_sec', 'nave']
    else:
        raise ValueError(f"Invalid kepler command: {kepler_cmd}")

    # Optionally allow a 'delay' key (float, optional)
    delay = cmd_dict.pop("delay", None)
    if delay is not None:
        try:
            _ = float(delay)
        except:
            raise ValueError("delay must be a float (seconds)")

    for arg in args:
        try:
            _ = float(cmd_dict.pop(arg))
        except:
            raise ValueError(f"Arg not present or wrong format: {arg}")
    assert len(cmd_dict) == 0, f'Commands not expected {cmd_dict}'

    # Reconstruct file_command, including delay if present
    file_command = ' '.join(pairs)
    print(f'{filename}: {file_command}')
    filepath.write_text(file_command)


if __name__ == '__main__':
    main()