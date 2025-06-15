from time import time, sleep
from epics import caget

def check_abort_pause(msg='aborted.'):
    "wait for pause to end, return whether Abort has been requested"
    _scandb.wait_for_pause(timeout=86400.0)
    return _scandb.test_abort(msg)

def set_user_name(user_name):
    _scandb.set_info('user_name', user_name)

def restart_server():
    "hard restart of server"
    epv = get_dbinfo('epics_status_prefix')
    if epv is not None:
        shutdownpv = epv + 'Shutdown'
        caput(shutdownpv, 1)

def open_IDA_shutter(wait=False):
   caput('13IDA:OpenFEShutter.PROC', 1, wait=wait)

def close_IDA_shutter(wait=False):
   caput('13IDA:CloseFEShutter.PROC', 1, wait=wait)

def open_IDE_shutter(wait=False):
   caput('13IDA:OpenEShutter.PROC', 1, wait=wait)

def close_IDE_shutter(wait=False):
   caput('13IDA:CloseEShutter.PROC', 1, wait=wait)

def open_shutter(all=True,wait=False):
    caput('13IDE:USBCTR:Bo1.VAL', 0)
    move_instrument('SSA Viewscreen', 'Screen Out')
    if all:
        open_IDA_shutter(wait=False)
        open_IDE_shutter(wait=False)
    if wait:
        move_instrument('SSA Viewscreen',
                        'Screen Out', wait=wait)

def close_shutter(table_only=True, wait=True, with_ide=False):
    caput('13IDE:USBCTR:Bo1.VAL', 1, wait=wait)
    if with_ide:
        close_IDE_shutter(wait=wait)

def enable_id_tracking():
    _scandb.set_info('qxafs_id_tracking', 1)

def disable_id_tracking():
    _scandb.set_info('qxafs_id_tracking', 0)

def set_id_gap(val, wait=True, timeout=15.0):
    caput('S13ID:USID:ScanGapC.VAL', val, wait=wait, timeout=timeout)

def set_id_taper(val, wait=True, timeout=15.0):
    gap = caget('S13ID:USID:GapSetC.VAL')
    taper = caget('S13ID:USID:OptimumTaperM.VAL')
    caput('S13ID:USID:ScanGapC.VAL', gap+0.35)
    sleep(0.50)
    for i in range(2):
        sleep(0.3)
        caput('S13ID:USID:TaperGapSetC.VAL', val)
        sleep(0.3)
        caput('S13ID:USID:GapSetC.VAL', gap)
        sleep(0.3)
        caput('S13ID:USID:StartC.VAL', 1)

    sleep(0.5)
    caput('S13ID:USID:ScanGapC.VAL', gap)


def set_energy(val, wait=True, timeout=15.0):
    caput('13IDE:En:Energy.VAL', val, wait=wait, timeout=timeout)

def expose(t=15):
    "expose beam for time specified"
    open_shutter()
    sleep_time = int(t*100.0)/1.0e5
    end_time= clock() + t
    while clock() < end_time:
        sleep(sleep_time)
    close_shutter()


def expose_at(posname, t=5):
    close_shutter()
    move_samplestage(posname, wait=True)
    sleep(1.0)
    tsec = t*60
    sleep_time = t*1.1
    end_time= clock() + tsec
    open_shutter()
    while clock() < end_time:
        sleep(sleep_time)

    move_stage('finey', 0.25)
    fast_mono_tilt()
    close_shutter()




def set_filter(thickness=0, set_i0=True):
    """set thickness of Al filters upstream of I0

    Args:
       thickness: thickness in microns, must be one of:
                   0, 50, 100, 150, 200, 250, 300, 350 [0]
       set_i0: whether to do `autset_i0amp_gain()` and
               `collect_offsets()` after setting filters [True]
    """
    othick = thickness
    _scandb.set_info('experiment_i0_filter', f"Al: {othick} microns")
    thickness = int(thickness/50)
    #    v1, v2, v3 = [int(a) for a in bin(thick)[2:][::-1]]
    v3 = v2 = v1 = 0
    if thickness == 7:
        v3 = v2 = v1 = 1
    elif thickness == 6:
        v3 = v2 = 1
    elif thickness == 5:
        v3 = v1 = 1
    elif thickness == 4:
        v3 = 1
    elif thickness == 3:
        v2 = v1 = 1
    elif thickness == 2:
        v2 = 1
    elif thickness == 1:
        v1 = 1
    #endif
    caput('13IDE:USBCTR:Bo2.VAL', v1)
    caput('13IDE:USBCTR:Bo3.VAL', v2)
    caput('13IDE:USBCTR:Bo4.VAL', v3)
    if set_i0:
        open_shutter()
        autoset_i0amp_gain()

def wait_for_shutters(hours=6):
    """wait for shutters to open, up to N hours"""
    open_shutter(all=True)
    sleep(0.1)
    status = (caget('13IDA:eps_mbbi25'), caget('13IDA:eps_mbbi27'))
    if status == (1, 1):
        return
    print("#pre_scan: waiting for shutters to open")
    timeout= time() + hours*3600.0
    while status != (1, 1) and (time() < timeout):
        if check_scan_abort():
            break
        sleep(5.0)
        if int(time()) % 600 < 15:
            open_shutter(all=True)
            sleep(30.0)
        status = (caget('13IDA:eps_mbbi25'), caget('13IDA:eps_mbbi27'))
