# def move_to_12kev():
#    "move to As K edge"
#    open_shutter()
#    set_i0amp_gain(100, 'nA/V')
#    set_i1amp_gain(500, 'nA/V')
#    move_to_edge('As', 'K')
#    detector_distance(120)
#    move_energy(12000)
#    autoset_i0amp_gain(take_offsets=False)
#    collect_offsets()
#
# def move_to_as():
#    "move to As K edge"
#    open_shutter()
#    set_i0amp_gain(100, 'nA/V')
#    set_i1amp_gain(500, 'nA/V')
#    detector_distance(120)
#    move_to_edge('As', 'K')
#    autoset_i0amp_gain(take_offsets=False)
#    collect_offsets()
#
#
# def move_to_19kev():
#    "move to Zr K edge"
#    open_shutter()
#    set_i0amp_gain(20, 'nA/V')
#    set_i1amp_gain(500, 'nA/V')
#    move_to_edge('Zr', 'K')
#    move_energy(19000)
#    detector_distance(120)
#    set_filter(thickness=200)
#    autoset_i0amp_gain(take_offsets=False)
#    collect_offsets()
#
#
# def move_to_cu():
#    "move to Cu K edge"
#    open_shutter()
#    set_i0amp_gain(100, 'nA/V')
#    set_i1amp_gain(500, 'nA/V')
#    move_to_edge('Cu', 'K')
#    autoset_i0amp_gain(take_offsets=False)
#    collect_offsets()
#
# def move_to_fe():
#    "move to Fe K edge"
#    open_shutter()
#    set_i0amp_gain(100, 'nA/V')
#    set_i1amp_gain(500, 'nA/V')
#    set_filter(thickness=300)
#    detector_distance(120)
#    move_to_edge('Fe', 'K')
#    autoset_i0amp_gain(take_offsets=False)
#    collect_offsets()
#
# def move_to_mn():
#    "move to Mn K edge"
#    open_shutter()
#    set_i0amp_gain(500, 'nA/V')
#    set_i1amp_gain(500, 'nA/V')
#    set_filter(thickness=0)
#    move_to_edge('Mn', 'K')
#    detector_distance(75)
#    autoset_i0amp_gain(take_offsets=False)
#    collect_offsets()
#
# def move_to_ti():
#    "move to Ti K edge"
#    open_shutter()
#    set_filter(thickness=0)
#    set_i0amp_gain(200, 'nA/V')
#    set_i1amp_gain(10, 'nA/V')
#    move_to_edge('Ti', 'K')
#    autoset_i0amp_gain(take_offsets=False)
#    collect_offsets()
#
# def move_to_eu():
#    "move to Eu L3 edge"
#    open_shutter()
#    set_filter(thickness=100)
#    set_i0amp_gain(100, 'nA/V')
#    set_i1amp_gain(20, 'nA/V')
#    move_to_edge('Eu', 'L3')
#    autoset_i0amp_gain(take_offsets=False)
#    collect_offsets()
#
# def move_to_au():
#    "move to Au L3 edge"
#    open_shutter()
#    set_i0amp_gain(50, 'nA/V')
#    set_i1amp_gain(200, 'nA/V')
#    move_to_edge('Au', 'L3')
#    autoset_i0amp_gain(take_offsets=False)
#    collect_offsets()


def move_to_v():
   "move to V K edge"
   open_shutter()
   set_i0amp_gain(10, 'nA/V')
   set_i1amp_gain(2, 'nA/V')
   kbmirror_stripe('silicon', wait=False)
   move_to_edge('V', 'K')
   collect_offsets()

def move_to_cr():
   "move to Cr K edge"
   open_shutter()
   set_i0amp_gain(10, 'nA/V')
   set_i1amp_gain(1, 'nA/V')
   kbmirror_stripe('silicon', wait=False)
   move_to_edge('Cr', 'K')
   collect_offsets()

def move_to_fe():
   "move to Fe K edge"
   open_shutter()
   set_i0amp_gain(5, 'nA/V')
   set_i1amp_gain(100, 'pA/V')
   move_to_edge('Fe', 'K')
   autoset_i0amp_gain(take_offsets=False)
   autoset_i1amp_gain(take_offsets=False)
   collect_offsets()

def move_to_co():
   "move to Co K edge"
   open_shutter()
   set_i0amp_gain(5, 'nA/V')
   set_i1amp_gain(100, 'pA/V')
   move_to_edge('Co', 'K')
   autoset_i0amp_gain(take_offsets=False)
   autoset_i1amp_gain(take_offsets=False)
   collect_offsets()


def move_to_ni():
   "move to Ni K edge"
   open_shutter()
   set_i0amp_gain(5, 'nA/V')
   set_i1amp_gain(100, 'pA/V')
   move_to_edge('Ni', 'K')
   autoset_i0amp_gain(take_offsets=False)
   autoset_i1amp_gain(take_offsets=False)
   collect_offsets()


def move_to_cu():
   "move to Cu K edge"
   open_shutter()
   set_i0amp_gain(2, 'nA/V')
   move_to_edge('Cu', 'K')
   autoset_i0amp_gain(take_offsets=False)
   autoset_i1amp_gain(take_offsets=False)
   collect_offsets()

