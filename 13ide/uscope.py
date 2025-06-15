__doc__ = """
Code to support Off-line Microscope and transfer of coordinates to Sample Stage

main functions:

uscope2sample(suffix=''):

   transfer all named positions saved for the IDE Microscope (off-line)
   to IDE SampleStage (on-line), applying the rotation matrix saved by
   the function `make_uscope_rotation()`

make_uscope_rotation()

   calculate and store best rotation matrix to transform positions from
   the IDE Microscope (off-line) to IDE SampleStage (on-line).

   this uses position names that are the same in both instruments, and
   requires at least 6 such positions. That is, save positions with the
   same names in both the IDE_Microscope and IDE_SampleStage.
   Positions names not found in both instruments are ignored.
"""

import json
from lmfit import minimize, Parameters, report_fit
import numpy as np

def affine_matrix_from_points(v0, v1, scale=True, usesvd=True):
    """Return affine transform matrix to register two point sets.

    v0 and v1 are shape (ndims, *) arrays of at least ndims non-homogeneous
    coordinates, where ndims is the dimensionality of the coordinate space.

    A similarity transformation matrix is returned.
    If also scale is False, a rigid/Euclidean transformation matrix
    is returned.

    By default the algorithm by Hartley and Zissermann [15] is used.
    If usesvd is True, similarity and Euclidean transformation matrices
    are calculated by minimizing the weighted sum of squared deviations
    (RMSD) according to the algorithm by Kabsch [8].
    Otherwise, and if ndims is 3, the quaternion based algorithm by Horn [9]
    is used, which is slower when using this Python implementation.

    The returned matrix performs rotation, translation and uniform scaling
    (if specified).

    >>> v0 = [[0, 1031, 1031, 0], [0, 0, 1600, 1600]]
    >>> v1 = [[675, 826, 826, 677], [55, 52, 281, 277]]
    >>> affine_matrix_from_points(v0, v1)
    array([[   0.14549,    0.00062,  675.50008],
           [   0.00048,    0.14094,   53.24971],
           [   0.     ,    0.     ,    1.     ]])
    >>> T = translation_matrix(np.random.random(3)-0.5)
    >>> R = random_rotation_matrix(np.random.random(3))
    >>> S = scale_matrix(random.random())
    >>> M = concatenate_matrices(T, R, S)
    >>> v0 = (np.random.rand(4, 100) - 0.5) * 20
    >>> v0[3] = 1
    >>> v1 = np.dot(M, v0)
    >>> v0[:3] += np.random.normal(0, 1e-8, 300).reshape(3, -1)
    >>> M = affine_matrix_from_points(v0[:3], v1[:3])
    >>> np.allclose(v1, np.dot(M, v0))
    True

    More examples in superimposition_matrix()

    """

    v0 = np.array(v0, dtype=np.float64, copy=True)
    v1 = np.array(v1, dtype=np.float64, copy=True)

    ndims = v0.shape[0]
    if ndims < 2 or v0.shape[1] < ndims or v0.shape != v1.shape:
        raise ValueError("input arrays are of wrong shape or type")

    # move centroids to origin
    t0 = -np.mean(v0, axis=1)
    M0 = np.identity(ndims+1)
    M0[:ndims, ndims] = t0
    v0 += t0.reshape(ndims, 1)
    t1 = -np.mean(v1, axis=1)
    M1 = np.identity(ndims+1)
    M1[:ndims, ndims] = t1
    v1 += t1.reshape(ndims, 1)

    if usesvd or ndims != 3:
        # Rigid transformation via SVD of covariance matrix
        u, s, vh = np.linalg.svd(np.dot(v1, v0.T))
        # rotation matrix from SVD orthonormal bases
        R = np.dot(u, vh)
        if np.linalg.det(R) < 0.0:
            # R does not constitute right handed system
            R -= np.outer(u[:, ndims-1], vh[ndims-1, :]*2.0)
            s[-1] *= -1.0
        # homogeneous transformation matrix
        M = np.identity(ndims+1)
        M[:ndims, :ndims] = R
    else:
        # Rigid transformation matrix via quaternion
        # compute symmetric matrix N
        xx, yy, zz = np.sum(v0 * v1, axis=1)
        xy, yz, zx = np.sum(v0 * np.roll(v1, -1, axis=0), axis=1)
        xz, yx, zy = np.sum(v0 * np.roll(v1, -2, axis=0), axis=1)
        N = [[xx+yy+zz, 0.0,      0.0,      0.0],
             [yz-zy,    xx-yy-zz, 0.0,      0.0],
             [zx-xz,    xy+yx,    yy-xx-zz, 0.0],
             [xy-yx,    zx+xz,    yz+zy,    zz-xx-yy]]
        # quaternion: eigenvector corresponding to most positive eigenvalue
        w, V = np.linalg.eigh(N)
        q = V[:, np.argmax(w)]
        q /= vector_norm(q)  # unit quaternion
        # homogeneous transformation matrix
        M = quaternion_matrix(q)

    if scale:
        # Affine transformation; scale is ratio of RMS deviations from centroid
        v0 *= v0
        v1 *= v1
        M[:ndims, :ndims] *= np.sqrt(np.sum(v1) / np.sum(v0))

    # move centroids back
    M = np.dot(np.linalg.inv(M1), np.dot(M, M0))
    M /= M[ndims, ndims]
    return M


