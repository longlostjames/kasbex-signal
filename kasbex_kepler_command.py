#!/usr/bin/env python
"""Write a command for kasbex_iop_signal.py to ingest.

Written to /path/to/dir/kepler-20250731-124815.log

Usage:
python kasbex_kepler_command.py <dir> command:<cmd> <k1>:<v1> ...
cmd: scan, rhi, ppi
python kasbex_kepler_command.py /path/to/dir/ command:scan azimuth:22 range:44
python kasbex_kepler_command.py /path/to/dir/ command:rhi start_angle:20 angle_span:10 fixed_angle:2 deg_per_sec:0.5 nave:2
python kasbex_kepler_command.py /path/to/dir/ command:pph start_angle:20 angle_span:10 fixed_angle:2 deg_per_sec:0.5 nave:2
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

    for arg in args:
        try:
            _ = float(cmd_dict.pop(arg))
        except:
            raise ValueError(f"Arg not present or wrong format: {arg}")
    assert len(cmd_dict) == 0, f'Commands not expected {cmd_dict}'

    file_command = ' '.join(pairs)
    print(f'{filename}: {file_command}')
    filepath.write_text(file_command, newline='')


if __name__ == '__main__':
    main()