def move_to_zn():
   "move to Zn K edge"
   open_shutter()
   move_to_edge('Zn', 'K')
   autoset_i0amp_gain(take_offsets=False)
   autoset_i1amp_gain(take_offsets=False)
   collect_offsets()

def move_to_ge():
   "move to Ge K edge"
   open_shutter()
   set_i0amp_gain(2, 'nA/V')
   move_to_edge('Ge', 'K')
   autoset_i0amp_gain(take_offsets=False)
   autoset_i1amp_gain(take_offsets=False)
   collect_offsets()

def move_to_as():
   "move to As K edge"
   open_shutter()
   set_i0amp_gain(2, 'nA/V')
   set_i1amp_gain(5, 'nA/V')
   move_to_edge('As', 'K')
   autoset_i0amp_gain(take_offsets=False)
   autoset_i1amp_gain(take_offsets=False)
   collect_offsets()

def move_to_se():
   "move to Se K edge"
   open_shutter()
   set_i0amp_gain(1, 'nA/V')
   set_i1amp_gain(5, 'nA/V')
   move_to_edge('Se', 'K')
   autoset_i0amp_gain(take_offsets=False)
   autoset_i1amp_gain(take_offsets=False)
   collect_offsets()

def move_to_br():
   "move to Br K edge"
   open_shutter()
   set_i0amp_gain(1, 'nA/V')
   move_to_edge('Br', 'K')
   autoset_i0amp_gain(take_offsets=False)
   autoset_i1amp_gain(take_offsets=False)
   collect_offsets()

def move_to_zr():
   "move to Zr K edge"
   open_shutter()
   set_i0amp_gain(500, 'pA/V')
   set_i1amp_gain(10, 'nA/V')
   move_to_edge('Zr', 'K')
   autoset_i0amp_gain(take_offsets=False)
   autoset_i1amp_gain(take_offsets=False)
   collect_offsets()

def move_to_mo():
   "move to Mo K edge"
   open_shutter()
   set_i0amp_gain(500, 'pA/V')
   set_i1amp_gain(10, 'nA/V')
   move_to_edge('Mo', 'K')
   collect_offsets()

# def move_to_as():
#    "move to As K edge"
#    open_shutter()
#    set_i0amp_gain(10, 'nA/V')
#    kbmirror_stripe('rhodium', wait=False)
#    move_to_edge('As', 'K')
#    autoset_i0amp_gain(take_offsets=False)
#    collect_offsets()
#
# def move_to_sr():
#    "move to Sr K edge"
#    open_shutter()
#    set_i0amp_gain(5, 'nA/V')
#    kbmirror_stripe('rhodium', wait=False)
#    move_to_edge('Sr', 'K')
#    autoset_i0amp_gain(take_offsets=False)
#    collect_offsets()
#
# def move_to_pb():
#    "move to Pb L3 edge"
#    open_shutter()
#    set_i0amp_gain(10, 'nA/V')
#    kbmirror_stripe('rhodium', wait=False)
#    move_to_edge('Pb', 'L3')
#    autoset_i0amp_gain(take_offsets=False)
#    collect_offsets()
#
# def move_to_18keV():
#     kbmirror_stripe('rhodium', wait=False)
#     move_to_edge('Zr', 'K', with_tilt=False)
#     move_energy(18000)
#     set_i0amp_gain(5, 'nA/V', offset=40)
#     sleep(2)
#     set_mono_tilt()
#
# def move_to_3500eV():
#     kbmirror_stripe('silicon', wait=False)
#     move_to_edge('Ca', 'K', with_tilt=False)
#     move_energy(3500)
#     set_i0amp_gain(50, 'nA/V', offset=40)
#     sleep(2)
#     set_mono_tilt()
#
#
# def expose_test():
#     move_stage('finey', 0, wait=True)
#     expose(120)
#
#     move_stage('finey', 0.05, wait=True)
#     expose(600)
#
#     move_stage('finey', 0.10, wait=True)
#     expose(3600)
#
#     move_stage('finey', 0.15, wait=True)
#     expose(4*3600)
#     close_shutter()


def filter50():
   set_filter(50)
   set_i0amp_gain(2, 'nA/V')
   collect_offsets()
   close_shutter()

def filter100():
   set_filter(100)
   set_i0amp_gain(1, 'nA/V')
   collect_offsets()
   close_shutter()

def filter150():
   set_filter(150)
   set_i0amp_gain(500, 'pA/V')
   collect_offsets()
   close_shutter()

def filter200():
   set_filter(200)
   set_i0amp_gain(200, 'pA/V')
   collect_offsets()
   close_shutter()

def filter250():
   set_filter(250)
   set_i0amp_gain(100, 'pA/V')
   collect_offsets()
   close_shutter()

def filter300():
   set_filter(300)
   set_i0amp_gain(50, 'pA/V')
   collect_offsets()
   close_shutter()

def filter350():
   set_filter(350)
   set_i0amp_gain(10, 'pA/V')
   collect_offsets()
   close_shutter()
