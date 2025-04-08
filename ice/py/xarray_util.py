'''ファイルまたはデータから, xarray.Datasetを作成する.

・対応フォーマット：netcdf, grib, grib2
・engine='h5netcdf'ではmaskedarrayができない？ので, netcdf4で読み込み部分を自作する.
・gribはeccodesを使いたい. あとで作成.
・データからでも読めるようにする. engine指定だとできないことが多い.

'''

import xarray
import netCDF4
# import io
# from pathlib import Path

# def open(i):
#     match i:
#         case str():
#             return xarray.open_dataset(i, engine='h5netcdf')
#         case _:
#             assert readable(i)
#             i2 = io.BytesIO(i.read())
#             return xarray.open_dataset(i2, engine='h5netcdf')

def open(i, ftype='nc'):
    match ftype:
        case 'nc':
            nc = open_netcdf(i)
            ncvars = lambda nc: [nc[key] for key in nc.variables]
            return xarray.Dataset({
                var.name: (var.dimensions, var[:], var.__dict__)
                for var in ncvars(nc)
            })

def open_netcdf(i):
    match i:
        case str():
            return netCDF4.Dataset(i)
        case _:
            assert readable(i)
            return netCDF4.Dataset('<netCDF>', memory=i.read())

def readable(x):
    return hasattr(x, 'read') and callable(getattr(x, 'read'))
