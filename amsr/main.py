#!/usr/bin/env python3
'''Create GeoJSON for AMSR2 composite.
'''

from amsr2composite import AMSR2Composite
from contourpyshapely import ContourpyShapely
from shapely2geojson import Shapely2GeoJSON

import sys
import numpy as np
import shapely
import datetime
import json
from pathlib import Path

def main(amsr2filename, amsr2date):

    a = AMSR2Composite(amsr2filename)

    lon_ext, lat_ext, conc_ext = convert_data(a)

    contours = make_contours(lon_ext, lat_ext, conc_ext)

    gj = make_geojson(contours)

    with open(f'out/amsr2-{amsr2date.strftime('%Y%m%d')}.geojson', 'w') as f:
        print(json.dumps(gj[:], separators=(',', ':')), file=f)
    
def convert_data(a: AMSR2Composite):
    '''データ変換する. 経度方向に1グリッドずつ, 緯度方向に1グリッド拡大する.
    '''
    # 経度
    lon_ext = np.append(
        np.insert(a.lons, 0, a.lons[-1] - 360),
        a.lons[0] + 360
    )
    # 緯度
    lat_ext = np.append(a.lats, 90.025)
    # 密接度
    conc = np.where(a.values[0] > 0, a.values[0].astype(np.float32) / 1e4, 0.0)
    conc[-50:,:] = np.where(a.values[0,-50:,:] < 0, 1, conc[-50:,:])
    conc_ext = np.concatenate((conc[:,-1:], conc, conc[:,:1]), axis=1)
    conc_ext = np.concatenate((conc_ext, conc_ext[-1:,:]))
    #
    return lon_ext, lat_ext, conc_ext

def make_contours(lon_ext, lat_ext, conc_ext):
    '''
    '''
    contours = []
    cs = ContourpyShapely(lon_ext, lat_ext, conc_ext)
    levels = np.append(np.arange(10) / 10, np.inf)
    for i in range(len(levels) - 1):
        value = levels[i:i+2]
        geom = shapely.intersection(
            cs.geometry(*value),
            shapely.box(-180, 0, 180, 90)
        )
        if geom.geom_type == 'GeometryCollection':
            print(set([g.geom_type for g in geom.geoms]), file=sys.stderr)
            geom = shapely.MultiPolygon([g for g in geom.geoms if isinstance(g, shapely.Polygon)])
        contours.append({
            'value': value,
            'geometry': geom
        })
    return contours

def make_geojson(contours):
    '''
    '''
    s2gj = Shapely2GeoJSON()
    for c in contours:
        s2gj.append(c['geometry'], props={'value': c['value'][0]}, round=3)
    def datetime_str(dt):
        assert dt.tzname() == 'UTC'
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    s2gj['metadata'] = {
        'institution': 'Weathernews Inc.',
        'source': f'411024814 WNI_ANLSIS_AMSR2_ICECNC_DAILY_filtered',
        'creation_time': datetime_str(datetime.datetime(2025, 3, 10, 13, 44, 12, tzinfo=datetime.UTC)),
        'acquisition_time': datetime_str(datetime.datetime(2025, 3, 1, tzinfo=datetime.UTC)),
    }
    return s2gj

if __name__ == '__main__':

    amsr2filename = sys.argv[1]
    amsr2date = datetime.datetime.strptime(Path(amsr2filename).name[:8], '%Y%m%d')
    main(amsr2filename, amsr2date)
