##
## Scanning Commands
##    pos_scan: move to a Named Position, run a Scan
##    pos_map

import numpy as np
import json

def pos_multiscan(posname, scannames, number=1):
    """
    move sample to a Named Position from SampleStage Positions list
    and run a list of scans defined from EpicsScan

    Parameters:
        posname  (string): Name of Position from SampleStage position list.
        scannames (list of strings): Names of Scans, as defined and saved from EpicsScan.
        number (integer): number of repeats of scan to do [default=1]

    Example:
       pos_multiscan('MySample', ['MnXANES', 'FeXANES'], number=1)

    """
    if check_abort_pause(): return
    move_samplestage(posname, wait=True)
    sleep(1.0)

    for scanname in scannames:
         elemname = scanname.replace('XANES', '').replace('_', '')
         move_to_edge(elemname)
         autoset_i0amp_gain()

         datafile = f'{scanname}_{posname}.001'
         do_scan(scanname,  filename=datafile, nscans=number)
    #endfor
#enddef


def pos_scan(posname, scanname, datafile=None, extra=None, number=1, **kws):
    """
    move sample to a Named Position from SampleStage Positions list
    and run a scan defined from EpicsScan

    Parameters:
        posname  (string): Name of Position from SampleStage position list.
        scanname (string): Name of Scan, as defined and saved from EpicsScan.
        datafile (string or None): Name of datafile to write [default=None]
            if None, datafile will be '<scanname>_<pos><extra>.001'
        number (integer): number of repeats of scan to do [default=1]
        extra (string): Extra name for file [default=None]

    Example:
       pos_scan('MySample', 'Fe_XANES', number=3)

    """
    if check_abort_pause(): return
    move_samplestage(posname, wait=True)
    sleep(1.0)
    if extra is None:
        extra = ''
    if datafile is None:
        datafile = f'{scanname}_{posname}{extra}.001'
    for key, val in kws.items():
        pvname = _getPV(key)
        if pvname is not None:
           caput(pvname, val)
        else:
           print("## No known PV for ", key)
    do_scan(scanname,  filename=datafile, nscans=number)
#enddef

def pos_map(posname, scanname):
    """
    move to a Named Position from SampleStage Positions list
    and run a slewscan map named in EpicsScan

    Parameters:
        posname (string):  Name of Position from SampleStage position list.
        scanname (string): Name of Scan, as defined and saved from EpicsScan.

    Example:
       pos_map('MySample', 'MyMap')
    """
    if check_abort_pause(): return
    move_samplestage(posname, wait=True)
    sleep(1.0)
    datafile = '%s_%s.001' % (scanname, posname)
    do_slewscan(scanname, filename=datafile)
#enddef

def scan_at_energy(scanname, posname, en):
    if check_abort_pause(): return
    move_energy(en)
    move_samplestage(posname, wait=True)
    fname = '%s_%s_%ieV.001' % (posname, scanname, en)
    do_scan(scanname, filename=fname)
#enddef

def _getPV(mname):
    """
    get PV name for a motor description.
    expected to be used internally.

    Parameters:
        mname (string): name of motor or other PV that can be scanned

    Returns:
        PVname (string) for motor, or None if not found in known names

    Example:
        xpv = _getPV('x')

    Note:
        known names include:
           'x' or 'finex' : sample fine X stage
           'y' or 'finey' : sample fine Y stage
           'focus'        : sample Z (focus) stage
           'coarsex'      : sample coarse X stage
           'coarsey'      : sample coarse Y stage
           'energy'       : monochromator energy
    """

    known = {'finex':   '13XRM:m1.VAL',
             'finey':   '13XRM:m2.VAL',
             'focus':   '13XRM:m11.VAL',
             'theta':   '13XRM:m6.VAL',
             'coarsex': '13XRM:m4.VAL',
             'coarsey': '13XRM:m5.VAL',
             }
    return known.get(mname.lower(), None)
#enddef

def move_stage(motorname, value, relative=False, wait=True):
    """move named stage to value

    Parameters:
        motorname (string): name of motor: 'finex', 'finey', 'coarsey', etc
        value (float): value to move to
        relative (bool): whether move is relative  [False]
        wait (bool): whether to wait for move to complete [True]
    """
    motor = _getPV(motorname)
    if motor is None:
        print(f"Error: cannot find motor named '{motorname}'")
        return

    if relative:
        value = value + caget(motor)
    print("Move " , motor, value, wait)

    caput(motor, value, wait=wait)


