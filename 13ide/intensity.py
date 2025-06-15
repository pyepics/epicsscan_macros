##
## Commands for setting intensities and Ion Chamber gains
# from epics import get_pv
# from time import sleep
from time import monotonic as clock
from time import sleep, ctime
# from common import check_abort_pause, check_scan_abort, caget, caput

def feedback_off():
    """
    Turn intensity feedback off
    """
    caput('13XRM:pitch_pid.FBON', 0)
    caput('13XRM:roll_pid.FBON', 0)
#enddef

def feedback_on(roll=True, pitch=True):
    """
    Turn intensity feedback on or off

    roll = True / False for roll feedback
    pitch = True / False for pitch feedback
    """
    caput('13XRM:pitch_pid.FBON', 0)
    caput('13XRM:roll_pid.FBON', 0)
    if pitch:
        caput('13XRM:pitch_pid.FBON', 1)
    #endif
    if roll:
        caput('13XRM:roll_pid.FBON', 1)
    #endif


def stop_mcs(prefix='13IDE:'):
    caput(f'{prefix}scaler1.CONT', 0)
    sleep(0.02)
    caput(f'{prefix}MCS1:StopAll',  1)
    sleep(0.02)
    caput(f'{prefix}MCS1:ChannelAdvance',  'Internal')
    sleep(0.02)

def scaler_mode(mode='autocount', count_time=1.0):
    """
    put scaler in 'autocount' or 'oneshot' or 'roi' mode
    """
    # stop mcs
    prefix='13IDE:'
    stop_mcs(prefix=prefix)

    count = 0
    while count < 5 and (0 != caget(f'{prefix}MCS1:Acquiring')):
        stop_mcs(prefix=prefix)
        sleep(0.02)
        caput(f'{prefix}scaler1.CONT', 0)
        sleep(0.02)
        caput(f'{prefix}scaler1.TP', 0.5)
        caput(f'{prefix}scaler1.TP1', 0.5)
        sleep(0.02)
        caput(f'{prefix}scaler1.CNT', 1, wait=True)
        sleep(0.02)
        caput(f'{prefix}MCS1:EraseStart', 1)
        sleep(0.02)
        caput(f'{prefix}MCS1:StopAll',  1)
        sleep(0.02)
        count += 1
    #endwhile

    caput(f'{prefix}scaler1.CONT', 0)  # one-shot
    caput(f'{prefix}scaler1.CNT',  0)  # done
    caput(f'{prefix}scaler1.TP', count_time)
    caput(f'{prefix}scaler1.TP1', count_time)
    sleep(0.02)

    val = 0
    if mode.lower().startswith('auto'): val = 1

    # caput(f'{prefix}scaler1.CONT', val)
    caput(f'{prefix}scaler1.CNT',  val)
#enddef


def optimize_id():
    """
    Optimize undulator by scanning ID energy and
    finding highest I0 intensity

    Example:
        optimize_id()
    """
    caput('13IDE:En:id_track', 0)
    und_energy  = caget('ID13us:ScanEnergy')
    mono_energy = caget('13IDE:En:Energy')
    energies = linspace(-75, 75, 31) + mono_energy
    caput('13IDE:En:Energy', energies[0])
    sleep(2.0)
    best_en  = mono_energy
    best_i0  = -10.0
    i0vals = []
    for en in energies:
       caput('13IDE:En:Energy', en, wait=True)
       sleep(1.00)
       i0val = caget('13IDE:scaler1.S2')
       i0vals.append(i0val)
       if i0val > best_i0:
         best_i0 = i0val
         best_en = en
       #endif
    #endfor
    caput('13IDE:En:id_track', 1)
    offset = und_energy - best_en*0.001
    print('best ID offset = %.3f keV ' % offset)
    caput('13IDE:En:id_off', offset)
    caput('13IDE:En:Energy', best_en)
#enddef


