##
## Commands for X-ray Diffraction
##
## Note that an XRD camera must be installed!

from pathlib import Path
from time import monotonic as clock
from epicsscan.detectors.ad_eiger import EigerSimplon
from epicsscan.detectors.ad_integrator import read_poni

CAMERA_EIG1 = '13EIG1:'
CAMERA_PIL300K = '13PIL300K:'
CAMERA_EIG2 = '13EIG2:'

CAMERA = _scandb.get_info('xrd_detector_prefix', CAMERA_EIG2)

eiger500k_params = {'prefix': '13EIG1:', 'ip': '10.54.160.234', 'iocport': 29200}
eiger1M_params  = {'prefix': '13EIG2:', 'ip';: '10.54.160.13', 'iocport': 27940}

def use_herfd_detector():
    _scandb.set_info('xrd_detector_prefix', '13EIG1:')
    _scandb.set_info('xrdmap_detector',    'eiger500k')


def use_xrd_detector():
    _scandb.set_info('xrd_detector_prefix', '13EIG2:')
    _scandb.set_info('xrdmap_detector',     'eiger1M')

def restart_eiger500k():
    """
    restart Eiger detector, and restart Epics interface
    Warning: takes about 1 minute
    """
    restart_eiger(**eiger500k_params)


def restart_eiger1m():
    """
    restart Eiger detector, and restart Epics interface
    Warning: takes about 1 minute
    """
    restart_eiger(**eiger1m_params)

def restart_eiger(prefix=None, ip=None, iocport=None):
    """
    restart Eiger detector, and restart Epics interface
    Warning: takes about 1 minute
    """
    if prefix is None:
        print("must provide prefix and other eiger parameters")
        return

    eiger = EigerSimplon(ip, procserv_iocport=iocport,
                         prefix=f'%{prefix}cam1:')
    print(f"Restarting Eiger {prefix} (may take a minute) ....")
    eiger.restart_daq()
    print("Eiger Ready to use.")

def enable_eiger(enable=True):
    useval = 1 if enable else 0
    _scandb.update('scandetectors', where={'name': 'eiger'}, use=useval)

def disable_eiger():
    enable_eiger(False)

def set_ponifile(filename):
    """set poni file for XRD mapping/autointegration
    relative to working directory
    """

    root = _scandb.get_info('server_fileroot')
    workdir = _scandb.get_info('user_folder')

    fname = Path(root, workdir, filename).
    if fname.exists():
        calib = read_poni(fname.as_posix())
    else:
        print("Could not find calibration file ", fname)
        return

    calname = fname.stem
    _scandb.set_detectorconfig(calname, json.dumps(calib))
    _scandb.set_info('xrd_calibration', calname)
    print(f"Will use calibration from PONI File {fname}")

def save_xrd(name, t=10, ext=None, prefix=None, timeout=60.0):
    """
    Save XRD image from XRD camera.

    Parameters:
        name (string):  name of datafile
        t (float):   exposure time in seconds [default= 10]
        ext (int or None): number for file extension
            if left as None, the extension will be auto-incremented.
        prefix (string):   PV prefix for areaDetector camera [default camera]
        timeout (float): maximumn time in seconds to wait
            for image to be saved [60]

    Examples:
        save_xrd('CeO2', t=20)

    Note:
        calls one of `save_xrd_marccd` or `save_xrd_pe`

    See Also:
       `save_xrd_marccd`, `save_xrd_pe`

    """
    if prefix is None:
        prefix = _scandb.get_info('xrd_detector_prefix')

    if 'pil' in prefix.lower():
        save_xrd_pil(name, t=t, ext=ext, prefix=prefix)
    elif 'eig' in prefix.lower():
        save_xrd_eiger(name, t=t, ext=ext, prefix=prefix)
    else:
        print("cannot identify XRD camera ", prefix)