def _scanloop(scanname, datafile, motorname, vals, number=1):
    """
    run a named scan at each point for a named motor.
    expected to be used internally.

    Parameters:
        scanname (string): name of scan
        datafile (string): name of datafile (must be given)
        motorname (string): name of motor
        vals (list or array of floats): motor values at which to do scan.
        number(int): number of scan repeats at each point

    Example:
        _scanloop('Fe_XAFS', 'sample1_', 'x', [-0.1, 0.0, 0.1])

    Note:
        output files will named <scanname>_<datafile>_<motorname>I.001
        where I will increment 1, 2, 3, .. number of points in vals.
        For the above example, the files will be named
            'Fe_XAFS_sample1_x1.001',
            'Fe_XAFS_sample1_x2.001',
            'Fe_XAFS_sample1_x3.001'
    """
    if check_abort_pause(): return
    motor = _getPV(motorname)
    if motor is None:
        print("Error: cannot find motor named '%s'" % motorname)
        return
    #endif
    filename = '%s_%s_%s.001' % (scanname, datafile, motorname)

    for i, val in enumerate(vals):
        caput(motor, val, wait=True)
        filename = '%s_%s_%s.%3.3i' % (scanname, datafile, motorname, i+1)
        do_scan(scanname,  filename=filename, nscans=number)
        if check_scan_abort(): return
    #endfor
#enddef

def line_scan(scanname, posname, motor='x',
              start=0, stop=0.1, step=0.001, number=1):
    """
    run a named scan (or map) at each point in along a line

    Parameters:
        scanname (string): name of scan
        posname (string): name of position
        motor (string): name of motor to move ['x']
        start (float): starting motor value [0]
        stop (float): ending motor value [0.100]
        step (float): step size for motor [0.001]
        number(int): number of scan repeats at each point
    Example:
        line_scan('Fe_XAFS', 'mysample1', motor='x', start=0, stop=0.05, step=0.005, number=2)

    Note:
       output files will named `<scanname>_<datafile>_<x>I.001`  where I will
       increment 1, 2, 3, and so on.

       For the example above, the files will be named 'Fe_XAFS_mysample1_x1.001',
       'Fe_XAFS_mysample1_x1.002', 'Fe_XAFS_mysample1_x2.001', 'Fe_XAFS_mysample1_x2.002',
       'Fe_XAFS_mysample1_x3.001', 'Fe_XAFS_mysample1_x2.002', and so on.

    See Also:
       grid_scan

    """
    if check_abort_pause(): return
    move_samplestage(posname, wait=True)
    sleep(1.0)

    npts = int(1.0 + (abs(start-stop)+0.1*abs(step))/abs(step))
    vals = linspace(start, stop, npts)

    datafile = posname
    _scanloop(scanname, datafile, motor, vals, number=number)
#enddef


def line_xrf(posname, motor='x',
             start=0, stop=0.1, step=0.001, t=5):
    """
    run a named scan (or map) at each point in along a line

    Parameters:
        posname (string): name of position
        motor (string): name of motor to move ['x']
        start (float): starting motor value [0]
        stop (float): ending motor value [0.100]
        step (float): step size for motor [0.001]
        t(float): dwelltime
    Example:
        line_xrf('mysample1', motor='x', start=0, stop=0.05, step=0.005, t=10)

    Note:
       output files will named `<scanname>_<datafile>_<x>I.001`  where I will
       increment 1, 2, 3, and so on.

       For the example above, the files will be named 'Fe_XAFS_mysample1_x1.001',
       'Fe_XAFS_mysample1_x1.002', 'Fe_XAFS_mysample1_x2.001', 'Fe_XAFS_mysample1_x2.002',
       'Fe_XAFS_mysample1_x3.001', 'Fe_XAFS_mysample1_x2.002', and so on.

    See Also:
       save_xrf

    """
    if check_abort_pause(): return
    motorpv = _getPV(motor)
    if motorpv is None:
        print("Error: cannot find motor named '%s'" % motor)
        return
    #endif
    move_samplestage(posname, wait=True)

    sleep(1.0)

    npts = int(1.0 + (abs(start-stop)+0.1*abs(step))/abs(step))
    vals = linspace(start, stop, npts)

    filename = '%s_%s_xrf.001' % (posname, motor)

    for i, val in enumerate(vals):
        caput(motorpv, val, wait=True)
        filename = '%s_%s_xrf.%3.3i' % (posname, motor, i+1)
        save_xrf(filename, t=t)
        if check_scan_abort(): return
    #endfor
