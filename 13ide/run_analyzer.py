#!/usr/bin/env python
import os
import time
import numpy as np
from numpy import sin, cos, sqrt, deg2rad, pi
from epics import caget, Device, PV

DSPACES = {'si': 5.4309, 'ge': 5.658}
hc = 12398.419

ACHI = 30.0
MOTORS = {'ana_th': PV('13XRM:m8.VAL'),
          'ana_d': PV('13XRM:m7.VAL'),
          'det_y': PV('13XRM:m11.VAL'),
          'det_x': PV('13XRM:m10.VAL'),
      }


def put_motor(name, value, wait=False):
    MOTORS[name].put(value, wait=wait)

def d_analyzer(theta=0, diameter=1000):
    """sample-analyzer distance: law of cosines"""
    csq = 2*(1 + cos(2*deg2rad(90-theta)))
    return diameter*sqrt(csq)/2.0
#enddef

def detector_xy(theta):
    d_anal = d_analyzer(theta)
    h_anal = d_anal*sin(deg2rad(ACHI))
    x_anal = d_anal*cos(deg2rad(ACHI))
    dfact = sqrt(2-2*cos(deg2rad(2*(90-theta))))
    x_det = d_anal*dfact*cos(deg2rad(ACHI+theta))
    y_det = d_anal*dfact*sin(deg2rad(ACHI+theta))

    return x_det, y_det


class Analyzer(Device):
    """ """
    attrs = ('h', 'k', 'l', 'xtal', 'diam', 'Energy',
             'Energy_RBV', 'Moving', 'det_track', 'sim_mode',
             'theta', 'ana_dist', 'det_x', 'det_y')

    _nonpvs = ('_prefix', '_pvs', '_delim', 'has_new_energy', 'en_val')

    def __init__(self, prefix='13XRM:ANA:'):

        Device.__init__(self, prefix, attrs=self.attrs)
        time.sleep(0.1)
        self.has_new_energy = False
        self.en_val = -1
        self.add_callback('Energy', self.onEnergyChange)
        self._pvs['Moving'].put(0)

    def onEnergyChange(self, value, **kws):
        self.has_new_energy = True
        if value > 1000 and value < 30000:
            self.en_val = value

    def set_energy(self):
        energy = self.en_val
        if energy < 2000 or energy > 30000:
            return
        xtal = ['si', 'ge'][self.xtal]
        diam = self.diam
        h = self.h
        k = self.k
        l = self.l

        dspace = DSPACES[xtal.lower()]
        hkl = np.array([h,k,l])


        hkllen = np.sqrt((hkl**2).sum())
        theta  = np.arcsin(hkllen * hc/(2*dspace*energy))
        thref  = np.pi/2.0 - theta
        ana_d  = 0.5*diam*np.sqrt(2*(1 + np.cos(2*thref)))
        # d_det  = 2.0*diam*np.sin(thref)
        thetad = theta*180/np.pi

        det_x, det_y = detector_xy(thetad)

        self._pvs['det_x'].put(det_x)
        self._pvs['det_y'].put(det_y)
        self._pvs['theta'].put(thetad)
        self._pvs['ana_dist'].put(ana_d)

        print("#Analyzer En=%.1f %s(%d,%d,%d) at %s" % (energy, xtal.title(), h, k, l, time.ctime()))
        # print("#  Theta=%.2f, AnaZ=%.2f, DetX=%.2f, DetY=%.2f" % (thetad, ana_d, det_x, det_y))
        if not self.sim_mode:
            put_motor('ana_d', ana_d, wait=False)
            put_motor('ana_th', thetad, wait=False)
            if self.det_track:
                put_motor('det_y', det_y, wait=False)
                put_motor('det_x', det_x, wait=True)
                put_motor('det_y', det_y, wait=True)

            put_motor('ana_d', ana_d, wait=True)
            put_motor('ana_th', thetad, wait=True)

        self.has_new_energy = False
        self._pvs['Energy_RBV'].put(energy)

        self._pvs['Moving'].put(0)
        print("Energy done", time.ctime())

    def run(self):
        while True:
            time.sleep(0.1)
            if self.has_new_energy or self._pvs['Moving'].get() == 1:
                self.set_energy()



if __name__ == '__main__':
    analyzer = Analyzer()
    analyzer.run()
