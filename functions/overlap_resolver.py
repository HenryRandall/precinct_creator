from shapely.geometry import Point, MultiPoint, Polygon, LineString, MultiPolygon, GeometryCollection
from shapely.ops import split

def overlap_resolver(shape_1, shape_2):
  """takes in 2 shapely shapes and evenly splits them based on the points of intersection"""

  # Create shapes that are the intersection of the input shapes, and a new shape for each input that lacks the overlapping area.
  intersections = shape_1.intersection(shape_2)
  shape_1_new = shape_1.difference(shape_2)
  shape_2_new = shape_2.difference(shape_1)

  # https://gis.stackexchange.com/questions/374042/find-the-intersecting-points-of-2-polygons-in-python
  # Find the points where the intersect
  intersection_points = shape_1.boundary.intersection(shape_2.boundary)

  # If there are multiple non-contiguous shapes in the intersection, loop through them
  if isinstance(intersections, MultiPolygon) or isinstance(intersections, GeometryCollection):
    for intersection in list(intersections.geoms):
      # Throw out lines
      if isinstance(intersection, LineString):
        continue
      # Calculate the points of intersection for this specific shape
      points = intersection.boundary.intersection(intersection_points)
      # If multiple points, draw a line and cut up to intersecting shape
      if isinstance(points, MultiPoint):
        line = LineString(points.geoms)
        split_intersection = split(intersection, line)
      else:
        split_intersection = intersection
      # If the split actually created multiple shapes, then give each to the closest polygon
      if isinstance(split_intersection, MultiPolygon):
        for geom in split_intersection.geoms:
          if geom.distance(shape_1.centroid) < geom.distance(shape_2.centroid):
            shape_1_new = shape_1_new.union(geom)
          else:
            shape_2_new = shape_2_new.union(geom)
      # If the intersection didn't split (meaning that one shape is poking into another) then give that to the closest shape
      else:
        if split_intersection.distance(shape_1.centroid) < split_intersection.distance(shape_2.centroid):
          shape_1_new = shape_1_new.union(split_intersection)
        else:
          shape_2_new = shape_2_new.union(split_intersection)

  # If there is 1 polygon in the intersection, no need to loop
  elif isinstance(intersections, Polygon):
    # If multiple points, draw a line and cut up to intersecting shape
    if isinstance(intersection_points, MultiPoint):
      line = LineString(intersection_points.geoms)
      split_intersection = split(intersections, line)
    else:
      split_intersection = intersections
    # If the split actually created multiple shapes, then give each to the closest polygon
    if isinstance(split_intersection, MultiPolygon):
      for geom in split_intersection.geoms:
        if geom.distance(shape_1.centroid) < geom.distance(shape_2.centroid):
          shape_1_new = shape_1_new.union(geom)
        else:
          shape_2_new = shape_2_new.union(geom)
    # If the intersection didn't split (meaning that one shape is poking into another) then give that to the closest shape
    else:
      if split_intersection.distance(shape_1.centroid) < split_intersection.distance(shape_2.centroid):
        shape_1_new = shape_1_new.union(split_intersection)
      else:
        shape_2_new = shape_2_new.union(split_intersection)

  return shape_1_new, shape_2_new

def shape_conditioner(poly):
  """Removes lines and points from Geometric Collections and simplfies them into polygons or multipolygons"""
  # loop through every geomerty
  for i, geomcoll in poly.items():
    # If a geometry collection, sort based on geometry
    if isinstance(geomcoll, GeometryCollection):
      shapes = []
      for geom in geomcoll.geoms:
        if isinstance(geom, (Point, LineString)):
          continue
        elif isinstance(geom, Polygon):
          shapes.append(geom)
        elif isinstance(geom, MultiPolygon):
          for shape in geom.geoms:
            shapes.append(shape)
      # If only 1 shape make polygon, else multipolygon
      if len(shapes) == 1:
        poly[i] = shapes[0]
      else:
        poly[i] = MultiPolygon(shapes)
  return poly