def superimposition_matrix(v0, v1, scale=False, usesvd=True):
    """Return matrix to transform given 3D point set into second point set.

    v0 and v1 are shape (3, *) or (4, *) arrays of at least 3 points.

    The parameters scale and usesvd are explained in the more general
    affine_matrix_from_points function.

    The returned matrix is a similarity or Euclidean transformation matrix.
    This function has a fast C implementation in transformations.c.

    >>> v0 = np.random.rand(3, 10)
    >>> M = superimposition_matrix(v0, v0)
    >>> np.allclose(M, np.identity(4))
    True
    >>> R = random_rotation_matrix(np.random.random(3))
    >>> v0 = [[1,0,0], [0,1,0], [0,0,1], [1,1,1]]
    >>> v1 = np.dot(R, v0)
    >>> M = superimposition_matrix(v0, v1)
    >>> np.allclose(v1, np.dot(M, v0))
    True
    >>> v0 = (np.random.rand(4, 100) - 0.5) * 20
    >>> v0[3] = 1
    >>> v1 = np.dot(R, v0)
    >>> M = superimposition_matrix(v0, v1)
    >>> np.allclose(v1, np.dot(M, v0))
    True
    >>> S = scale_matrix(random.random())
    >>> T = translation_matrix(np.random.random(3)-0.5)
    >>> M = concatenate_matrices(T, R, S)
    >>> v1 = np.dot(M, v0)
    >>> v0[:3] += np.random.normal(0, 1e-9, 300).reshape(3, -1)
    >>> M = superimposition_matrix(v0, v1, scale=True)
    >>> np.allclose(v1, np.dot(M, v0))
    True
    >>> M = superimposition_matrix(v0, v1, scale=True, usesvd=False)
    >>> np.allclose(v1, np.dot(M, v0))
    True
    >>> v = np.empty((4, 100, 3))
    >>> v[:, :, 0] = v0
    >>> M = superimposition_matrix(v0, v1, scale=True, usesvd=False)
    >>> np.allclose(v1, np.dot(M, v[:, :, 0]))
    True

    """
    v0 = np.array(v0, dtype=np.float64)[:3]
    v1 = np.array(v1, dtype=np.float64)[:3]
    print("XX  ", v0, v1)
    return affine_matrix_from_points(v0, v1, scale=scale, usesvd=usesvd)


USCOPE_NAME = 'IDE_Microscope'
USCOPE_XYZ = ['13IDE:m1.VAL', '13IDE:m2.VAL', '13IDE:m3.VAL']

