##
## The function `pre_scan_command` is run automatically
## just before many of the internal scanning commands:
##
##  * before each 1-d scan, including XAFS Scans
##  * before each 2-d scan

DATE = '17-June-2025'
from time import time, sleep
from epics import caget, caput

def skip_prescan():
    _scandb.set_info('prescan_skip', 1)

def unskip_prescan():
    _scandb.set_info('prescan_skip', 0)

def pre_scan_command(row=1, *args, **kws):
    """
    function run prior to each internal scanning command
    This can be used to customize checks for intensity, etc.
    """
    t0 = time()
    # avoid running twice in a row
    lastrun_time =  float(_scandb.get_info('prescan_lasttime', 0))
    print(f"Pre Scan: {DATE} {row} {args} {kws.keys()}")
    prescan_skip =  _scandb.get_info('prescan_skip', as_bool=True)
    if prescan_skip:
        print("skipping pre_scan")
        return

    if (t0 - lastrun_time) < 10:
        print("skipping pre_scan: ran recently")
        return

    msg = ''
    if row is None or row < 1:
       row = 1
    #endif

    msg = f"row={row}"

    # Step 1: restart QE2
    roll_fb = caget('13XRM:roll_pid.FBON')
    caput('13XRM:QE2:Acquire', 0)
    sleep(0.25)
    caput('13XRM:QE2:Acquire', 1)

    # Step 2: open the IDE shutter, beam-filter stop
    open_shutter(all=True)
    shutter_status = (caget('13IDA:eps_mbbi25'),
                      caget('13IDA:eps_mbbi27'))
    if shutter_status != (1, 1):
        print("#pre_scan: waiting for shutters to open")
        tx = time()
        while shutter_status != (1, 1) and (time()-tx < 4*3600.0):
            if check_scan_abort():
                break
            sleep(1.0)
            if int(time()) % 300 < 10:
                open_shutter(all=True)
                sleep(10.0)
            shutter_status = (caget('13IDA:eps_mbbi25'),
                              caget('13IDA:eps_mbbi27'))
    sleep(0.1)

    #
    mono_energy = caget('13IDE:En:Energy')

    scantype = kws.get('scantype', 'map')
    with_gapscan = kws.get('with_gapscan', False)
    if scantype == 'qxafs' and with_gapscan:
        e0     = kws.get('e0', mono_energy)
        en_array = np.array(kws.get('energy', [mono_energy]))
        dwelltime = kws.get('dwelltime', 0.25)
        valid_gapscan = enable_gapscan(energy=en_array, e0=e0, dwelltime=dwelltime)
        print("Pre Scan using GapScan:", e0, dwelltime, len(en_array), valid_gapscan)

    print("fast_mono_tilt() at energy ", mono_energy)
    fast_mono_tilt()
    if mono_energy < 3000.00:
        feedback_on(roll=True, pitch=True)
    pitch_val = caget('13IDA:E_MonoPiezoPitch.VAL')
    roll_val = caget('13IDA:E_MonoPiezoRoll.VAL')
    _scandb.set_info('mono_pitch_val', f"{pitch_val:.3f}")
    _scandb.set_info('mono_pitch_roll', f"{roll_val:.3f}")

    sleep(0.1)
    now = time()
    _scandb.set_info('prescan_lasttime', int(time()))
    print(f'#pre_scan done ({now-t0:.2f})')
    return None

def post_scan_command(row=0):
    "run after each scan"
    sleep(0.05)
    disable_gapscan()
    # pval = _scandb.get_info('mono_pitch_val')
    # rval = _scandb.get_info('mono_pitch_roll')
    # print("Post Scan Command, restore mono pitch ", pval, rval)
    # caput('13XRM:pitch_pid.FBON', 0)
    # caput('13XRM:roll_pid.FBON', 0)
    # caput('13IDA:E_MonoPiezoPitch.VAL', pval)
    # caput('13IDA:E_MonoPiezoRoll.VAL', rval)
    # caput('13XRM:pitch_pid.FBON', 1)
    # caput('13XRM:roll_pid.FBON', 1)
#enddef