#enddef


def transect_scan(scanname, datafile, pos1, pos2, npts=11, nscans=1):
    """
    run a scan at evenly spaced points from

    (FineX, FineY) of Position1 to (FineX, FineY) of Position2

    Parameters:
        scanname (string): name of scan
        datafile (string): name for datafile
        pos1 (string): name of Start position
        pos2 (string): name of Stop position
        npts (int): number of steps                [11]
        nscans (int): number of scans at each step [1]

    Example:
        transect_scan('Fe_XAFS', 'sample1', 'Point1', 'Point2', npts=5)

    Notes:
        1. output files will named <scanname>_<datafile>_I.001 where I will
           increment 1, 2, 3, .... For the above example, the files will be named
             'Fe_XAFS_sample1_1.001',
             'Fe_XAFS_sample1_2.001',
             'Fe_XAFS_sample1_3.001', and so on

    See Also:
        line_scan, grid_xrd, diag, diag_scan

    """
    if check_abort_pause(): return

    instrument = _scandb.get_info('samplestage_instrument', 'SampleStage')
    p1 = _instdb.get_position(instrument, pos1)
    p2 = _instdb.get_position(instrument, pos2)

    move_samplestage(pos1, wait=True)
    if p1 is None:
        print("Error: cannot find position '%s'" % pos1)
        return

    if p2 is None:
        print("Error: cannot find position '%s'" % pos2)
        return

    xmotor = p1.pv[0].pv.name
    if xmotor is None:
        print("Error: cannot find motor named '%s'" % xname)
        return

    xstart = float(p1.pv[0].value)
    xstop  = float(p2.pv[0].value)

    if abs(xstop-xstart) < 0.001:
        xmotor = p1.pv[4].pv.name
        xstart = float(p1.pv[4].value)
        xstop  = float(p2.pv[4].value)
    #endif

    ymotor = p1.pv[1].pv.name
    if ymotor is None:
        print("Error: cannot find motor named '%s'" % yname)
        return
    #endif
    ystart = float(p1.pv[1].value)
    ystop  = float(p2.pv[1].value)

    if abs(ystop-ystart) < 0.001:
        ymotor = p1.pv[5].pv.name
        ystart = float(p1.pv[5].value)
        ystop  = float(p2.pv[5].value)

    xvals = linspace(xstart, xstop, npts)
    yvals = linspace(ystart, ystop, npts)

    i = 0
    for xval, yval in zip(xvals, yvals):
        i += 1
        caput(xmotor, xval, wait=True)
        caput(ymotor, yval, wait=True)
        filename = "%s_%s_%i.001" % (scanname, datafile, i)
        do_scan(scanname,  filename=filename, nscans=nscans)
        if check_scan_abort(): return
    #endfor
#enddef

def diagonal_scan(scanname, datafile, x='x', y='y',
                  xstart=0, xstop=0.1, xstep=0.001,
                  ystart=0, ystop=0.1, number=1):
    """
    run a scan at each point along a diagonal of two motors, say 'x' and 'y'

    Parameters:
        scanname (string): name of scan
        datafile (string): name for datafile
        x (string): name of X motor (inner loop) ['x']
        y (string): name of Y motor (outer loop) ['y']
        xstart (float): starting X value [0]
        xstop (float): ending X value [0.100]
        xstep (float): step size for X value [0.001]
        ystart (float): starting Y value [0]
        ystop (float): ending Y value [0.100]

    Example:
        diagonal_scan('Fe_XAFS', 'sample1', y='theta', xstart=0, xstop=0.05, xstep=0.005,
                   ystart=0, ystop=10)

    Notes:
        1. you set 'xstep', but not 'ystep'

        2. output files will named <scanname>_<datafile>_I.001 where I will
           increment 1, 2, 3, .... For the above example, the files will be named
             'Fe_XAFS_sample1_1.001',
             'Fe_XAFS_sample1_2.001',
             'Fe_XAFS_sample1_3.001', and so on

    See Also:
        line_scan, grid_xrd

    """
    if check_abort_pause(): return
    yname = y
    xname = x

    nx  = int(1.0 + (abs(xstart-xstop)+0.1*abs(xstep))/abs(xstep))
    ny  = nx
    xvals = linspace(xstart, xstop, nx)
    yvals = linspace(ystart, ystop, ny)

    ymotor = _getPV(yname)
    xmotor = _getPV(xname)
    if xmotor is None:
        print("Error: cannot find motor named '%s'" % xname)
        return
    #endif
    if ymotor is None:
        print("Error: cannot find motor named '%s'" % yname)
        return
    #endif

    for ix, xval in enumerate(xvals):
        caput(xmotor, xval, wait=True)
        caput(ymotor, yvals[ix], wait=True)
        filename = "%s_%s_%i.001" % (scanname, datafile, ix+1)
        do_scan(scanname,  filename=filename, nscans=number)
        if check_scan_abort(): return
    #endfor