def collect_offsets(t=10):
    """
    Collect dark-current offsets for Ion chameber scalers

    Parameters:
        t (float):  time in seconds to count dark current for (default 10)

    Examples:
        collect_offsets()
    """
    # close shutter
    # caput('13IDA:CloseEShutter.PROC', 1)
    # set scaler to 1 shot mode, count time of 10 seconds
    count_time =  caget('13IDE:scaler1.TP')

    scaler_mode(mode='oneshot', count_time=t)
    close_shutter(wait=True)
    sleep(0.01)

    freq = caget('13IDE:scaler1.FREQ')
    caput('13IDE:scaler1.CNT', 1, wait=True)
    caput(f'13IDE:scaler1_calc1.CALC', f'A/{freq:.4e}')
    sleep(0.10)
    # read clock ticks, and counts for each channel
    clock_count = 1.0*caget('13IDE:scaler1.S1')
    for i, name in ((2, 'B'), (3, 'C'), (4, 'D'), (5, 'E'), (6, 'F'), (7, 'G'), (8, 'H')):
       desc = caget(f'13IDE:scaler1.NM{i}')
       if len(desc) > 0:
          counts = caget(f'13IDE:scaler1.S{i}')
          scale = counts/clock_count
          expr   = f'{name}-(A*{scale:.6e})'
          caput(f'13IDE:scaler1_calc{i}.CALC', expr)

    # reset count time, put in auto-count mode, open shutter
    scaler_mode(mode='autocount', count_time=count_time)
    open_shutter()
    _scandb.set_info('needs_offset', 0)
#enddef

SRS_SENS = [1, 2, 5, 10, 20, 50, 100, 200, 500]
SRS_UNITS = ['pA/V', 'nA/V', 'uA/V', 'mA/V']

def set_SRSgain(sens, unit, prefix='13IDE:A1', offset=30):
    """
    set pre-amplifier sensitivity, units, and offset

    Parameters:
        sens (int):  Number for sensitivity.
            One of (1, 2, 5, 10, 20, 50, 100, 200, 500).
        units (string): Unit sring.
            One of  ('pA/V', 'nA/V', 'uA/V', 'mA/V').
        prefix (string): PV prefix for SRS570 amplifier [default '13IIDE:A1']
        offset (float):  Input current offset for amplifier [default 25]

    Example:
       set_SRSgain(100, 'nA/V', prefix='13IDE:A2', offset=105)

    """
    units = [a.lower() for a in SRS_UNITS]
    sens_val = SRS_SENS.index(sens)
    unit_val = units.index(unit.lower())
    # print(sens_val, unit_val)
    caput("%ssens_unit.VAL" % prefix, unit_val)
    caput("%ssens_num.VAL"  % prefix, sens_val)
    if sens_val > 2:
        sens_val -= 3
    else:
        sens_val += 6
        unit_val -= 1
    #endif
    caput("%soffset_unit.VAL" % prefix, unit_val, wait=True)
    caput("%soffset_num.VAL"  % prefix, sens_val, wait=True)
    caput("%soff_u_put.VAL"   % prefix, offset, wait=True)

    sleep(0.05)
    # caput("%sreset.PROC"  % prefix, 1, wait=True)
    caput("%sinit.PROC"  % prefix, 1, wait=True)
    _scandb.set_info('needs_offset', 1)
#enddef

def set_i2amp_gain(sens, unit, offset=25):
    """
    set I2 pre-amplifier sensitivity, units, and offset

    Parameters:
        sens (int):  Number for sensitivity.
            One of (1, 2, 5, 10, 20, 50, 100, 200, 500).
        units (string): Unit sring.
            One of  ('pA/V', 'nA/V', 'uA/V', 'mA/V').
        prefix (string): PV prefix for SRS570 amplifier [default '13IIDE:A1']
        offset (float):  Input current offset for amplifier [default 25]

    Examples:
        set_i2amp_gain(100, 'nA/V')
    """
    set_SRSgain(sens, unit, prefix='13IDE:A3', offset=offset)
#enddef

def set_i1amp_gain(sens, unit, offset=25):
    """
    set I1 pre-amplifier sensitivity, units, and offset

    Parameters:
        sens (int):  Number for sensitivity.
            One of (1, 2, 5, 10, 20, 50, 100, 200, 500).
        units (string): Unit sring.
            One of  ('pA/V', 'nA/V', 'uA/V', 'mA/V').
        prefix (string): PV prefix for SRS570 amplifier [default '13IIDE:A1']
        offset (float):  Input current offset for amplifier [default 25]

    Examples:
        set_i1amp_gain(100, 'nA/V')
    """
    set_SRSgain(sens, unit, prefix='13IDE:A2', offset=offset)
#enddef

def set_i0amp_gain(sens, unit, offset=25):
    """
    set I0 pre-amplifier sensitivity, units, and offset

    Parameters:
        sens (int):  Number for sensitivity.
            One of (1, 2, 5, 10, 20, 50, 100, 200, 500).
        units (string): Unit sring.
            One of  ('pA/V', 'nA/V', 'uA/V', 'mA/V').
        prefix (string): PV prefix for SRS570 amplifier [default '13IIDE:A1']
        offset (float):  Input current offset for amplifier [default 25]

    Examples:
        set_i0amp_gain(100, 'nA/V')

    """
    set_SRSgain(sens, unit, prefix='13IDE:A1', offset=offset)
