#!/usr/bin/env python

import time
import subprocess
import numpy as np
import os
import glob
import shutil
import threading
import signal
import sys
import datetime
import math
import logging
import termios
import tty


# Global variables to control the default process
running_default_process = False
running_fix = False
running_rhi = False
running_ppi = False
default_thread = None
default_process_pid = None  # To store the PID of the default process
scan_rate = 2.0
max_range = 40
cmd_path = "/home/data/kasbex/kasbex-command"
previous_cmd_files = set()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("kasbex_process.log")
    ]
)

def signal_handler(sig, frame):
    """
    Handle signals to interrupt the default process and terminate subprocesses cleanly.
    """
    global running_default_process, running_fix, running_rhi
    global subproc_fix

    logging.info("Signal received, attempting to stop processes...")

    if running_default_process:
        logging.info("Stopping default process...")
        running_default_process = False

        if running_fix and subproc_fix:
            logging.info("Terminating FIX scan subprocess...")
            try:
                subproc_fix.terminate()
                subproc_fix.wait(timeout=5)  # Wait for the process to terminate
                logging.info("FIX scan subprocess terminated successfully.")
            except subprocess.TimeoutExpired:
                logging.warning("FIX scan subprocess did not terminate in time. Forcing termination...")
                subproc_fix.kill()
                subproc_fix.wait()
            except Exception as e:
                logging.error(f"Error while terminating FIX scan subprocess: {e}")
            finally:
                running_fix = False

    logging.info("Signal handling complete.") #Exiting program.")
    #sys.exit(0)

def is_file_recent(file_path, sec):
    modification_time = os.path.getmtime(file_path)
    current_time = datetime.datetime.now().timestamp()
    time_difference = current_time - modification_time
    return time_difference <= sec


def latest_cmd_file(cmd_path):
    global previous_cmd_files
    pattern = "kepler*.log"
    current_files = set(glob.glob(os.path.join(cmd_path, pattern)))
    new_files = current_files - previous_cmd_files

    cmd_file = ""
    if new_files:
        latest_file = max(new_files, key=os.path.getmtime)
        if is_file_recent(latest_file, 900):
            shutil.copy(latest_file, os.path.join(cmd_path, 'latest_kepler_command.txt'))
            cmd_file = latest_file
    previous_cmd_files = current_files
    return cmd_file


def read_cmd_file(file_path):
    with open(file_path, "r") as file:
        line = file.readline()
        newline = line.rstrip().replace(': ', ':')
        pairs = newline.split()
        data = {key.strip(): value.strip() for key, value in (pair.split(':') for pair in pairs)}
    return data


def run_storm_rhis(storm_az,storm_range,scan_speed):
    delta_az = np.rad2deg(0.5/storm_range)
    if ( 40 > storm_range >= 30 ):
        elmax = 25.0;
        nscan = 4;
        dwell = False
        dotwice = True
    elif ( 20 <= storm_range < 30 ):
        elmax = 30.0;
        nscan = 6;
        dwell = False
        dotwice = False
    elif ( 10 <= storm_range < 20 ):
        elmax = 45.0;
        nscan = 4;
        dwell = False
        dotwice = False
    else:
        elmax = 90.0;
        nscan = 0;
        dwell = True
        dotwice = False
#    azimuths = stor_maz + np.arange(-(0.5+nscan/2),0.5+nscan/2,1.0)*delta_az;
    azimuths = storm_az + (np.arange(nscan) - nscan/2 + 0.5)*delta_az;
    print(azimuths-storm_az);

    if not dwell:    
        for i in np.arange(0,nscan,2):
            run_scan_rhi(0,elmax,azimuths[i],scan_speed,2)
            run_scan_rhi(elmax,-elmax,azimuths[i+1],scan_speed,2)
        if (dotwice):
            for i in np.arange(0,nscan,2):
                run_scan_rhi(0,elmax,azimuths[i],scan_speed,2)
                run_scan_rhi(elmax,-elmax,azimuths[i+1],scan_speed,2)


def run_scan_rhi(start_angle, angle_span, fixed_angle, deg_per_sec, nave):
    global running_rhi
    logging.info(f"Running RHI scan: start_angle={start_angle}, angle_span={angle_span}, fixed_angle={fixed_angle}, deg_per_sec={deg_per_sec}, nave={nave}")
    running_rhi = True
    subprocess.run([
        '/home/data/metek/m36s/srv_scripts/kepler_scan',
        '--scan', 'RHI',
        '--min_angle', str(start_angle),
        '--angle_span', str(angle_span),
        '--fixed_angle', str(fixed_angle),
        '--deg_per_sec', str(deg_per_sec),
        '--nave', str(nave)
    ])
    logging.info("Completed RHI scan")
    running_rhi = False