#enddef

def grid_scan(scanname, x='x', y='y', datafile=None,
              xstart=0, xstop=0.1, xstep=0.001,
              ystart=0, ystop=0.1, ystep=0.001):
    """
    run a named scan (or map) at each point in an x, y grid

    Parameters:
        scanname (string): name of scan
        x (string): name of X motor (inner loop) ['x']
        y (string): name of Y motor (outer loop) ['y']
        datafile (string): name for datafile [scanname]
        xstart (float): starting X value [0]
        xstop (float): ending X value [0.100]
        xstep (float): step size for X value [0.001]
        ystart (float): starting Y value [0]
        ystop (float): ending Y value [0.100]
        ystep (float): step size for Y value [0.001]

    Example:
        grid_scan('Fe_XAFS', 'sample1', y='theta', xstart=0, xstop=0.05, xstep=0.005,
                   ystart=0, ystop=10, ystep=1)

    Note:
        output files will named <scanname>_<datafile>_<y>I_<x>J.001
        where I and J will increment 1, 2, 3, ...
        For the above example, the files will be named
        'Fe_XAFS_sample1_theta1_x1.001',
        'Fe_XAFS_sample1_theta1_x2.001',
        'Fe_XAFS_sample1_theta1_x3.001', and so on

    See Also:
        line_scan, grid_xrd

    """
    if check_abort_pause(): return
    yname = y
    xname = x

    nx  = int(1.0 + (abs(xstart-xstop)+0.1*abs(xstep))/abs(xstep))
    ny  = int(1.0 + (abs(ystart-ystop)+0.1*abs(ystep))/abs(ystep))
    xvals = linspace(xstart, xstop, nx)
    yvals = linspace(ystart, ystop, ny)

    ymotor = _getPV(yname)
    xmotor = _getPV(xname)
    if ymotor is None:
        print("Error: cannot find motor named '%s'" % yname)
        return
    #endif
    print("Xmotor ", xmotor, xvals)
    print("Ymotor ", ymotor, yvals)
    if datafile is None: datafile = scanname

    for iy, yval in enumerate(yvals):
        caput(ymotor, yval, wait=True)
        print("Move y ", ymotor, yval, 'loop over x ', xname, xvals)
        ydatafile = "%s_%s%i" % (datafile, yname, iy+1)
        _scanloop(scanname, ydatafile, xname, xvals)
        # print( "_scanloop ", scanname, ydatafile, xname, xvals)
        if check_scan_abort():  return
    #endfor
#enddef

## For V:
# energies=[5460, 5467.5, 5469, 5485.9, 5493.3, 5600]):

def redox_map(posname, scanname, datafile=None, energies=[2472.0, 2481.5, 2550]):
    """
    repeat a scan or map at multiple energies

    Parameters:
        posname (string): position name
        scanname (string):  scan name

        energies (list of floats):   list of energies (in eV) to run map scan at

    Example:
       redox_map('MyMap', 'sampleX', energies=[5450, 5465, 5500])

    Note:
        output files will named <scanname>_<energy>eV.001
        for the example above, the files will be named
        'MyMap_sampleX_5450.0eV.001',
        'MyMap_sampleX_5465.0eV.001',
        'MyMap_sampleX_5500.0eV.001',

    """
    if check_abort_pause(): return
    move_samplestage(posname, wait=True)

    if datafile is None:
        datafile = '%s_%s.001' % (scanname, posname)
    #endif

    for en in energies:
        move_energy(en)
        set_mono_tilt()
        caput('13XRM:pitch_pid.FBON', 1)

        dfile = '%s_%.1feV.001' % (datafile, en)
        print("Start Map ", scanname, " Filename ", dfile)
        do_scan(scanname,  filename=dfile)

        caput('13XRM:pitch_pid.FBON', 0)
        if check_scan_abort(): return




