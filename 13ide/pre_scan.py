##
## The function `pre_scan_command` is run automatically
## just before many of the internal scanning commands:
##
##  * before each 1-d scan, including XAFS Scans
##  * before each 2-d mesh scan,
##  * before each row of a 2-d slew scan.

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
    print(f"Pre Scan: {DATE} {row=}")
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
    #
    mono_energy = estart = caget('13IDE:En:Energy')
    scantype = kws.get('scantype', 'map')
    with_gapscan = kws.get('with_gapscan', False)
    if scantype == 'qxafs' and with_gapscan:
        e0     = kws.get('e0', mono_energy)
        en_array = np.array(kws.get('energy', [mono_energy]))
        dwelltime = kws.get('dwelltime', 0.25)
        valid_gapscan = enable_gapscan(energy=en_array, e0=e0, dwelltime=dwelltime)
        estart = en_array[1]
        print("Pre Scan using GapScan:", e0, dwelltime, len(en_array), valid_gapscan)

    # print("Would save sample images:" ):
    # save_sample_images()

    print("fast_mono_tilt() at energy ", mono_energy, estart)
    fast_mono_tilt()
    if mono_energy < 3000.00:
        feedback_on(roll=True, pitch=True)
        if scantype == 'qxafs' and with_gapscan:
            caput('13IDE:En:Energy', estart)
            sleep(5.0)

    pitch_val = caget('13IDA:E_MonoPiezoPitch.VAL')
    roll_val = caget('13IDA:E_MonoPiezoRoll.VAL')
    _scandb.set_info('mono_pitch_val', f"{pitch_val:.3f}")
    _scandb.set_info('mono_pitch_roll', f"{roll_val:.3f}")

    sleep(0.1)
    now = time()
    _scandb.set_info('prescan_lasttime', int(time()))
    print(f'#pre_scan done ({now-t0:.2f})')
    return None