def run_scan_ppi(start_angle, angle_span, fixed_angle, deg_per_sec, nave):
    global running_ppi
    logging.info(f"Running PPI scan: start_angle={start_angle}, angle_span={angle_span}, fixed_angle={fixed_angle}, deg_per_sec={deg_per_sec}, nave={nave}")
    running_ppi = True
    subprocess.run([
        '/home/data/metek/m36s/srv_scripts/kepler_scan',
        '--scan', 'PPI',
        '--min_angle', str(start_angle),
        '--angle_span', str(angle_span),
        '--fixed_angle', str(fixed_angle),
        '--deg_per_sec', str(deg_per_sec),
        '--nave', str(nave)
    ])
    logging.info("Completed PPI scan")
    running_ppi = False

def default_process():
    """
    Run the default process when no new files are detected.
    """
    global running_default_process, default_process_pid
    global subproc_fix, running_fix
    global scan_rate

    logging.info("Starting default process...")
    running_default_process = True
    default_process_pid = threading.get_ident()

    try:
        #scan_speed = scan_rate
        #rhi_nave = int(5 * 54 * 0.3 / scan_speed)

        running_fix = True
        subproc_fix = subprocess.Popen(
            [
                '/home/data/metek/m36s/srv_scripts/kepler_scan',
                '--scan', 'FIX',
                '--dwelltime', '300',
                '--fixed_angle', '0',
                '--nave', '270'
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = subproc_fix.communicate()
        logging.info(f"Completed FIX scan. Output: {stdout.decode().strip()}")
        if stderr:
            logging.warning(f"FIX scan errors: {stderr.decode().strip()}")
        running_fix = False

    except Exception as e:
        logging.error(f"Error in default process: {e}")
    finally:
        running_default_process = False
        default_process_pid = None
        logging.info("Default process completed.")

def main():
    """
    Main function to monitor and execute commands based on input files.
    """
    global scan_rate, max_range, default_thread

    signal.signal(signal.SIGUSR1, signal_handler)

    logging.info("Starting main loop...")
    while True:
        try:
            start_time = time.time()

            cmd_file = latest_cmd_file(cmd_path)
            kepler_cmd = "stop"
            if cmd_file:
                cmd_dict = read_cmd_file(cmd_file)
                kepler_cmd = cmd_dict.get("command", "stop")
                delay_sec = float(cmd_dict.get("delay", 0)) if "delay" in cmd_dict else 0
                if kepler_cmd == "scan":
                    target_az = float(cmd_dict.get("azimuth", 0))
                    target_range = float(cmd_dict.get("range", 0))
                    if target_range > max_range:
                        kepler_cmd = "stop"
                elif kepler_cmd in ["rhi", "ppi"]:
                    start_angle = float(cmd_dict.get("start_angle", 0))
                    angle_span = float(cmd_dict.get("angle_span", 0))
                    fixed_angle = float(cmd_dict.get("fixed_angle", 0))
                    deg_per_sec = float(cmd_dict.get("deg_per_sec", 0))
                    nave = int(cmd_dict.get("nave", 0))

            logging.info(f"Command: {kepler_cmd}")

            if kepler_cmd in ["scan", "rhi", "ppi"]:
                if running_default_process and running_fix:
                    logging.info("Interrupting default process...")
                    os.system('/home/data/metek/m36s/bin/kill_datasaving')
                    os.kill(os.getpid(), signal.SIGUSR1)
                    remove_lock_file()

                if not running_default_process:
                    if default_thread is None or not default_thread.is_alive():
                        if delay_sec > 0:
                            logging.info(f"Delaying command execution by {delay_sec} seconds as specified in command file.")
                            time.sleep(delay_sec)
                        if kepler_cmd == "scan":
                            run_storm_rhis(target_az, target_range, scan_rate)
                        elif kepler_cmd == "rhi":
                            run_scan_rhi(start_angle, angle_span, fixed_angle, deg_per_sec, nave)
                        elif kepler_cmd == "ppi":
                            run_scan_ppi(start_angle, angle_span, fixed_angle, deg_per_sec, nave)
                        restart_default_process()

            elif kepler_cmd == "stop":
                if not running_default_process:
                    #os.system('/home/data/metek/m36s/bin/kill_datasaving')
                    if default_thread is None or not default_thread.is_alive():
                        restart_default_process()

            end_time = time.time()
            duration = end_time - start_time
            logging.info(f"Loop duration: {duration:.2f} seconds")
            time.sleep(max(0, 5 - duration))

        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            time.sleep(5)

def restart_default_process():
    """
    Restart the default process in a new thread.
    """
    global default_thread
    logging.info("Restarting default process...")
    default_thread = threading.Thread(target=default_process)
    default_thread.start()

def remove_lock_file():
    """
    Remove the lock file used by the system.
    """
    lock_file = '/tmp/aerotech_is_in_use'
    if os.path.exists(lock_file):
        os.remove(lock_file)
        logging.info("Lock file removed.")

if __name__ == "__main__":
    main()