def grid_xrd(datafile, t=5, x='x', y='y',
             xstart=0, xstop=0.1, xstep=0.001,
             ystart=0, ystop=0.1, ystep=0.001, bgr_per_row=False):
    """
    collect an XRD image at each point in an x, y grid
    running save_xrd() at each point in the grid

    Parameters:
        datafile (string): name for datafile
        t (float): exposure time per pixel
        x (string): name of X motor (inner loop) ['x']
        y (string): name of Y motor (outer loop) ['y']
        xstart (float): starting X value [0]
        xstop (float): ending X value [0.100]
        xstep (float): step size for X value [0.001]
        ystart (float): starting Y value [0]
        ystop (float): ending Y value [0.100]
        ystep (float): step size for Y value [0.001]
        bgr_per_row (True or False): whether to collec xrd_bgr()
            at the beginning of each row.

    Example:
        grid_xrd('MySample', xstart=0, xstop=0.05, xstep=0.005,
                  ystart=0, ystop=10, ystep=1)

    Note:
        output files will named <scanname>_<datafile>_<y>I_<x>J.001
        where I and J will increment 1, 2, 3, and so on.
        For the above example, the files will be named
        'MySample_y1_x1.001', 'MySample_y1_x2.001', and so on

    See Also:
        save_xrd, xrd_bgr

    """
    if check_abort_pause(): return
    yname = y
    xname = x

    nx  = int(1.0 + (abs(xstart-xstop)+0.1*abs(xstep))/abs(xstep))
    ny  = int(1.0 + (abs(ystart-ystop)+0.1*abs(ystep))/abs(ystep))
    xvals = linspace(xstart, xstop, nx)
    yvals = linspace(ystart, ystop, ny)

    xmotor = _getPV(xname)
    ymotor = _getPV(yname)
    if ymotor is None:
        print("Error: cannot find motor named '%s'" % yname)
        return
    #endif

    for iy, yval in enumerate(yvals):
        caput(ymotor, yval, wait=True)
        if bgr_per_row: xrd_bgr()
        ydatafile = "%s_%s%i" % (datafile, yname, iy+1)
        for ix, xval in enumerate(xvals):
           caput(xmotor, xval, wait=True)
           fname = ydatafile + '_%s%i' % (xname, ix+1)
           save_xrd(fname, t=t, ext=1)
           if check_scan_abort():  return
        #endfor
    #endfor
#enddef

def line_xrd(datafile, t=5, motor='x', start=0, stop=0.1, step=0.001):
    """
    collect an XRD image at each point in along a line

    Parameters:
        datafile (string): name for datafile
        t (float): exposure time per point
        motor (string): name of motor ['x']
        start (float): starting  value [0]
        stop (float): ending  value [0.100]
        step (float): step size for  value [0.001]

    Example:
        line_xrd('MySample', t=5, start=0, stop=0.05, step=0.005)

    Note:
        output files will named <datafile>.001, .002, and so on.
        For the above example, the files will be named
        'MySample.001', 'MySample.002', and so on

    See Also:
        save_xrd, grid_xrd
    """
    if check_abort_pause(): return
    npts = int(1.0 + (abs(start-stop)+0.1*abs(step))/abs(step))
    mvals = linspace(start, stop, npts)
    motor_pv = _getPV(motor)
    for i, val in enumerate(mvals):
       caput(motor_pv, val, wait=True)
       save_xrd(datafile, t=t, ext=(i+1))
       if check_scan_abort():  return
    #endfor
#enddef

