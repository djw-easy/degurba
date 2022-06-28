from turtle import left, right
from typing_extensions import Self
import rasterio as rio
from osgeo import gdal, ogr
from rasterio import features
from rasterio.transform import guard_transform
import numpy as np
import math
import os
import json
from typing import Union, TypeVar
from affine import Affine


def clip_raster(in_raster,
                cutline_shp,
                out_raster,
                srcSRS=None, dstSRS=None,
                srcNodata=None, dstNodata=None,
                **kwargs):
    """Clip raster with shapefile. 
        Args:
            in_raster: 
            cutline_shp: 
            out_raster: 
            srcSRS, dstSRS: 
            srcNodata, dstNodata: 
    """
    ds = gdal.Open(in_raster)
    band = ds.GetRasterBand(1)
    if srcSRS == None:
        srcSRS = ds.GetProjection()
    if dstSRS == None:
        dstSRS = srcSRS
    if srcNodata == None:
        srcNodata = band.GetNoDataValue()
    if dstNodata == None:
        dstNodata = srcNodata
    clip_options = gdal.WarpOptions(format='GTiff',
                                    cutlineDSName=cutline_shp,
                                    cropToCutline=True,
                                    srcSRS=srcSRS, dstSRS=dstSRS,
                                    srcNodata=srcNodata, dstNodata=dstNodata,
                                    **kwargs)
    ds_clip = gdal.Warp(out_raster, ds, options=clip_options)
    ds = band = ds_clip = None


def rowcol(x, y, affine, op=math.floor):
    """ Get row/col for a x/y
    """
    r = int(op((y - affine.f) / affine.e))
    c = int(op((x - affine.c) / affine.a))
    return r, c


def bounds_window(bounds, affine):
    """Create a full cover rasterio-style window
    """
    w, s, e, n = bounds
    row_start, col_start = rowcol(w, n, affine)
    row_stop, col_stop = rowcol(e, s, affine, op=math.ceil)
    return (row_start, row_stop), (col_start, col_stop)


def window_bounds(window, affine):
    (row_start, row_stop), (col_start, col_stop) = window
    w, s = affine * (col_start, row_stop)
    e, n = affine * (col_stop, row_start)
    return w, s, e, n


def beyond_extent(window, shape):
    """Checks if window references pixels beyond the raster extent"""
    (wr_start, wr_stop), (wc_start, wc_stop) = window
    return wr_start < 0 or wc_start < 0 or wr_stop > shape[0] or wc_stop > shape[1]


def geometry_bounds(geometry):
    """Return a (left, bottom, right, top) bounding box.
    Parameters
    ----------
    geometry: GeoJSON-like feature (implements __geo_interface__),
              feature collection, or geometry.

    Returns
    -------
    tuple
        Bounding box: (left, bottom, right, top)
    """
    geom_types = {'Polygon', 'MultiPolygon'}

    geom = getattr(geometry, '__geo_interface__', None) or geometry

    try:
        geom_type = geom["type"]
        if geom_type not in geom_types.union({'GeometryCollection'}):
            return False

    except (KeyError, TypeError):
        return False

    if 'bbox' in geom:
        return tuple(geom['bbox'])

    geom = geom.get('geometry') or geom

    # geometry must be a geometry, GeometryCollection, or FeatureCollection
    if not ('coordinates' in geom or 'geometries' in geom or 'features' in geom):
        raise ValueError(
            "geometry must be a GeoJSON-like geometry, GeometryCollection, "
            "or FeatureCollection"
        )
    
    if geom_type == 'Polygon':
        coords = np.vstack(geom['coordinates'])
        left, right = np.min(coords[:, 0]), np.max(coords[:, 0])
        bottom, top = np.min(coords[:, 1]), np.max(coords[:, 1])
        return (left, bottom, right, top)

    if geom_type == 'MultiPolygon':
        # Muti polygons must have at least one Polygon
        coords = []
        for c in geom['coordinates']:
            coords.append(np.vstack(c))
        coords = np.vstack(coords)
        left, right = np.min(coords[:, 0]), np.max(coords[:, 0])
        bottom, top = np.min(coords[:, 1]), np.max(coords[:, 1])
        return (left, bottom, right, top)


