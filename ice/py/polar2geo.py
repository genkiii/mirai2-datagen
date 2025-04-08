'''Polar2Geo
'''

import pyproj
import shapely
import numpy as np


flatten = lambda x: [z for y in x for z in (flatten(y) if hasattr(y, '__iter__') else (y,))]

def shapely_transform(coords, src_crs, dest_crs):
    pyproj_transform = pyproj.Transformer.from_crs(src_crs, dest_crs, always_xy=True).transform
    return np.array(pyproj_transform(coords[:,0], coords[:,1])).transpose()


class Polar2Geo:

    def __init__(self):
        # print('Polar2Geo.__init__')
        # CRS
        self.crs = pyproj.CRS(proj='ob_tran', o_proj='longlat', o_lon_p=0, o_lat_p=0, lon_0=0)
        self.pyproj_transform = pyproj.Transformer.from_crs(self.crs, '4326', always_xy=True).transform
        # 分割用ジオメトリ
        longlat2xy = lambda long, lat: np.array([round(x, 10) for x in self.pyproj_transform(long, lat, direction='INVERSE')])
        xy0 = longlat2xy(0, 90)
        assert np.all(xy0 == (0, 0))
        xy1 = longlat2xy(-180, 80) * 9
        xy3 = longlat2xy(-90, 80) * 9
        xy2 = xy1 + xy3
        self.pole = shapely.Point(xy0)
        self.antimeridian = shapely.LineString((xy0, xy1))
        self.westbox = shapely.Polygon((xy0, xy1, xy2, xy3, xy0))

    def __call__(self, geom, src_crs=None):
        # print('Polar2Geo.__call__')
        if src_crs is not None:
            geom_ = shapely.transform(geom, lambda coords: shapely_transform(coords, src_crs, self.crs))
            geom2 = self.transform(geom_)
        else:
            geom2 = self.transform(geom)
        assert geom2.geom_type in ('Polygon', 'MultiPolygon')
        return geom2

    def transform(self, geom):
        # print('Polar2Geo.transform', geom.geom_type, len(geom.geoms) if geom.geom_type == 'MultiPolygon' else '')
        # 分割する場合
        if geom.intersects(self.antimeridian) and not shapely.touches(geom, self.antimeridian):
            p_180w_90w = self.transform(geom.intersection(self.westbox)) # 180W:90W
            p_90w_180e = self.transform(geom.difference(self.westbox)) # 90W:180E
            return shapely.union_all(flatten([p_180w_90w, p_90w_180e]))
        # 分割しない場合
        match geom.geom_type:
            case 'MultiPolygon':
                return shapely.MultiPolygon([self.transform(polygon) for polygon in geom.geoms])
            case 'Polygon':
                def shapely_transformation(coords, max_longitude):
                    x, y = np.array(self.pyproj_transform(coords[:,0], coords[:,1]))
                    x = np.where(x > max_longitude, x-360, x)
                    return np.array([x, y]).transpose()
                max_longitude = -90 if geom.difference(self.westbox).area == 0 else 180
                geom2 = shapely.transform(geom, lambda coords: shapely_transformation(coords, max_longitude=max_longitude))
                # 北極点を含む場合
                if shapely.touches(geom, self.pole):
                    exterior_coords = list(geom2.exterior.coords)
                    # 北極点を線分に変換する.
                    for n, c in enumerate(exterior_coords):
                        if c[1] == 90:
                            exterior_coords[n] = (exterior_coords[n+1][0], 90.0)
                            exterior_coords.insert(n, (exterior_coords[n-1][0], 90.0))
                            break
                    geom2 = shapely.Polygon(exterior_coords, geom2.interiors)
                assert geom2.geom_type == 'Polygon'
                return geom2 # Polygon