#     # caput('13IDE:Unidig1Bo0', 0)
#     open_shutter(wait=True)
#     sleep(0.5)
#
#     # Step 3: allow for short-circuit to exit pre_scan now.
#     i0_llim = float(caget('13XRM:ION:FluxLowLimit'))
#     if i0_llim  < 1000:
#         print("#pre_scan: not waiting for shutter.")
#         return
#     #endif
#
#     # Step 3.5: check if ID is in Rotary mode and try to fix it if so.
#     badmode = 'Rotary'
#     print('#pre_scan: undulator mode = ', caget('ID13us:EncoderSelect', as_ostring=True))
#     if badmode == caget('ID13us:EncoderSelect', as_string=True):
#         print("#pre_scan: undulator is in Rotary mode!!!!!")
# #        energy = caget('13IDE:En:Energy')
# #         id_energy = caget('ID13us:ScanEnergy')
# #         caput('ID13us:ScanEnergy', id_energy+0.50, wait=True)
# #         if badmode == caget('ID13us:EncoderSelect', as_string=True):
# #             caput('ID13us:ScanEnergy', id_energy+0.75, wait=True)
# #         #endif
# #         sleep(0.25)
# #         caput('ID13us:ScanEnergy', id_energy+0.05, wait=True)
# #         sleep(0.25)
# #         caget('13IDE:En:Energy', energy+2.0, wait=True)
# #         sleep(0.25)
# #         caget('13IDE:En:Energy', energy, wait=True)
#     #endif
#     # Step 3.5: check if ID is in Rotary mode and try to fix it if it is.
#     if badmode == caget('ID13us:EncoderSelect', as_string=True):
#         print("#pre_scan: undulator is still in Rotary mode!!!!")
#     #endif
#
#
#     # Step 4: wait up to 4 hours for shutters to open
#     #         try opening shutters every 10 minutes
#     shutter_status = (caget('13IDA:eps_mbbi25'), Caget('13IDA:eps_mbbi27'))
#     if shutter_status != (1, 1):
#         print("#pre_scan: waiting for shutters to open")
#         t0 = systime()
#         while shutter_status != (1, 1) and (systime()-t0 < 4*3600.0):
#             shutter_status = (caget('13IDA:eps_mbbi25'), caget('13IDA:eps_mbbi27'))
#             sleep(1.0)
#             if int(systime()) % 180 < 10:
#                 caput('13IDA:OpenFEShutter.PROC', 1)
#                 caput('13IDA:OpenEShutter.PROC',  1)
#                 sleep(15.0)
#             #endif
#             if check_scan_abort():
#                 break
#             #endif
#         #endwhile
#         if check_scan_abort():
#            return
#         #endif
#     #endif
#
#     # Step 5: do fast mono tilt
#     energy = caget('13IDE:En:Energy')
#     if energy < 3000.0:
#         caput('13XRM:pitch_pid.FBON', 0)
#         caput('13XRM:roll_pid.FBON',  0)
#         caput('13IDE:En:Energy', energy+0.1, wait=True)
#         caput('13IDE:En:Energy', energy)
#         tilt_save = caget('13IDE:userTran1.M')
#         roll_save = caget('13IDE:userTran1.N')
#
#         i0_flux = float(caget('13XRM:ION:FluxOut'))
#         i0_llim = float(caget('13XRM:ION:FluxLowLimit'))
#         if (i0_flux < i0_llim):
#             sleep(0.25)
#             tilt_save = caget('13IDE:userTran1.M')
#             roll_save = caget('13IDE:userTran1.N')
#             caput('13IDA:DAC1_7.VAL',   min(9.5, max(0.5, tilt_save)))
#             caput('13IDA:DAC1_8.VAL',   min(9.5, max(0.5, roll_save)))
#             print(" set tilt and roll to ", tilt_save, roll_save)
#         #endif
#         sleep(1.0)
#         print("fast_mono_tilt() at energy below 3000")
#         fast_mono_tilt()
#         sleep(1.0)
#         caput('13XRM:pitch_pid.FBON', (energy < 2700))
#         # caput('13XRM:roll_pid.FBON',  1)
#     else:
#         caput('13IDE:En:Energy', energy+0.1, wait=True)
#         caput('13IDE:En:Energy', energy)
#         sleep(0.1)
#         print("fast_mono_tilt() at energy ", energy)
#         fast_mono_tilt()
#     #endif
#
#     i0_flux = float(caget('13XRM:ION:FluxOut'))
#     i0_llim = float(caget('13XRM:ION:FluxLowLimit'))
#     # Step 6: if flux is low, wait a short time
#     if (i0_flux < i0_llim):
#         print("#pre_scan: waiting for I0 flux %.5g, expecting %.5g" %(i0_flux, i0_llim ))
#         # at low energy, allow for feedback to catch up
#         waittime = 10.0
#         if energy < 3000.0:
#             sleep(2)
#         #endif
#         t0 = systime()
#         i0_flux = float(caget('13XRM:ION:FluxOut'))
#         i0_llim = float(caget('13XRM:ION:FluxLowLimit'))
#         while i0_flux < i0_llim and (systime()-t0) < waittime:
#             sleep(1)
#             i0_flux = float(caget('13XRM:ION:FluxOut'))
#             i0_llim = float(caget('13XRM:ION:FluxLowLimit'))
#             if check_scan_abort():
#                 break
#             #endif
#         #endwhile
#         if check_scan_abort():
#            return
#         #endif
#     #endif
#
#     # Step 7: if flux is still low, or autotune time is expired,
#     # do a full set_mono_tilt()
#     autotune_lastts = caget('13XRM:ION:AutotuneTS')
#     autotune_delay  = 3600. * float(caget('13XRM:ION:AutotuneDelay'))
#     autotune_needed = (systime() - autotune_lastts) > autotune_delay
#
#     if autotune_needed or (i0_flux < i0_llim):
#         caput('13XRM:pitch_pid.FBON', 0)
#         caput('13XRM:roll_pid.FBON',  0)
#         tilt_save = caget('13IDE:userTran1.M')
#         roll_save = caget('13IDE:userTran1.N')
#         caput('13IDA:DAC1_7.VAL',   min(9.5, max(0.5, tilt_save)))
#         caput('13IDA:DAC1_8.VAL',   min(9.5, max(0.5, roll_save)))
#         if autotune_needed:
#             print("#pre_scan: autotune needed after %d hours" % (autotune_delay))
#         else:
#             print("#pre_scan: i0 flux too low. %.5g, expected %.5g" % (i0_flux, i0_llim))
#         #endif
#         set_mono_tilt()
#         if check_scan_abort():
#             return
#         #endif
#     #endif
#
#     # Step 8: if flux is still too low, wait another fifteen minutes,
#     #         hoping for operator intervention
#     i0_flux = float(caget('13XRM:ION:FluxOut'))
#     i0_llim = float(caget('13XRM:ION:FluxLowLimit'))
#     energy = caget('13IDE:En:Energy')
#     en_off = 0
#     t0 = systime()
#     if (i0_flux < i0_llim):
#         print("#pre_scan: I0 flux still too low, waiting for 1 hour (hit Abort to cancel)")
#     #endif
#
#     while i0_flux < i0_llim and systime()-t0 < 900.0:
#         i0_flux = float(caget('13XRM:ION:FluxOut'))
#         i0_llim = float(caget('13XRM:ION:FluxLowLimit'))
#         sleep(1.0)
#         # may need to tweak the energy (ID may be wrong)
#         if systime() % 120.0 < 5:
#             en_off  += 0.1
#             if en_off > 2.02:
#                 en_off = -2.0
#             #endif
#             caput('13IDE:En:Energy', energy + en_off)
#             sleep(5)
#         #endif
#         if check_scan_abort():
#             break
#         #endif
#     #endwhile
#
#     if check_scan_abort():
#         return
#     #endif
#     # save these pitch / roll DAC positions for later use
#
#     if i0_flux > i0_llim:
#         tilt_save = caget('13IDA:DAC1_7.VAL')
#         roll_save = caget('13IDA:DAC1_8.VAL')
#         caput('13IDE:userTran1.M', tilt_save)
#         caput('13IDE:userTran1.N', roll_save)
#     #endif
#
#     use_roll  = roll_fb or (energy < 3900.0)
#     use_pitch = energy < 2700.0
#     mono_angle = caget('13IDA:m65.VAL')
#     use_roll  = roll_fb or (mono_angle > 37.0)
#     # use_pitch = mono_angle > 47.0
#
#     # use_roll  = roll_fb or (mono_angle > 26.0)
#     # use_pitch = mono_angle > 25.0
#     feedback_on(roll=use_roll, pitch=use_pitch)
#
#
#     now = systime()

# enddef
#
def post_scan_command(row=0):
    sleep(0.05)
    disable_gapscan()
    pval = _scandb.get_info('mono_pitch_val')
    rval = _scandb.get_info('mono_pitch_roll')
    fb_pitch_on = caget('13XRM:pitch_pid.FBON')
    fb_roll_on  = caget('13XRM:roll_pid.FBON')
    if fb_pitch_on or fb_roll_on:
        print("Post Scan Command, restore mono pitch ", pval, rval)
        caput('13XRM:pitch_pid.FBON', 0)
        caput('13XRM:roll_pid.FBON', 0)
        caput('13IDA:E_MonoPiezoPitch.VAL', pval)
        caput('13IDA:E_MonoPiezoRoll.VAL', rval)
        sleep(2)
        caput('13XRM:pitch_pid.FBON', 1)
        caput('13XRM:roll_pid.FBON', 1)
#enddef