#enddef


def autoset_gain(prefix='13IDE:A1', scaler='13IDE:I0_Volts', offset=25, count=0):
    """
    automatically set i0 gain to be in range

    Parameters:
       prefix (string): PV name for SRS570.
       scaler (string): PV name for scaler reading to use for reading intensity.
       offset (float):  Scaler offset value to use (default 25).
       count (int):     Recursion count to avoid infinite loop.
    Returns:
       success (True or False): whether setting the gain succeeded.
    """
    # wait_for_shutters(hours=1)
    I0Max = 2.8
    I0Min = 0.7
    i0val = caget(scaler)
    sleep(0.5)
    if i0val < I0Max and i0val > I0Min:
        return True

    for i in range(2):
        unit = caget("%ssens_unit.VAL" % prefix)
        sens = caget("%ssens_num.VAL"  % prefix)
        sleep(0.5)
        i0val = caget(scaler)
        if i0val > I0Max:
           sens = sens + 1
           if sens > 8:
               sens = 0
               unit = unit + 1

        elif i0val < I0Min:
           sens = sens - 1
           if sens < 0:
              sens = 8
              unit = unit - 1
        else:
            return True
        ## check that we haven't gone out of range
        if unit < 0 or unit > 3:
            print(" Unit out of range ", unit)
            return False
        msg = "changing SRS sensitivity"
        print(f"{msg} i0={i0val:.3f} -> {SRS_SENS[sens]} {SRS_UNITS[unit]}")

        caput("%ssens_unit.VAL" % prefix, unit)
        caput("%ssens_num.VAL"  % prefix, sens)

        ## set offsets
        if sens > 2:
            off_sens = sens - 3
            off_unit = unit
        else:
            off_sens = sens + 6
            off_unit = unit - 1
        #endif

        caput("%soffset_unit.VAL" % prefix, off_unit)
        caput("%soffset_num.VAL"  % prefix, off_sens)
        caput("%soff_u_put.VAL"   % prefix, offset)
        _scandb.set_info('needs_offset', 1)
        sleep(1.0)
        i0val = caget(scaler)
        if (i0val > I0Min) and (i0val < I0Max):
            break
    scaler_mode(mode='autocount')
    return True
#enddef

def autoset_i0amp_gain(take_offsets=True):
    needs_offset = _scandb.get_info('needs_offset')
    autoset_gain(prefix='13IDE:A1', scaler='13IDE:USB1808:Ai1.VAL', offset=40)
    scaler_mode(mode='autocount')
    if take_offsets and _scandb.get_info('needs_offset',
                                         as_bool=True, default=False):
        collect_offsets()
    #endif

#enddef

def autoset_i1amp_gain(take_offsets=True):
    autoset_gain(prefix='13IDE:A2', scaler='13IDE:USB1808:Ai2.VAL', offset=40)
    scaler_mode(mode='autocount')
    if take_offsets and _scandb.get_info('needs_offset',
                                         as_bool=True, default=False):
        collect_offsets()
    #endif
#enddef

def autoset_i2amp_gain():
    autoset_gain(prefix='13IDE:A3', scaler='13IDE:scaler1.S4', offset=-100)
    scaler_mode(mode='autocount')
#enddef

def BPM_config(prefix='13XRM:QE2:', averaging_time=None, compute_offsets=False):
    caput(f'{prefix}Acquire', 0)
    sleep(0.05)
    if averaging_time is not None:
        caput(f'{prefix}AveragingTime', averaging_time, wait=True)

    caput(f'{prefix}Acquire', 1)
    sleep(0.05)

    if compute_offsets:
        caput(f'{prefix}ComputePosOffsetX.PROC', 1, wait=True)
        caput(f'{prefix}ComputePosOffsetY.PROC', 1, wait=True)
    caput(f'{prefix}ReadData.PROC', 1)
    return


