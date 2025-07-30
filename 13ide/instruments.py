###

def detector_distance(distance, wait=True):
    """
    Set Sample-detector distance in mm.

    Args:
        distance (float):  Sample-detector distance in mm.
        wait (True or False):  whether to wait for move to complete [True]

    Example:
        detector_distance(60)
    """
    print('>Moving Detector %.1f (wait=%s)' % (distance, wait))
    caput('13IDE:m19.VAL', distance, wait=wait)
    _scandb.set_info('experiment_xrfdet_distance', "%.1f" % distance)
#enddef

def detectors_out():
    detector_distance(75)
    move_instrument('Eiger XRD Stages', 'out')
#enddef

def detectors_in():
    detector_distance(68)
    move_instrument('Eiger XRD Stages', '95 mm')
#enddef

def foe_slits(val='250'):
    move_instrument('FOE Slits', val)
#enddef


def ssa_hsize(hsize):
   """
   set SSA Horizontal beamsize, in mm.

   Args:
       hsize (float): SSA slit size in mm

   Example:
      ssa_hsze(0.050)
   """
   caput('13IDA:m70.VAL', hsize)
   _scandb.set_info('experiment_ssa_hwid', "%.4f" % hsize)
#enddef


def bpm_foil(foilname):
    """
    select and move to BPM Foil by name

    Parameters:
        name (string): name of foil. One of
               'Open', 'Ti', 'Cr', 'Ni', 'Al', 'Au'

    Note:
       not case-sensitive.

    Example:
       bpm_foil('Ni')

    """
    move_instrument('BPM Foil', foilname.title(), infoname='experiment_bpmfoil')
#enddef


def dhmirror_stripe(stripe='silicon', wait=True):
    """
    move double horizontal beamline mirrors to a selected stripe

    Parameters:
        stripe (string): name of stripe. One of
            'silicon', 'rhodium', 'platinum' ['silicon']
        wait (True or False): whether to wait for move
            to complete before returning [True]
    Note:
        the first letter of the stripe ('s', 'r', 'p') is
        sufficient.

    Example:
       dhmirror_stripe('rh')
    """

    stripes = {'s':'Si', 'r': 'rhodium', 'p': 'platinum'}
    name = stripes.get(stripe.lower()[0], None)
    if name is not None:
        stripe_name = name
    #endif
    move_instrument('Double H Mirror Stripes', stripe_name, wait=wait,
                    infoname='experiment_largekb_stripes')
#enddef


def kbmirror_stripe(stripe='silicon', wait=True):
    """move KB mirrors to a selected stripe

    Parameters:
        stripe (string): name of stripe. One of
            'silicon', 'rhodium', 'platinum' ['silicon']
        wait (True or False): whether to wait for move
            to complete before returning [True]

    Examples:
        kbmirror_stripe('silicon')
    """
    stripes = {'s':'silicon',  'r': 'rhodium',  'p': 'platinum'}
    name = stripes.get(stripe.lower()[0], None)
    if name is not None:
        print("Moving KB Mirror Stripes ", name)
        move_instrument('Small KB Mirror Stripes',
                        name, wait=wait,
                        infoname='experiment_smallkb_stripes')

def focus(position='2um'):
    """move small KB mirrors to named focus condition
    """
    move_instrument('Small KBs Focus', position, wait=True,
                    infoname='experiment_beamsize')
#enddef



def defocus():
    """move small KB mirrors to 50x50 microns"""
    move_instrument('Small KBs Focus', '50 um', wait=True, infoname='experiment_beamsize')

def focus_50um():
    """move small KB mirrors to 50x50 microns"""
    move_instrument('Small KBs Focus', '50 um', wait=True, infoname='experiment_beamsize')

def focus_25um():
    """move small KB mirrors to 25 microns"""
    move_instrument('Small KBs Focus', '25 um', wait=True, infoname='experiment_beamsize')


def focus_10um():
    """move small KB mirrors to 10 microns"""
    move_instrument('Small KBs Focus', '10 um', wait=True, infoname='experiment_beamsize')

def focus_2um():
    """move small KB mirrors to 2 microns"""
    move_instrument('Small KBs Focus', '2 um', wait=True, infoname='experiment_beamsize')

#

def move_rotary1(value=None, wait=True):
    "move rotary1 stage to value"
    if value is not None:
        caput('13IDE:m31.VAL', value, wait=wait)
    #endif
#enddef

def move_rotary2(value=None, wait=True):
    "move rotary2 stage to value"
    if value is not None:
        caput('13IDE:m32.VAL', value, wait=wait)
    #endif
#enddef

def rotate_azimuth(target=None):
   """
   rotate sample azimuthal angle
   """
   direc = 0
   if target is None: target = 1
   if target < 0:
       target = -target
       direc = 1
   #endif
   if target > 0:
      caput('rpi_2:Motor1Dir', direc)
      sleep(0.5)

      caput('rpi_2:Motor1Steps.VAL', target)
      sleep(0.5)
      caput('rpi_2:Motor1Move.VAL', 1)
      # caput('rpi_2:Motor1Move.VAL', 0)
   #endif
#enddef