def geometry_window(geometry, affine):
    bounds = geometry_bounds(geometry)
    window = bounds_window(bounds, affine)
    return window


def overlap(shape, win):
    height, weight = shape
    (r_start, r_stop), (c_start, c_stop) = win

    # Calculate overlap
    or_start = max(min(r_start, height), 0)
    or_stop = max(min(r_stop, height), 0)
    oc_start = max(min(c_start, weight), 0)
    oc_stop = max(min(c_stop, weight), 0)

    return (or_start, or_stop), (oc_start, oc_stop)


def boundless_array(arr, window):
    """Return a numpy masked array by the window of arr
    Parameters
    ----------
    arr: numpy array, 2D or 3D
        if arr is a 3D numpy array, it's shape must be (channels, height, weight)
    """

    dim3 = False
    if len(arr.shape) == 3:
        dim3 = True
        channels, height, weight = arr.shape
    elif len(arr.shape) != 2:
        raise ValueError("Must be a 2D or 3D array")
    else:
        height, weight = arr.shape

    # unpack for readability
    (wr_start, wr_stop), (wc_start, wc_stop) = window

    # Calculate overlap
    (olr_start, olr_stop), (olc_start, olc_stop) = overlap((height, weight), window)

    # Calc dimensions
    overlap_shape = (olr_stop - olr_start, olc_stop - olc_start)
    if dim3:
        window_shape = (channels, wr_stop - wr_start, wc_stop - wc_start)
    else:
        window_shape = (wr_stop - wr_start, wc_stop - wc_start)

    # create an array of nodata values
    out = np.ma.MaskedArray(
                np.zeros(shape=window_shape, dtype=arr.dtype), 
                mask=True)

    # Fill with data where overlapping
    nr_start = olr_start - wr_start
    nr_stop = nr_start + overlap_shape[0]
    nc_start = olc_start - wc_start
    nc_stop = nc_start + overlap_shape[1]
    if dim3:
        out[:, nr_start:nr_stop, nc_start:nc_stop] = \
            arr[:, olr_start:olr_stop, olc_start:olc_stop]
    else:
        out[nr_start:nr_stop, nc_start:nc_stop] = \
            arr[olr_start:olr_stop, olc_start:olc_stop]

    return out


class Vector(object):

    def __init__(self, path,
                 layer=0) -> None:
        if not os.path.exists(path):
            raise ValueError("The path {} is not exist.".format(path))
        self.ds = ogr.Open(path, update=1)
        self.layer = self.ds.GetLayer(layer)
        self.layer_def = self.layer.GetLayerDefn()
        self.columns = []
        for i in range(self.layer_def.GetFieldCount()):
            field_def = self.layer_def.GetFieldDefn(i)
            self.columns.append(field_def.GetName())

    def __getitem__(self, column):
        """
        """
        if (column != 'geometry' and
                column not in self.columns):
            raise KeyError("The column {} is not exist. ".format(column))

        values = []
        feature_count = self.layer.GetFeatureCount()
        if not feature_count:
            return values

        for i in range(feature_count):
            feature = self.layer.GetFeature(i)
            if column == 'geometry':
                geom = feature.GetGeometryRef()
                geom = json.loads(geom.ExportToJson())
                value = geom
                # value = shape(geom.ExportToJson())
            else:
                value = feature.GetField(self.columns.index(column))
            values.append(value)

        return values

    @property
    def geometry(self):
        return self.__getitem__('geometry')

    def _type_convert(self, type):
        type_convert = {'int': ogr.OFTInteger64,
                        'float': ogr.OFTReal,
                        'string': ogr.OFTString}
        return type_convert[type]

    def create_field(self, name, type,
                     width=50,
                     values=None):
        if values != None:
            length = len(values)
            feature_count = self.layer.GetFeatureCount()
            if length != feature_count:
                raise ValueError(
                    'The length of input value must be {}. '.format(feature_count))

        type = self._type_convert(type)
        field_def = ogr.FieldDefn(name, type)
        field_def.SetWidth(width)
        self.layer.CreateField(field_def)
        # self.layer_def.AddFieldDefn(field_def)

        for i in range(feature_count):
            feature = self.layer.GetFeature(i)
            if values == None:
                feature.SetFieldNull(name)
            value = values[i]
            feature.SetField(name, value)
            self.layer.SetFeature(feature)

        self.columns.append(name)

    def close(self):
        self.ds.Destroy()

    def __del__(self):
        self.close()