def theta_xafs(scanname, datafile, motor='theta',
              start=-5, stop=5, step=0.5, number=1):
    """
    run a named scan (or map) at each point in along a line

    Parameters:
        scanname (string): name of scan
        datafile (string): name for datafile
        motor (string): name of motor to move ['x']
        start (float): starting motor value [0]
        stop (float): ending motor value [0.100]
        step (float): step size for motor [0.001]
        number(int): number of scan repeats at each point
    Example:
        theta_xafs('Fe_XAFS', 'sample1', motor='x', start=0, stop=0.05, step=0.005, number=2)

    Note:
       output files will named `<scanname>_<datafile>_<x>I.001`  where I will
       increment 1, 2, 3, and so on.

       For the example above, the files will be named 'Fe_XAFS_sample1_x1.001',
       'Fe_XAFS_sample1_x1.002', 'Fe_XAFS_sample1_x2.001', 'Fe_XAFS_sample1_x2.002',
       'Fe_XAFS_sample1_x3.001', 'Fe_XAFS_sample1_x2.002', and so on.

    See Also:
       grid_scan

    """
    if check_abort_pause(): return
    npts = int(1.0 + (abs(start-stop)+0.1*abs(step))/abs(step))
    vals = linspace(start, stop, npts)

    _scanloop(scanname, datafile, motor, vals, number=number)
#enddef

def dac_xafs(scanname, samplename, tstart=-5, tstop=5, xstart=6.8, xstop=7.0, npts=11):
    """
    run a named scan (or map) at each point in along a (theta, x) line

    Parameters:
        scanname (string): name of scan
        samplename (string): name for sample
        tstart (float): starting theta value [-5]
        tstop (float): ending theta value [5]
        xstart (float): starting x value [6.8]
        xstop (float): ending x value [7.0]
        npts(int):  number of scan points
    Example:
        dac_xafs('GeXAFS', 'sample1', tstart=0, tstop=0.05, npts=11)

    Note:
       output files will named `<scanname>_<samplename>.00I`  where I will
       increment 1, 2, 3, and so on.

    See Also:
       grid_scan

    """
    if check_abort_pause(): return
    diode_in()
    set_mono_tilt()

    tvals = linspace(tstart, tstop, npts)
    xvals = linspace(xstart, xstop, npts)
    theta_pv = _getPV('theta')
    finex_pv = _getPV('finex')

    filename = '%s_%s.001' % (scanname, samplename)

    for theta, finex in zip(tvals, xvals):
        caput(theta_pv, theta, wait=True)
        caput(finex_pv, finex, wait=True)
        do_scan(scanname,  filename=filename, nscans=1)
        if check_scan_abort(): return
    #endfor
#enddef

def maplist(posname, scanname, suffixes=None):
    """
    repeat a scan or map at multiple points with similar names

    Parameters:
        posname (string): position name
        scanname (string):  scan name
        suffix (string): position name suffix

    Example:
       maplist('SampleA_', 'MyMap', suffixes=['1', '2', '3'])

    to do MyMap at SampleA_1, SampleA_2, SampleA_3
    """
    if suffixes is None: suffixes = []
    for suff in suffixes:
        pname = "%s%s" % (posname, suff)
        move_samplestage(pname, wait=True)

        datafile = '%s_%s.001' % (scanname, pname)

        if check_scan_abort(): return
        do_scan(scanname,  filename=datafile)
        if check_scan_abort():  return
    #endfor
#enddef



def herfd_scan(posname, scanname, energies=[7045, 7057, 7058, 7059, 7060]):
    """
    repeat a scan at multiple emission energies

    Parameters:
        posname  (string): position name
        scanname (string):  scan name
        energies (list): list of emission energies

    Example:

    Note:
    """
    if check_abort_pause(): return
    move_samplestage(posname, wait=True)

    for en in energies:
        datafile = '%s_%d_%s.001' % (scanname, en, posname)
        caput('13XRM:ANA:Energy', en, wait=True)
        do_scan(scanname,  filename=datafile)
        if check_scan_abort(): return
    #endfor
#enddef

def rixs_scan(posname, scanname, estart=7055, estop=7062, estep=0.25):
    """
    repeat a scan at multiple emission energies

    Parameters:
        posname (string): position name
        scanname (string):  scan name
        estart   (float): emission energy start
        estop   (float):  mission energy stop
        estep   (float):  emission energy step

    Example:
       redox_map('FeO1', 'FeHERFD', estart=7050, estop=7060, estep=0.1)

    Note:
        output files will named <scanname>_<energy>eV.001
        for the example above, the files will be named
        'MyMap_sampleX_5450.0eV.001',
        'MyMap_sampleX_5465.0eV.001',
        'MyMap_sampleX_5500.0eV.001',

    """
    if check_abort_pause(): return
    move_samplestage(posname, wait=True)

    datafile = '%s_%s' % (scanname, posname)

    nepts = int((estop-estart + 1.1*estep)/estep)
    energies = linspace(estart, estop, nepts)

    for en in energies:
        caput('13XRM:ANA:Energy', en)
        fast_mono_tilt()
        dfile = '%s_emission%.1feV.001' % (datafile, en)
        do_scan(scanname,  filename=dfile)
        if check_scan_abort(): return
    #endfor