##
## SSTAGE_NAME = 'IDE_SampleStage'
##
SSTAGE_NAME = 'SampleStage_VP5ZA'
SSTAGE_NAME = 'SampleStage_4rot'
SSTAGE_NAME = 'SampleStage'
SSTAGE_XYZ = ['13XRM:m4.VAL', '13XRM:m5.VAL', '13XRM:m3.VAL']

def read_uscope_xyz(name=USCOPE_NAME):
    """
    read XYZ Positions from Offline Microscope Instrument
    returns dictionary of PositionName: (x, y, z)
    """
    out = {}
    for pname in _instdb.get_positionlist(name):
        v = _instdb.get_position_vals(name, pname)
        out[pname]  = [v[p] for p in USCOPE_XYZ]
    #endfor

    return out
#enddef

def read_sample_xyz(name=SSTAGE_NAME):
    """
    read XYZ Positions from SampleStage Instrument
    returns dictionary of PositionName: (x, y, z)

    Note: FineX, FineY and Theta stages are not included
    """
    out = {}
    for pname in _instdb.get_positionlist(name):
        v = _instdb.get_position_vals(name, pname)
        if SSTAGE_XYZ[0] in v:
            out[pname]  = [v[p] for p in SSTAGE_XYZ]
        #endif
    #endfor
    return out
#enddef


def params2rotmatrix(params, mat):
    """--private--  turn fitting parameters
    into rotation matrix
    """
    mat[0][1] = params['c01'].value
    mat[1][0] = params['c10'].value
    mat[0][2] = params['c02'].value
    mat[2][0] = params['c20'].value
    mat[1][2] = params['c12'].value
    mat[2][1] = params['c21'].value
    return mat
#enddef

def resid_rotmatrix(params, mat, v1, v2):
    "--private-- resdiual function for fit"
    mat = params2rotmatrix(params, mat)
    return (v2 - dot(mat, v1)).flatten()
#enddef


def calc_rotmatrix(d1, d2):
    """get best-fit rotation matrix to transform coordinates
    from 1st position dict into the 2nd position dict
    """
    labels = []
    d2keys = d2.keys()
    for x in d1.keys():
        if x in d2keys:
            labels.append(x)
        #endif
    #endfor
    labels.sort()
    if len(labels) < 6:
        print("""Error: need at least 6 saved positions
  in common to calculate rotation matrix""")
        return None, None, None
    #endif
    print("Calculating Rotation Matrix using Labels:")
    print(labels)
    v1 = ones((4, len(labels)))
    v2 = ones((4, len(labels)))
    for i, label in enumerate(labels):
        v1[0, i] = d1[label][0]
        v1[1, i] = d1[label][1]
        v1[2, i] = d1[label][2]
        v2[0, i] = d2[label][0]
        v2[1, i] = d2[label][1]
        v2[2, i] = d2[label][2]
    #endfor

    # get initial rotation matrix, assuming that
    # there are orthogonal coordinate systems.
    mat = superimposition_matrix(v1, v2, scale=True)
    print("Got Mat ", mat)

    params = Parameters()
    params.add('c10', value=mat[1][0])
    params.add('c01', value=mat[0][1])
    params.add('c20', value=mat[2][0])
    params.add('c02', value=mat[0][2])
    params.add('c12', value=mat[1][2])
    params.add('c21', value=mat[2][1])

    fit_result = minimize(resid_rotmatrix, params, args=(mat, v1, v2))
    print("Fit result ", report_fit(fit_result))
    mat = params2rotmatrix(fit_result.params, mat)
    print(" Calculated Rotation Matrix. ")
    print(mat)
    return mat, v1, v2
#enddef


##
## Main Interface
##

