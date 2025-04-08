import xarray
import datetime

r4 = lambda x: x.astype('float32')

class Xdata(xarray.Dataset):

    __slots__ = ()

    def __init__(self, i, engine):
        match engine:
            case 'netCDF4':
                vars, coords, attrs = self.open_netCDF4(i)
            case 'pygrib':
                vars, coords, attrs = self.open_pygrib(i)
            case _:
                raise Exception(f"Knknown engine '{engine}'")
        super().__init__(vars, coords, attrs)

    def open_netCDF4(self, i):
        import netCDF4
        nc = netCDF4.Dataset('<netCDF4>', memory=i.read()) if readable(i) else netCDF4.Dataset(i)
        ncvars = lambda nc: [nc[key] for key in nc.variables]
        vars = {
            var.name: (var.dimensions, var[:], var.__dict__)
            for var in ncvars(nc)
        }
        attrs = nc.__dict__
        return vars, None, attrs


    def open_pygrib(self, i):
        import pygrib
        gr = pygrib.open(i)
        vars = {}
        coords = None
        attrs = {}
        times = []
        for x in gr:
            if x.shortName == 'unknown':
                continue
            vars[x.shortName] = xarray.Variable(
                ('time', 'latitude', 'longitude'),
                [r4(x.values)],
                {
                    'name': x.name,
                    'units': x.units
                }
            )
            lats2, lons2 = x.latlons()
            lats, lons = r4(lats2[:,0]), r4(lons2[0])
            if coords is None:
                coords = xarray.Coordinates({'latitude': lats, 'longitude': lons}, {})
            else:
                assert all(coords.variables['latitude'] == lats) and all(coords.variables['longitude'] == lons)
            attrs['GRIB_edition'] = x.GRIBEditionNumber
            if 'reftime' not in vars:
                reftime = datetime.datetime.strptime(str(x.dataDate) + str(x.dataTime), '%Y%m%d%H%M%S')
                vars['reftime'] = xarray.Variable('reftime', [reftime])
            time = datetime.datetime.strptime(str(x.validityDate) + str(x.validityTime), '%Y%m%d%H%M%S')
            if len(times) == 0:
                vars['time'] = xarray.Variable('time', [time])
            else:
                assert times[0] == time
        return vars, coords, attrs

def readable(x):
    return hasattr(x, 'read') and callable(getattr(x, 'read'))