def save_xrd_eiger(name, t=10, ext=None, prefix=None, timeout=60.0):
    """
    Save XRD image from Eiger camera.

    Parameters:
        name (string):  name of datafile
        t (float):   exposure time in seconds [default= 10]
        ext (int or None): number for file extension
            if left as None, the extension will be auto-incremented.
        prefix (string):   PV prefix for areaDetector camera [default camera
        timeout (float): maximumn time in seconds to wait
            for image to be saved [60]

    Examples:
        save_xrd_eiger('CeO2', t=20)

    """
    if prefix is None:
        prefix = _scandb.get_info('xrd_detector_prefix')

    x = caput(prefix+'cam1:Acquire', 0, wait=True)
    sleep(0.5)

    x = caput(prefix+'cam1:FWEnable', 1)
    x = caput(prefix+'cam1:SaveFiles', 0)
    x = caput(prefix+'cam1:ManualTrigger', 0)
    x = caput(prefix+'cam1:NumTriggers', 1)
    x = caput(prefix+'TIFF1:EnableCallbacks', 0)
    x = caput(prefix+'TIFF1:AutoSave',        0)
    x = caput(prefix+'TIFF1:FileName',     name)
    if ext is not None:
        x = caput(prefix+'TIFF1:FileNumber',    ext)
        x = caput(prefix+'TIFF1:AutoIncrement',   0)
    else:
        x = caput(prefix+'TIFF1:AutoIncrement',   1)

    x = caput(prefix+'TIFF1:EnableCallbacks', 1)
    x = caput(prefix+'cam1:TriggerMode', 0)

    print(f'Save tiff from Eiger ({t:.1f} seconds)')
    sleep(0.5)
    x = caput(prefix+'cam1:NumImages', 1)
    x = caput(prefix+'cam1:AcquirePeriod', t)
    x = caput(prefix+'cam1:AcquireTime', t)

    sleep(0.5)
    t0 = clock()
    caput(prefix+'cam1:Acquire', 1)
    sleep(1.0 +  t/3.0)
    while ((1 == caget(prefix+'cam1:Acquire')) and
            (clock()-t0 < timeout)):
         sleep(0.25)

    sleep(0.25)

    # clean up, returning to short dwell time
    caput(prefix+'TIFF1:WriteFile',       1)
    caput(prefix+'TIFF1:EnableCallbacks', 0)
    sleep(0.25)
    name = caget(prefix+'TIFF1:FullFileName_RBV',  as_string=True)
    print(f'Acquire Done, wrote file {name}, {(clock()-t0):.2f} seconds')

    x = caput(prefix+'cam1:FWEnable', 0)
    caput(prefix+'cam1:Acquire', 0)
    caput(prefix+'cam1:NumImages', 64000)
    caput(prefix+'cam1:AcquirePeriod', 0.25)
    caput(prefix+'cam1:AcquireTime', 0.25)
    caput(prefix+'cam1:AcquirePeriod', 0.25)
    caput(prefix+'cam1:Acquire', 1)


def save_xrd_pil(name, t=10, ext=None, prefix=None, timeout=60.0):
    """
    Save XRD image from Pilatus camera.

    Parameters:
        name (string):  name of datafile
        t (float):   exposure time in seconds [default= 10]
        ext (int or None): number for file extension
            if left as None, the extension will be auto-incremented.
        prefix (string):   PV prefix for areaDetector camera [default camera
        timeout (float): maximumn time in seconds to wait
            for image to be saved [60]

    Examples:
        save_xrd_pil('CeO2', t=20)

    """
    if prefix is None:
        prefix = _scandb.get_info('xrd_detector_prefix')

    print(" SAVE XRD  prefix ", prefix)
    # save shutter mode, disable shutter for now
    shutter_mode = caget(prefix+'cam1:ShutterMode')
    caput(prefix+'cam1:ShutterMode', 0)
    caput(prefix+'cam1:Acquire', 0)
    sleep(0.1)
    print("Save XRD...")
    caput(prefix+'TIFF1:EnableCallbacks', 0)
    caput(prefix+'TIFF1:AutoSave',        0)
    caput(prefix+'TIFF1:AutoIncrement',   1)
    caput(prefix+'TIFF1:FileName',     name)
    if ext is not None:
        caput(prefix+'TIFF1:FileNumber',    ext)

    caput(prefix+'TIFF1:EnableCallbacks', 1)

    caput(prefix+'cam1:TriggerMode', 0)

    sleep(0.25)

    caput(prefix+'cam1:NumImages', 1)
    caput(prefix+'cam1:AcquireTime', t)

    # expose
    caput(prefix+'cam1:Acquire', 1)
    t0 = clock()
    print('Wait for Acquire ... ')

    while ((1 == caget(prefix+'cam1:Acquire')) and
            (clock()-t0 < timeout)):
        sleep(0.25)
    print(f'Acquire Done, writing file {name}')
    sleep(0.1)

    # clean up, returning to short dwell time
    caput(prefix+'TIFF1:WriteFile',       1)
    caput(prefix+'TIFF1:EnableCallbacks', 0)
    sleep(0.5)

def xrd_at(posname,  t=10):
    move_samplestage(posname, wait=True)
    save_xrd(posname, t=t, ext=1)
