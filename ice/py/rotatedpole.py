'''RotatedPole
'''

import cartopy
import pyproj

class RotatedPole:

    def __init__(self, grid_north_pole_latitude, grid_north_pole_longitude, north_pole_grid_longitude=0):
        self.grid_north_pole_latitude = grid_north_pole_latitude
        self.grid_north_pole_longitude = grid_north_pole_longitude
        self.north_pole_grid_longitude = north_pole_grid_longitude

    @property
    def as_cartopy(self):
        return cartopy.crs.RotatedPole(
            pole_latitude=self.grid_north_pole_latitude,
            pole_longitude=self.grid_north_pole_longitude,
            central_rotated_longitude=self.north_pole_grid_longitude
        )

    @property
    def as_pyproj(self):
        return pyproj.CRS(
            proj='ob_tran',
            o_proj='longlat',
            o_lon_p=self.north_pole_grid_longitude,
            o_lat_p=self.grid_north_pole_latitude,
            lon_0=self.grid_north_pole_longitude-180
        )