class Raster(object):

    def __init__(self, raster,
                 affine=None,
                 crs=None,
                 nodata=None,
                 band=1):
        self.crs = crs

        if isinstance(raster, np.ndarray):
            if affine is None:
                raise ValueError("Specify affine transform for numpy arrays")
            if not len(raster.shape) == 2:
                raise ValueError("The inpute ndarray must be 2-d array")
            # create a mask array by nodata value
            isnodata = (raster == nodata) | np.isnan(raster)
            self.array = np.ma.masked_array(raster, isnodata)
            self.affine = affine
            self.shape = raster.shape
        else:
            src = rio.open(raster, 'r')
            self.affine = guard_transform(src.transform)
            self.shape = (src.height, src.width)
            self.crs = src.crs
            array = src.read(band)
            nodataval = src.nodata
            # create a mask array by nodata value
            isnodata = (array == nodata) | (array == nodataval)
            # add nan mask (if necessary)
            isnodata = isnodata | np.isnan(array)
            # convert numpy array to numpy masked array
            self.array = np.ma.masked_array(array, isnodata)
            src = None

    def save(self, path, nodata=None) -> None:
        if nodata is None:
            if np.issubdtype(self.array.dtype, np.floating):
                nodata = np.nan
            else:
                nodata = np.iinfo(self.array.dtype).max
        array = self.array.filled(nodata)
        with rio.open(path,
                      'w',
                      driver='GTiff',
                      nodata=nodata,
                      height=array.shape[0],
                      width=array.shape[1],
                      count=1,
                      dtype=array.dtype,
                      crs=self.crs,
                      transform=self.affine,
                      compress='lzw') as dst:
            dst.write(array, 1)

    def read(self, 
            bounds=None, 
            window=None, 
            boundless=True, 
            only_array=False):
        """ Performs a read against the underlying array source

        Parameters
        ----------
        bounds: bounding box
            in w, s, e, n order, iterable, optional
        window: rasterio-style window, optional
            bounds OR window are required,
            specifying both or neither will raise exception
        boundless: boolean
            allow window/bounds that extend beyond the dataset’s extent, default: True
            partially or completely filled arrays will be returned as appropriate.
        only_array: boolean
            return a masked numpy array, default: False
            bounds OR window are required, specifying both or neither will raise exception
        Returns
        -------
        Raster object with update affine and array info
        """
        # Calculate the window
        if bounds and window:
            raise ValueError("Specify either bounds or window")

        if bounds:
            win = bounds_window(bounds, self.affine)
        elif window:
            win = window
        else:
            raise ValueError("Specify either bounds or window")
        
        if not boundless and beyond_extent(win, self.shape):
            raise ValueError("Window/bounds is outside dataset extent and boundless reads are disabled")

        out = boundless_array(self.array, window=win)

        if only_array:
            return out

        c, _, _, f = window_bounds(win, self.affine)  # c ~ west, f ~ north
        a, b, _, d, e, _, _, _, _ = tuple(self.affine)
        new_affine = Affine(a, b, c, d, e, f)

        return Raster(out, new_affine, self.crs)

    def read_from_geometry(self, geometry, boundless=True, all_touched=False) -> np.ma.MaskedArray:
        """
        Parameters
        ----------
        geometries : iterable over geometries (GeoJSON-like objects)
        all_touched : boolean, optional
            If True, all pixels touched by geometries will be burned in.  If
            false, only pixels whose center is within the polygon or that
            are selected by Bresenham's line algorithm will be burned in.
        Returns
        -------
        ndarray: boolean
        """

        bounds = geometry_bounds(geometry)
        window = bounds_window(bounds, self.affine)

        clip_raster = self.read(window=window, boundless=boundless)
        geometries = [geometry]
        geometry_mask = features.geometry_mask(
            geometries=geometries,
            out_shape=clip_raster.shape,
            transform=clip_raster.affine,
            all_touched=all_touched, 
            invert=True)
        array = np.ma.masked_array(clip_raster.array, ~geometry_mask)

        return array
