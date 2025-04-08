import contourpy
import shapely

class ContourpyShapely:

    def __init__(self, x=None, y=None, z=None):
        self.generator = contourpy.contour_generator(x, y, z)

    def geometry(self, vmin, vmax):
        points2, offsets2 = self.generator.filled(vmin, vmax)
        num_polygons = len(points2)
        if num_polygons > 1:
            return shapely.MultiPolygon([
                self.polygon(points, offsets)
                for (points, offsets) in zip(points2, offsets2)
            ])
        else:
            raise # 以下, 未テストのため（ケース発生時に検証を経て削除）
            return self.polygon(points2[0], offsets2[0])

    def polygon(self, points, offsets):
        coords = []
        for j in range(len(offsets)-1):
            i1, i2 = offsets[j], offsets[j+1]
            assert all(points[i1] == points[i2-1])
            coords.append(points[i1:i2])
        return shapely.Polygon(coords[0], coords[1:])