def find_max_intensity(drivepv, vals, readpv, minval=0.1, debug=False):
    """
    find a max in an intensity while sweeping through an
    array of drive values,  around a current position, and
    move to the position with max intensity.

    Parameters:
        drivepv (string):  PV for driving positions
        vals (array of floats):  array of **relative** positions (from current value)
        readpv (string):   PV for reading intensity
        minval (float):   minimum acceptable intensity [defualt = 0.1]

    Returns:
        best_drive_value, max_readpv, max_read_pv2
    Note:
       if the best intensity is below minval, the position is
       moved back to the original position.

    """
    xorig = xbest = get_pv(drivepv).get()
    i1max = i1 = get_pv(readpv).get()
    caput(drivepv, xorig+vals[0])

    for _val in vals:
        val = xorig + _val
        caput(drivepv, val, wait=True)
        sleep(0.2)
        i1 = caget(readpv)
        if i1 > i1max:
            xbest, i1max = val, i1
        if get_dbinfo('request_abort', as_bool=True):
            return
        if debug:
            print(val, i1, i1max, xbest)
    #endfor
    if i1max < minval:
        xbest = xorig
        print(" i1max too small ", i1max, minval)
    #endif
    print(f" move {drivepv}  {xbest:.3f}")
    caput(drivepv, xbest, wait=True)
    sleep(0.05)
    return xbest, i1max
#enddef


def set_mono_tilt(enable_fb_roll=None, enable_fb_pitch=None):
    """
    Adjust IDE monochromator 2nd crystal tilt and roll to maximize intensity.

    Parameters:
        enable_fb_roll (True or False or None): enable roll feedback after
               best position is found. [None]
        enable_fb_pitch (True or False or None): enable pitch feedback after
               best position is found. [None]

    Note:
        This works by
            1. adjusting pitch to maximize intensity at BPM
            2. adjusting roll to maximize intensity at I0 Ion Chamber
            3. adjusting pitch to maximize intensity at I0 Ion Chamber

    """
    print('#-- set_mono_tilt')
    with_roll = True
    t0 = clock()
    energy_pv = '13IDE:En:Energy'
    tilt_pv = '13IDA:E_MonoPiezoPitch.VAL'
    roll_pv = '13IDA:E_MonoPiezoRoll.VAL'
    i0_pv   = '13IDE:I0_Volts'
    sum_pv  = '13XRM:QE2:SumAll:MeanValue_RBV'
    i0_minval = 0.1   # expected smallest I0 Voltage

    if enable_fb_pitch is None:
        # enable_fb_pitch = caget('13IDE:En:Energy') < 3000.0
        enable_fb_pitch = caget('13IDA:m65.VAL') > 46.
    #endif
    if enable_fb_roll is None:
        # enable_fb_roll = caget('13IDE:En:Energy') < 3000.0
        enable_fb_roll = caget('13IDA:m65.VAL') > 35.
    #endif

    caput('13XRM:pitch_pid.FBON', 0)
    caput('13XRM:roll_pid.FBON', 0)

    # tweak energy to force undulator to wake up
    en_current = caget(energy_pv)
    caput(energy_pv, en_current-1.0)
    sleep(0.25)

    # stop, restart Quad Electrometer
    BPM_config(prefix='13XRM:QE2:', averaging_time=0.1)

    caput(energy_pv, en_current, wait=True)

    # find best tilt value with BPM sum
    tilt_best = caget(tilt_pv)
    caput(tilt_pv, min(7, max(tilt_best, 3)))

    try:
        tilt_best, i1 = find_max_intensity(tilt_pv, linspace(-5, 5, 61), sum_pv)
    except:
        pass

    if get_dbinfo('request_abort', as_bool=True):
        return
    print(f'  pitch (BPM): {tilt_best:.3f}')

    # find best tilt value with IO
    try:
        tilt_best, i1 = find_max_intensity(tilt_pv, linspace(-3, 3, 61), i0_pv)
    except:
        pass
    #endtry
    if get_dbinfo('request_abort', as_bool=True):
        return
    #endif
    print(f'  pitch (I0): {tilt_best:.3f}')

    # find best roll with I0
    if with_roll:
        roll_best, i1 = find_max_intensity(roll_pv, linspace(-2.5, 2.5, 61), i0_pv)
        if i1 < i0_minval:
            caput(roll_pv, 5.0, wait=True)
            sleep(0.25)
            roll_best, i1 = find_max_intensity(roll_pv, linspace(-5., 5., 61), i0_pv)

        print(f' roll broad: {roll_best:.3f}')
        if get_dbinfo('request_abort', as_bool=True):
            return

    # re-find best tilt value using I0
    fast_mono_tilt()

    caput('13XRM:pitch_pid.FBON', 0)
    if enable_fb_roll:
        caput('13XRM:roll_pid.FBON', 1)
    #endif

    if enable_fb_pitch:
        sleep(0.5)
        caput('13XRM:pitch_pid.FBON', 1)
    #endif
    print('#-- set_mono_tilt done (%.2f seconds)' % (clock()-t0))