#enddef

def ssa_xafs(posname, scanname,
             ssavals=[0.02, 0.04, 0.06, 0.08, 0.1]):
    if check_abort_pause(): return
    move_samplestage(posname, wait=True)
    fileform = "{:s}_{:s}_SSA{:3.0f}um.001".format
    for sval in ssavals:
        caput('13IDA:m70.VAL', sval)
        autoset_i0amp_gain()
        set_mono_tilt()
        collect_offsets()
        fname = fileform(posname, scanname, sval*1000)
        do_scan(scanname, filename=fname)


def xrf_maps():
    energies = [11000, 12000, 13000, 14000, 15000, 16000, 17000, 18000]
    edges    = ['Ge',   'As',   'Br', 'Kr',  'Rb',   'Sr',  'Y',  'Zr']
    ddistances = [53, 51, 49, 47]
    samples  = ['AXOXRFA', 'AXOXRFB', 'SRM1832A', 'SRM1832B',
                'SRM1833A', 'SRM1833B']
    filters  = [0, 300]
    mapname  = 'map100um'
    fileform = "{:s}_{:.0f}eV_det{:.0f}_filt{:.0f}.001".format
    for edge, en in zip(edges, energies):
        detector_distance(60, wait=False)
        move_to_edge(edge, with_tilt=True)
        move_energy(en, wait=True)
        autoset_i0amp_gain()
        set_mono_tilt()
        for sample in samples:
            detector_distance(60, wait=True)
            move_samplestage(sample, wait=True)
            for ddist in ddistances:
                detector_distance(ddist)
                fast_mono_tilt()
                for fval in filters:
                    filter(fval)
                    fname = fileform(sample, en, ddist, fval)
                    do_scan(mapname, filename=fname)


def xafs_dtc_scans(posname, scanname):
    FOE_VALS = (0.75, 0.4, 0.1)
    DET_VALS = (60.0, 65.0, 70.0)
    SSA_VALS = (0.20, 0.10, 0.050, 0.025, 0.010, 0.005)
    for fval in FOE_VALS:
        caput('13IDA:m6.VAL', fval)
        for dval in DET_VALS:
            caput('13IDE:m19.VAL', dval)
            ssa_hsize(SSA_VALS[0])
            set_mono_tilt()
            autoset_i0amp_gain()
            for sval in SSA_VALS:
                ssa_hsize(sval)
                print("---> hsize ", sval)
                fast_mono_tilt()
                print("setting i0 gain")
                autoset_i0amp_gain()
                print("starting scan")
                sleep(1)
                pos_scan(posname, scanname)
            #endfor
        #endfor
    #endfor
#enddef

def xafs_dtc1(posname, scanname):
    FOE_VALS = (1.0, 0.5, 0.25, 0.1)
    DET_VALS = (60.0, 65.0, 70.0)
    SSA_VALS = (0.200, 0.100, 0.05, 0.025, 0.010, 0.005)
    ssa_hsize(SSA_VALS[0])
    set_mono_tilt()
    for sval in SSA_VALS:
        ssa_hsize(sval)
        sleep(0.25)
        autoset_i0amp_gain()
        print("starting scan")
        pos_scan(posname, scanname)
    #endfor
#enddef


def fe_map(scanname, posname):
    """
    repeat a scan at multiple energies around Fe edge - a custom redox map

    Parameters:
        posname (string): position name
        scanname (string):  scan name

    Example:
       fe_map('MyMap')

    Note:
        output files will named <scanname>_<energy>eV.001
        for the example above, the files will be named
        'MyMap_sampleX_7100.0eV.001',
        'MyMap_sampleX_7105.0eV.001'
    """
    if check_abort_pause(): return
    move_samplestage(posname, wait=True)
    datafile = '%s_%s' % (scanname, posname)

    energies = [7100, 7105, 7107, 7108, 7109]
    energies.extend(np.arange(7110,  7114, 0.25).tolist())
    energies.extend(np.arange(7114,  7130,  1.0).tolist())
    energies.extend(np.arange(7130,  7250, 10.0).tolist())

    for en in energies:
        move_energy(en)
        dfile = '%s_%.2feV' % (datafile, en)
        do_scan(scanname,  filename=dfile)
        if check_scan_abort(): return


