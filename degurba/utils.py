import numpy as np
import os
from .io import Raster, Vector, geometry_window, overlap


def stat_func(array, stat):
    """
    Parameters
    ----------
    array: numpy masked array
    """
    stats = {'min': np.ma.min, 'max': np.ma.max,
             'mean': np.ma.mean, 'sum': np.ma.sum,
             'count': np.ma.count, 'std': np.ma.std,
             'median': np.ma.median,
             'range': lambda x: np.ma.max(x) - np.ma.min(x)}
    return stats[stat](array)


def zonal_stats(vector, raster,
                affine=None,
                crs=None,
                nodata=None,
                stat=None,
                zone_func=None,
                field=None,
                out_array=False,
                all_touched=False
                ):
    """
    Parameters
    ----------
    vector: path to an vector source or io.Vector object or ndarray
    raster: path to an raster source or io.Raster object
    affine: Affine instance
        required only for ndarrays, otherwise it is read from src
    crs: str, dict, or CRS; optional
        Coordinate reference systems defines how a dataset’s pixels map to locations on, 
        for example, a globe or the Earth.
    nodata: int or float, optional
    stat: str 
        Which statistics to calculate for each zone. 
        The optional parameters are min, max, mean, sum, count, std, median, range
    zone_func: callable
        function to apply to zone ndarray prior to computing stats
    field: str, optional
        field in the vector
        defaults to None
    out_array: bool, optional
        If True, return an array of same shape and data type as `source` in which to store results.
    all_touched: bool, optional
        Whether to include every raster cell touched by a geometry, or only
        those having a center point within the polygon.
        defaults to `False`
    """
    if stat and zone_func:
        raise ValueError("Specify either stat or zone_func")

    if field and out_array:
        raise ValueError("Specify either field or out_array")

    if isinstance(vector, str):
        if not os.path.exists(vector):
            raise ValueError("The vector {} is not exist.".format(vector))
        else:
            vector = Vector(vector)

    if isinstance(raster, str):
        if not os.path.exists(raster):
            raise ValueError("The vector {} is not exist.".format(raster))
        else:
            raster = Raster(raster, affine=affine, crs=crs, nodata=nodata)

    if out_array:
        out_array = np.zeros(raster.shape, dtype=raster.array.dtype)

    values = []
    for i, geometry in enumerate(vector['geometry'], 1):
        clip_raster = raster.read_from_geometry([geometry], all_touched=all_touched)
        array = clip_raster.array
        geometry_mask = ~array.mask

        if stat != None:
            value = stat_func(array, stat)

        # execute zone_func on masked zone ndarray
        if zone_func is not None:
            if not callable(zone_func):
                raise TypeError(('zone_func must be a callable '
                                 'which accepts function a '
                                 'single `zone_array` arg.'))
            value = zone_func(array)

        if isinstance(out_array, np.ndarray):
            win = geometry_window(geometry, raster.affine)
            (or_start, or_stop), (oc_start, oc_stop) = overlap(out_array.shape, win)
            (r_start, r_stop), (c_start, c_stop) = win
            if r_start<0:
                g_r_start = -r_start
                g_r_stop = or_stop-or_start+g_r_start
            else:
                g_r_start = 0
                g_r_stop = or_stop-or_start
            if c_start<0:
                g_c_start = -c_start
                g_c_stop = oc_stop-oc_start+g_c_start
            else:
                g_c_start = 0
                g_c_stop = oc_stop-oc_start
            geometry_mask = geometry_mask[g_r_start:g_r_stop, g_c_start:g_c_stop]
            out_array[or_start:or_stop, oc_start:oc_stop][geometry_mask] = value
        else:
            values.append(value)

    if field != None:
        vector.create_field(name=field, type='float', values=values)
        return vector

    if isinstance(out_array, np.ndarray):
        return out_array