#enddef

def fast_mono_tilt():
    """
    Quick adjustment of IDE monochromator 2nd crystal tilt and roll to maximize I0

    Note:
        This is meant to be a faster, simpler version of set_mono_tilt()
    """
    t0 = clock()
    # wait_for_shutters(hours=1)
    energy_pv = '13IDE:En:Energy'
    tilt_pv = '13IDA:E_MonoPiezoPitch.VAL'
    roll_pv = '13IDA:E_MonoPiezoRoll.VAL'
    i0_pv   = '13IDE:I0_Volts'
    sum_pv  = '13XRM:QE2:SumAll:MeanValue_RBV'
    pitch_fb_save = caget('13XRM:pitch_pid.FBON')
    roll_fb_save =  caget('13XRM:roll_pid.FBON')
    energy = caget(energy_pv)

    roll_ex, tilt_ex, npts = 1.5, 0.75, 31

    caput('13XRM:pitch_pid.FBON', 0)
    caput('13XRM:roll_pid.FBON', 0)

    BPM_config(prefix='13XRM:QE2:', averaging_time=0.1)
    print(f"#-- fast_mono_tilt: {ctime()}")
    # find best roll with I0
    roll_best, i1 = find_max_intensity(roll_pv, linspace(-roll_ex, roll_ex, npts), i0_pv)
    # find best tilt value with IO
    tilt_best, i1 = find_max_intensity(tilt_pv, linspace(-tilt_ex, tilt_ex, npts), i0_pv)

    sleep(0.5)
    BPM_config(prefix='13XRM:QE2:', averaging_time=0.5, compute_offsets=True)
    sleep(0.5)

    if energy < 3000.00:
        pitch_fb_save = roll_fb_save = 1

    caput('13XRM:pitch_pid.FBON', pitch_fb_save)
    caput('13XRM:roll_pid.FBON', roll_fb_save)

    dt = clock() - t0
    print(f'#-- fast_mono_tilt done: {dt:.2f} seconds')
#enddef

def med_mono_tilt():
    """
    adjustment of IDE monochromator 2nd crystal tilt and roll to maximize I0

    Note:
        This is meant to be a faster, simpler version of set_mono_tilt()
    """
    t0 = clock()
    # wait_for_shutters(hours=1)
    energy_pv = '13IDE:En:Energy'
    tilt_pv = '13IDA:E_MonoPiezoPitch.VAL'
    roll_pv = '13IDA:E_MonoPiezoRoll.VAL'
    i0_pv   = '13IDE:I0_Volts'
    sum_pv  = '13XRM:QE2:SumAll:MeanValue_RBV'
    pitch_fb_save = caget('13XRM:pitch_pid.FBON')
    roll_fb_save =  caget('13XRM:roll_pid.FBON')
    energy = caget(energy_pv)

    roll_ex, tilt_ex, npts = 2.0, 1.0, 51

    caput('13XRM:pitch_pid.FBON', 0)
    caput('13XRM:roll_pid.FBON', 0)

    BPM_config(prefix='13XRM:QE2:', averaging_time=0.1)
    print(f"#-- fast_mono_tilt: {ctime()}")
    # find best roll with I0
    roll_best, i1 = find_max_intensity(roll_pv, linspace(-roll_ex, roll_ex, npts), i0_pv)
    # find best tilt value with IO
    tilt_best, i1 = find_max_intensity(tilt_pv, linspace(-tilt_ex, tilt_ex, npts), i0_pv)

    sleep(0.25)
    BPM_config(prefix='13XRM:QE2:', averaging_time=0.5, compute_offsets=True)
    sleep(0.25)
    caput('13XRM:pitch_pid.FBON', pitch_fb_save)
    caput('13XRM:roll_pid.FBON', roll_fb_save)

    dt = clock() - t0
    print(f'#-- fast_mono_tilt done: {dt:.2f} seconds')
#enddef

def find_proll(energy):
    move_energy(energy)
    med_mono_tilt()
    sleep(0.5)

    broll = caget('13IDA:E_MonoPiezoRoll')
    bpitch = caget('13IDA:E_MonoPiezoPitch')
    ypos = caget('13XRM:QE2:PosY:MeanValue_RBV')
    xpos = caget('13XRM:QE2:PosX:MeanValue_RBV')
    print(f"{energy:.1f}  {bpitch:.2f}   {broll:.2f} ypos={ypos:.2f} xpos={xpos:.2f}")
