import numpy as np
import os
from .io import Raster, Vector, geometry_window, overlap
from .io import geometry_bounds


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


def zonal_stats(vector, 
                raster,
                field, 
                affine=None,
                crs=None,
                nodata=None,
                stat=None,
                zone_func=None,
                all_touched=False
                ):
    """
    Parameters
    ----------
    vector: path to an vector source or io.Vector object or ndarray
    raster: path to an raster source or io.Raster object
    field: str, optional
        field in the vector
        defaults to None
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
    all_touched: bool, optional
        Whether to include every raster cell touched by a geometry, or only
        those having a center point within the polygon.
        defaults to `False`
    """
    if stat and zone_func:
        raise ValueError("Specify either stat or zone_func")

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

    values = []
    for geometry in vector['geometry']:
        clip_raster = raster.read_from_geometry([geometry], all_touched=all_touched)
        array = clip_raster.array
        geometry_mask = ~array.mask
        if not np.any(geometry_mask):
            left, bottom, right, top = geometry_bounds(geometry)
            center_x, center_y = (left + right) / 2, (bottom + top) / 2
            center_row, center_col = raster.index(center_x, center_y)
            value = raster.array[center_row, center_col]
            values.append(int(value))
            continue

        if stat != None:
            value = stat_func(array, stat)
            values.append(int(value))
            continue

        # execute zone_func on masked zone ndarray
        if zone_func is not None:
            if not callable(zone_func):
                raise TypeError(('zone_func must be a callable '
                                 'which accepts function a '
                                 'single `zone_array` arg.'))
            value = zone_func(array)
            values.append(int(value))
            continue

    if field != None:
        vector.create_field(name=field, type='float', values=values)
        return vector


