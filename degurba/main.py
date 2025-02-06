import numpy as np
from scipy import ndimage
from .io import Raster
from .utils import zonal_stats


class DEGURBA:

    grid_cells_l1_cla = {
        'urban_centres': 1,
        'urban_clusters': 2,
        'rural_grid_cells': 3
    }
    local_units_l1_cla = {
        'cities': 1,
        'towns_semi_dense_areas': 2,
        'rural_areas': 3
    }
    grid_cells_l2_cla = {
        'urban_centre': 11,
        'dense_urban_cluster': 21,
        'semi_dense_urban_cluster': 22,
        'suburban_peri_urban_grid_cells': 23,
        'rural_cluster': 31,
        'low_density_rural_grid_cells': 32,
        'very_low_density_rural_grid_cells': 33
    }
    local_units_l2_cal = {
        'city': 11,
        'dense_town': 21,
        'semi_dense_town': 22,
        'suburban_peri_urban_area': 23,
        'village': 31,
        'dispersed_rural_area': 32,
        'mostly_uninhabited_area': 33
    }

    def __init__(self, 
                 pn=None,
                 affine=None,
                 crs=None,
                 nodata=None,
                 band=1) -> None:
        if not isinstance(pn, type(None)):
            self.pn = Raster(pn, affine=affine, crs=crs, nodata=nodata, band=band)

    def _get_urban_centres(self, pn):
        '''Identify the urban centres (high-density clusters), it is done in four steps.
            Args:
                pn (numpy array): population counts array.
        '''
        # First step, identify cells with at least 1500 inhabitants
        urban_centres_mask = pn >= 1500
        if isinstance(urban_centres_mask, np.ma.masked_array):
            urban_centres_mask = urban_centres_mask.data
        urban_centres_mask = urban_centres_mask.astype(np.byte)
        # Second, identify groups of contiguous cells using the "four-point contiguity" method
        s = np.array(
            [
                [0, 1, 0],
                [1, 1, 1],
                [0, 1, 0]
            ]
        )
        label, num_features = ndimage.label(urban_centres_mask, structure=s)
        # Third step, remove group whose total number of inhabitants less than 50000
        for i in range(1, num_features+1):
            mask = label == i
            if np.sum(pn[mask]) < 50000:
                urban_centres_mask[mask] = 0
        # Fouth step, fill gaps and smooth borders by using iterative ‘majority rule’
        w = np.array(
            [
                [1, 1, 1],
                [1, 0, 1],
                [1, 1, 1]
            ]
        )
        for i in range(1, num_features+1):
            mask = label == i
            mask = mask.astype(np.byte)
            while True:
                mask = ndimage.convolve(
                    mask, weights=w, mode='constant', cval=0)
                mask = np.logical_and(mask >= 5, urban_centres_mask == 0)
                if 0 == np.count_nonzero(mask):
                    break
                urban_centres_mask[mask] = 1
        return urban_centres_mask.astype(np.bool_)

    def _get_urban_clusters(self, pn, urban_centres_mask):
        """Identify the urban clusters (moderate-density clusters), it is done in four steps.
            Args:
                pn (numpy array): population counts array.
                urban_centres (numpy array): urban centres. 
        """
        # First step, identify cells with at least 300 inhabitants
        urban_clusters_mask = pn >= 300
        if isinstance(urban_clusters_mask, np.ma.masked_array):
            urban_clusters_mask = urban_clusters_mask.data
        urban_clusters_mask = urban_clusters_mask.astype(np.byte)
        # Second, identify groups of contiguous cells using the "eight-point contiguity" method
        s = np.array(
            [
                [1, 1, 1],
                [1, 1, 1],
                [1, 1, 1]
            ]
        )
        label, num_features = ndimage.label(urban_clusters_mask, structure=s)
        # Third step, remove group whose total number of inhabitants less than 5000
        for i in range(1, num_features+1):
            mask = label == i
            if np.sum(pn[mask]) < 5000:
                urban_clusters_mask[mask] = 0
        # Fouth step, overlay the urban centres on urban clusters to identify final urban clusters
        urban_clusters_mask = np.logical_and(urban_clusters_mask,
                                             urban_centres_mask == 0)
        urban_clusters_mask = urban_clusters_mask.astype(np.byte)
        return urban_clusters_mask.astype(np.bool_)

    def _get_rural_grid_cells(self, pn, urban_centres_mask, urban_clusters_mask):
        """Identify the rural grid cells  (mostly low density cells) that are not identified as urban centres or as urban clusters.
            Args:
                pn (numpy array): population counts array.
                urban_centres_mask (numpy array): urban centres.
                urban_clusters_mask (numpy array): urban clusters. 
        """
        rural_grid_cells_mask = pn >= 0
        if isinstance(rural_grid_cells_mask, np.ma.masked_array):
            rural_grid_cells_mask = rural_grid_cells_mask.data
        rural_grid_cells_mask = np.logical_and(rural_grid_cells_mask,
                                               urban_centres_mask == False)
        rural_grid_cells_mask = np.logical_and(rural_grid_cells_mask,
                                               urban_clusters_mask == False)
        rural_grid_cells_mask = rural_grid_cells_mask.astype(np.byte)
        return rural_grid_cells_mask.astype(np.bool_)

    def classify_grid_cells_l1(self):
        pn_array = self.pn.array
        urban_centres = self._get_urban_centres(pn_array)
        urban_clusters = self._get_urban_clusters(
            pn_array, urban_centres)
        rural_grid_cells = self._get_rural_grid_cells(
            pn_array, urban_centres, urban_clusters)
        grid_cells_clas = [urban_centres,
                           urban_clusters, rural_grid_cells]
        grid_cells_l1 = np.zeros(
            shape=urban_centres.shape, dtype=np.int8)
        for grid_cells_cla, index in zip(grid_cells_clas,
                                         self.grid_cells_l1_cla.values()):
            grid_cells_l1[grid_cells_cla] = index
        grid_cells_l1 = Raster(
            grid_cells_l1, affine=self.pn.affine, crs=self.pn.crs, nodata=0)

        return grid_cells_l1

    def classify_local_units_l1(self, local_units, field=None, 
                                grid_cells_l1=None, all_touched=False):
        """
        Parameters:
        -----------
        local_units: path to an vector source or io.Vector object or ndarray
        grid_cells_l1: the result of classify_grid_cells_l1
        """
        if grid_cells_l1 == None:
            grid_cells_l1 = self.classify_grid_cells_l1()

        def classify(grid_cells):
            total_count = grid_cells.count()
            if not total_count:
                return 0
            urban_centres = self.grid_cells_l1_cla['urban_centres']
            urban_centres_cells_r = np.count_nonzero(
                grid_cells == urban_centres) / total_count

            if urban_centres_cells_r >= 0.5:
                return self.local_units_l1_cla['cities']

            rural_grid_cells = self.grid_cells_l1_cla['rural_grid_cells']
            rural_grid_cells_r = np.count_nonzero(
                grid_cells == rural_grid_cells) / total_count

            if urban_centres_cells_r < 0.5 and rural_grid_cells_r < 0.5:
                return self.local_units_l1_cla['towns_semi_dense_areas']

            if rural_grid_cells_r >= 0.5:
                return self.local_units_l1_cla['rural_areas']

        local_units = zonal_stats(
            local_units, grid_cells_l1, field=field, 
            zone_func=classify, all_touched=all_touched)
        return local_units
