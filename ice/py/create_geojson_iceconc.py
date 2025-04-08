#!/usr/bin/env python3
'''Create GeoJSON for ice-concentration.
'''

import xarray_util
from am import AmData
from contourpyshapely import ContourpyShapely
from rotatedpole import RotatedPole
from polar2geo import Polar2Geo
from shapely2geojson import Shapely2GeoJSON

import datetime
import json
import numpy as np


def main(inputpath_nc, varname, levels, outputpath_gj=None, l=-1):

    # Open dataset
    d = read(inputpath_nc)
    crs_data = RotatedPole(d.rotated_pole.grid_north_pole_latitude, d.rotated_pole.grid_north_pole_longitude)
    var = d[varname][l]

    # Create polygons
    contours = []
    cs = ContourpyShapely(d.rlon, d.rlat, var)
    # for n in range(10):
    #     value = (n/10, (n+1)/10)
    for i in range(len(levels) - 1):
        value = levels[i:i+2]
        contours.append({
            'value': value,
            'geometry': cs.geometry(*value)
        })

    # Convert to longlat
    p2g = Polar2Geo()
    for c in contours:
        c['geometry_longlat'] = p2g(c['geometry'], crs_data.as_pyproj)

    # Output GeoJSON
    s2gj = Shapely2GeoJSON()
    for c in contours:
        s2gj.append(c['geometry_longlat'], props={'value': c['value'][0]}, round=3)
    s2gj['metadata'] = metadata(d, varname, l)

    # Output GeoJSON
    if outputpath_gj:
        ymdh = lambda dt: dt.strftime('%Y%m%d%H')
        outputpath_gj_fmt = outputpath_gj.format(
            reftime=ymdh(seconds2datetime(d.reftime)),
            fcsttime=ymdh(seconds2datetime(d.time[l]))
        )
        with open(outputpath_gj_fmt, 'w') as f:
            print(json.dumps(s2gj[:], separators=(',', ':')), file=f)

    return s2gj[:]

def read(ncfilepath):
    def read_ahead(f, n):
        b = f.read(n)
        f.seek(-n, 1)
        return b
    with open(ncfilepath, 'rb') as f:
        # if f.read(2) == b'WN':
        #     f.seek(0)
        #     AmData(f, carrier=False)
        # else:
        #     f.seek(0)
        if read_ahead(f, 2) == b'WN':
            AmData(f, carrier=False)
        return xarray_util.open(f)

def metadata(d, varname, n=0):
    def datetime_str(dt):
        assert dt.tzname() == 'UTC'
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    return {
        'institution': 'Weathernews Inc.',
        'source': f'WNI_MRF_ISEE / {varname}',
        'creation_time': datetime_str(datetime.datetime.now(datetime.UTC)),
        'reference_time': datetime_str(seconds2datetime(d.reftime)),
        'forecast_time': datetime_str(seconds2datetime(d.time[n]))
    }

def seconds2datetime(s):
    return datetime.datetime(1970, 1, 1, tzinfo=datetime.UTC) + datetime.timedelta(seconds=float(s))


if __name__ == '__main__':

    import sys

    inputpath_nc = sys.argv[1]
    varname = sys.argv[2] # 'conc' | 'thic'

    var_id = {
        'conc': 'ice-concentration',
        'thic': 'ice-thickness'
    }[varname]
    levels = {
        'ice-concentration': np.append(np.arange(10) / 10, np.inf),
        'ice-thickness': [0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.7, 0.9, 1.2, 1.5, 1.8, 2.1, 2.5, 3, 3.5, 4, 4.5, 5, float('inf')]
    }[var_id]
    outputpath_gj = f'{var_id}_{{reftime}}_{{fcsttime}}.geojson'

    main(inputpath_nc, varname, levels, outputpath_gj)
