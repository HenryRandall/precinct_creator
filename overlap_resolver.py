from shapely.geometry import GeometryCollection, MultiPoint, Polygon, LineString, MultiPolygon
from shapely.ops import split

def overlap_resolver(shape_1, shape_2):
  """takes in 2 shapely shapes and evenly splits them based on the points of intersection"""

  intersections = shape_1.intersection(shape_2)
  shape_1_new = shape_1.difference(shape_2)
  shape_2_new = shape_2.difference(shape_1)

  # https://gis.stackexchange.com/questions/374042/find-the-intersecting-points-of-2-polygons-in-python
  intersection_points = shape_1.boundary.intersection(shape_2.boundary)

  if isinstance(intersections, MultiPolygon) or isinstance(intersections, GeometryCollection):
    for intersection in list(intersections.geoms):
      if isinstance(intersection, LineString):
        continue
      points = intersection.boundary.intersection(intersection_points)

      if isinstance(points, MultiPoint):
        line = LineString(points.geoms)
        split_intersection = split(intersection, line)
      else:
        split_intersection = intersection

      if isinstance(split_intersection, MultiPolygon):
        for geom in split_intersection.geoms:
          if geom.distance(shape_1.centroid) < geom.distance(shape_2.centroid):
            shape_1_new = shape_1_new.union(geom)
          else:
            shape_2_new = shape_2_new.union(geom)
      else:
        if split_intersection.distance(shape_1.centroid) < split_intersection.distance(shape_2.centroid):
          shape_1_new = shape_1_new.union(split_intersection)
        else:
          shape_2_new = shape_2_new.union(split_intersection)


  elif isinstance(intersections, Polygon):
    if isinstance(intersection_points, MultiPoint):
      line = LineString(intersection_points.geoms)
      split_intersection = split(intersections, line)
    else:
      split_intersection = intersections

    if isinstance(split_intersection, MultiPolygon):
      for geom in split_intersection.geoms:
        if geom.distance(shape_1.centroid) < geom.distance(shape_2.centroid):
          shape_1_new = shape_1_new.union(geom)
        else:
          shape_2_new = shape_2_new.union(geom)
    else:
      if split_intersection.distance(shape_1.centroid) < split_intersection.distance(shape_2.centroid):
        shape_1_new = shape_1_new.union(split_intersection)
      else:
        shape_2_new = shape_2_new.union(split_intersection)

  return shape_1_new, shape_2_new