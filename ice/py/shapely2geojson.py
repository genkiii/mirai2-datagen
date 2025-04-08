'''shapely2geojson'''

import shapely
import json

class Shapely2GeoJSON:

    def __init__(self):
        self.data = {}
        self.features = []

    def __setitem__(self, key, value):
        self.data[key] = value

    def append(self, shape, props=None, round=None):
        feature = {
            'type': 'Feature',
            'geometry': self._shape2geojsongeometry(shape, round=round)
        }
        if props:
            feature['properties'] = props
        self.features.append(feature)

    def _shape2geojsongeometry(self, shape, round=None):
        geom = json.loads(shapely.to_geojson(shape))
        if type(round) is int:
            geom['coordinates'] = self._round_coords(geom['coordinates'], round)
        return geom

    def _round_coords(self, c, digits=0):
        if hasattr(c, '__iter__'):
            return [self._round_coords(c2, digits) for c2 in c]
        else:
            return round(c, digits)
    #     return [round_coords[c2] for c2 in c] if hasattr(c, '__iter__') else round(c, digits)
    # round_coords = lambda c, digits=0: \
    #     [round_coords(c2) for c2 in c] if hasattr(c, '__iter__') else round(c, digits)

    def __getitem__(self, x):
        if len(self.features) == 1:
            self.data = self.features[0] | self.data
        else:
            self.data = {
                'type': 'FeatureCollection',
                'features': self.features
            } | self.data
        return self.data
