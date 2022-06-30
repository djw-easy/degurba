import matplotlib.pyplot as plt
from degurba.degurba import DEGURBA

border_path = r"D:\Files\SDGs\SDG11.7.1\Codes\Data\Border\BJ_Street\BJStreet.shp"
pn_path = r"D:\Files\SDGs\SDG11.7.1\Codes\Data\pd\bj_ppp_2020_1000m_UNadj.tif"

degurba = DEGURBA(pn_path)
grid_cells_l1 = degurba.classify_grid_cells_l1()

plt.imshow(grid_cells_l1.array);

local_units = degurba.classify_local_units_l1(border_path, grid_cells_l1=grid_cells_l1, field='l1')

local_units.close()