def make_uscope_rotation():
    """
    Calculate and store the rotation maxtrix needed to convert
    positions from the GSECARS offline microscope (OSCAR)
    to the SampleStage in the microprobe station.

    This calculates the rotation matrix based on all position
    names that occur in the Position List for both instruments.

    Note:
        The result is saved as a json dictionary to the config table

    Warning:
        Please consult with Matt or Tony before running this!
    """

    d1 = read_uscope_xyz()
    d2 = read_sample_xyz()
    # calculate the rotation matrix
    mat_us2ss, v1, v2 = calc_rotmatrix(d1, d2)
    if mat_us2ss is None:
        return
    #endif
    uscope = _instdb.get_instrument(USCOPE_NAME)
    sample = _instdb.get_instrument(SSTAGE_NAME)

    uname = uscope.name.replace(' ', '_')
    sname = sample.name.replace(' ', '_')
    conf_us2ss = "CoordTrans:%s:%s" % (uname, sname)

    us2ss = dict(source=USCOPE_XYZ, dest=SSTAGE_XYZ,
                 rotmat=mat_us2ss.tolist())
    # print("rot = ", mat_us2ss)
    # print("Set Config ", conf_us2ss, json.dumps(us2ss))
    _scandb.set_config(conf_us2ss, json.dumps(us2ss))

    # calculate the rotation matrix going the other way
    mat_ss2us, v1, v2 = calc_rotmatrix(d2, d1)
    conf_ss2us = "CoordTrans:%s:%s" % (sname, uname)

    ss2us = dict(source=SSTAGE_XYZ, dest=USCOPE_XYZ,
                 rotmat=mat_ss2us.tolist())
    print("SAVE TO DB ", conf_ss2us, ss2us)
    _scandb.set_config(conf_ss2us, json.dumps(ss2us))
    # _scandb.commit()
#enddef

def uscope2sample(suffix='', xoffset=0, yoffset=0, zoffset=0):
    """
    transfer *all* named positions saved for the GSECARS offline
    microscope (OSCAR) to the SampleStage in the microprobe station.

    Applies the rotation matrix saved by the function `make_uscope_rotation()`

    Parameters:
        suffix (string): suffix to apply when transferring names,
            so as to avoid name clashes.
        xoffset (float, default=0):  offset in X, after coordinate transform
        yoffset (float, default=0):  offset in Y, after coordinate transform
        zoffset (float, default=0):  offset in Z, after coordinate transform

    Example:
        uscope2sample(suffix='_mount1')

    Note:
        Saved position names may be overwritten.

        Non-zero values for xoffset, yoffset, zoffset can accomodate for
        offsets for SampleStage, due to changes in mirror pitch.

    """
    uscope = _instdb.get_instrument(USCOPE_NAME)
    sample = _instdb.get_instrument(SSTAGE_NAME)
    uname = uscope.name.replace(' ', '_')
    sname = sample.name.replace(' ', '_')
    conf_name = "CoordTrans:%s:%s" % (uname, sname)
    try:
        us2ss_conf = _scandb.get_config(conf_name)
        rotmat = array(json.loads(us2ss_conf.notes))
        print(" ROT MAT ", rotmat)
    except:
        print("Error: could not get rotation matrix!")
        return
    #endtry
    upos   = read_uscope_xyz()
    labels = upos.keys()

    v = ones((4, len(labels)))
    for i, key in enumerate(labels):
        v[0, i] = upos[key][0]
        v[1, i] = upos[key][1]
        v[2, i] = upos[key][2]
    #endfor
    # Predict coordinates in SampleStage coordination system
    pred = dot(rotmat, v)
    # make SampleStage coordinates
    poslist = _instdb.get_positionlist(SSTAGE_NAME)
    pos0    = _instdb.get_position_vals(SSTAGE_NAME, poslist[0])
    pvs = pos0.keys()
    pvs.sort()
    spos = OrderedDict()
    for pvname in pvs:
        spos[pvname] = 0.000
    #endfor
    xpv, ypv, zpv = SSTAGE_XYZ
    for i, label in enumerate(labels):
        spos[xpv] = pred[0, i] + xoffset
        spos[ypv] = pred[1, i] + yoffset
        spos[zpv] = pred[2, i] + zoffset
        nlabel = '%s%s' % (label, suffix)
        _instdb.save_position(SSTAGE_NAME, nlabel, spos)
    #endfor
#enddef