def cu_grid(posname, xjump=0.200, yjump=0, energy1=8983.9, energy2=9200,
            xstart=0, xstop=1, xstep=0.1,
            ystart=0, ystop=1, ystep=0.1,
            scan1='cu_timeseries', scan2='Cu_XANES_halfsec'):
    """
    move to a position, run 1 scan then jump  in x/y
    and run a second scan in a grid

    Parameters:
        posname (string): position name
        xjump:   jump in x (0.2)
        yjump:   jump in y (0.0)
        scan1   name of first scan to run ('cu_timeseries')
        scan2   name of second scan to run ('Cu_XANES_halfsec')
    """


    if check_abort_pause(): return
    move_samplestage(posname, wait=True)
    if check_abort_pause(): return
    print("  running SCAN:  ", scan1 , "  at ", posname)
    move_energy(energy1)
    pos_scan(posname, scan1)

    xmotor = _getPV('coarsex')
    xposition = caget(xmotor)
    caput(xmotor, xposition-xjump)

    ymotor = _getPV('coarsey')
    yposition = caget(ymotor)
    caput(ymotor, yposition+yjump)

    # print(" move x, y ", xmotor, xposition+xjump, ymotor, yposition+yjump)
    if check_abort_pause(): return

    print(" grid_scan: ", scan2, posname, xstart, xstop, xstep,  ystart, ystop, ystep)
    grid_scan(scan2, posname, x='finex', y='finey',
              xstart=xstart, xstop=xstop, xstep=xstep,
              ystart=ystart, ystop=ystop, ystep=ystep)
    if check_abort_pause(): return
    move_energy(energy2)
    close_shutter()


def enscan(e0, start=-100, stop=100, step=1, dwelltime=1,
           filename='enscan.001', is_relative=True, rois=None, elem='Cu',
           edge='K', with_xrf=True, scanname=None):

    sdict = {'type': 'xafs', 'scanmode': 'slew',
             'energy_drive': '13IDE:En:Energy.VAL',
             'energy_read': '13IDE:En:E_RBV.VAL',
             'pos_settle_time': 0.05,
             'det_settle_time': 0.01}

    sdict['e0'] = e0
    sdict['filename'] = filename
    sdict['dwelltime'] = dwelltime
    sdict['is_relative'] = is_relative

    rois_used = ['OutputCounts']
    if rois is not None:
        for roi in rois:
            if roi not in rois_used:
                rois_used.append(roi)
    sdict['rois'] = rois_used

    if elem is not None:
        sdict['elem'] = elem
    if edge is not None:
        sdict['edge'] = edge
    npts  = int(1 + (stop - start + step*0.25 )/step)
    sdict['regions'] = [[start, stop, npts, dwelltime, 'eV']]

    # print('Scan Regions ', e0, sdict['regions'])

    det_mcs =  {'nchan': 8.0, 'scaler': '13IDE:scaler1',
                'label': 'mcs', 'prefix': '13IDE:MCS1:',
                'kind': 'usbctr', 'notes': None}
    det_xrf =  {'fileroot': '/cars4/data/xas_user/', 'nmcas': 7.0,
                'nrois': 48.0, 'use_full': False, 'label': 'xspress3',
                'prefix': '13QX7:', 'kind': 'xspress3', 'notes': None}

    sdict['detectors'] = [det_mcs]
    if with_xrf:
        sdict['detectors'].append(det_xrf)

    sdict['counters'] = [['QuadBPM_Sum', '13XRM:QE2:SumAll:MeanValue_RBV'],
                         ['Mono_xtal1_temp', '13IDA:DMM1Ch12_calc'],
                         ['Mono_xtal2_temp', '13IDA:DMM1Ch11_calc']]

    if scanname is None:
        scanname = '_enscan_'

    sdef = _scandb.get_scandef(scanname)
    if sdef is not None:
        _scandb.del_scandef(scanname)
    _scandb.add_scandef(scanname, text=json.dumps(sdict), type='xafs')
    do_scan(scanname, filename=filename, nscans=1)
