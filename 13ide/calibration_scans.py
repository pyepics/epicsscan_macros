import numpy as np




############


def use_3rd_harmonic():
    caput('13IDE:En:Energy', 9024)
    caput('13IDE:En:id_off.VAL', -0.126)
    caput('13IDE:En:id_harmonic', 3)
    caput('S13ID:USID:HarmonicValueC', 3)
    caput('13IDE:En:Energy', 9025)
    caput('13IDA:m8.VAL', 0.15)
    caput('13IDA:m6.VAL', 0.1)
    sleep(2)
    set_mono_tilt()

def set_foe_slit(vwid, hwid):
    "vwid and hwid expected in microns"
    if hwid > 2.5:
        hwid = hwid / 1000.
    caput('13IDA:m6.VAL', hwid)
    if vwid > 2.5:
        vwid = vwid / 1000.
    caput('13IDA:m8.VAL', vwid)

    sens = 10
    if vwid*hwid > 20000:
        sens = 20
    cur = int(caget('13IDE:A2sens_num.VAL', as_string=True))

    set_i1amp_gain(sens, 'uA/V', offset=25)
    set_i2amp_gain(sens, 'uA/V', offset=25)

    open_shutter()
    print("@Set vwid/hwid ", vwid, hwid)
    sleep(0.25)
    autoset_gain(prefix='13IDE:A1', offset=40)
    scaler_mode(mode='oneshot')

    if sens != cur:
        collect_offsets()
    sleep(0.25)


def foe_slit_scan(harm=1):
    for hwid in (50, 100, 200, 400, 500, 700, 1000):
        caput('13IDA:m6.VAL', 0.001*hwid, wait=True)
        for vwid in (50, 100, 150, 200, 250, 350, 400, 500, 600):
            needs_offset = vwid in (50, 200, 400)
            if vwid == 50:
                sens = 2
            elif vwid == 200:
                sens = 5
            elif vwid == 400:
                sens = 10
            set_i1amp_gain(sens, 'uA/V', offset=25)
            set_i2amp_gain(sens, 'uA/V', offset=25)

            caput('13IDA:m8.VAL', 0.001*vwid, wait=True)
            print("@Set vwid/hwid ", vwid, hwid)
            open_shutter()
            print("@Set Gain")
            fast_mono_tilt()
            fname = f'Calib9KeV_harmonic{harm}_foe{vwid}x{hwid}.001'
            print("@Do Scan for ", fname)
            do_scan('Calib9keV',  filename=fname)
            if check_scan_abort():
                print("@ABORT SEEN")
                return
        caput('13IDA:m8.VAL', 0.025)
    caput('13IDA:m6.VAL', 0.1)
    print("Done")

def foe_slit_scan311(harm=1):
    for hwid in (50, 100, 200, 400, 500):
        caput('13IDA:m6.VAL', 0.001*hwid)
        for vwid in (50, 100, 150, 200, 250, 400, 500):
            needs_offset = vwid in (50, 150, 400)
            if vwid == 50:
                sens = 2
            elif vwid == 150:
                sens = 5
            elif vwid == 400:
                sens = 10
            set_i1amp_gain(sens, 'uA/V', offset=25)
            set_i2amp_gain(sens, 'uA/V', offset=25)
            _scandb.set_info('needs_offset', needs_offset)
            caput('13IDA:m8.VAL', 0.001*vwid, wait=True)
            open_shutter()
            print("@Set vwid/hwid ", vwid, hwid)
            sleep(0.25)
            autoset_i0amp_gain()
            fname = f'Cal_Si311_9KeV_harmonic{harm}_foe{vwid}x{hwid}.001'
            print("@Do Scan for ", fname)
            do_scan('Calib311_9keV',  filename=fname)
            if check_scan_abort():
                print("@ABORT SEEN")
                return
        caput('13IDA:m8.VAL', 0.05)
    caput('13IDA:m6.VAL', 0.011, wait=True)
    sleep(0.5)
    caput('13IDA:m6.VAL', 0.05)
    print("Done")
