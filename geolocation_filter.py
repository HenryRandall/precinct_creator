# First 2 Functions taken mostly from this research
# https://autogis-site.readthedocs.io/en/2019/notebooks/L3/nearest-neighbor-faster.html
from sklearn.neighbors import BallTree
import numpy as np
import statistics
import math

def get_nearest(src_points, candidates, k_neighbors=1):
    """Find nearest neighbors for all source points from a set of candidate points"""

    # Create tree from the candidate points
    tree = BallTree(candidates, leaf_size=15, metric='haversine')

    # Find closest points and distances
    distances, indices = tree.query(src_points, k=k_neighbors)

    # Transpose to get distances and indices into arrays
    distances = distances.transpose()
    indices = indices.transpose()

    # Get closest indices and distances (i.e. array at index 0)
    # note: for the second closest points, you would take index 1, etc.
    closest = indices[k_neighbors-1]
    closest_dist = distances[k_neighbors-1]

    # Return indices and distances
    return (closest, closest_dist)

def nearest_neighbor(left_gdf, right_gdf, k, return_dist=True):
  """
  For each point in left_gdf, find kth closest point in right GeoDataFrame and return them.

  NOTICE: Assumes that the input Points are in WGS84 projection (lat/lon).
  """

  left_geom_col = left_gdf.geometry.name
  right_geom_col = right_gdf.geometry.name

  # Ensure that index in right gdf is formed of sequential numbers
  right = right_gdf.copy().reset_index(drop=True)

  # Parse coordinates from points and insert them into a numpy array as RADIANS
  left_radians = np.array(left_gdf[left_geom_col].apply(lambda geom: (geom.x * np.pi / 180, geom.y * np.pi / 180)).to_list())
  right_radians = np.array(right[right_geom_col].apply(lambda geom: (geom.x * np.pi / 180, geom.y * np.pi / 180)).to_list())

  # Find the nearest points
  # -----------------------
  # closest ==> index in right_gdf that corresponds to the closest point
  # dist ==> distance between the nearest neighbors (in meters)

  closest, dist = get_nearest(src_points=left_radians, candidates=right_radians, k_neighbors=k)

  # Return points from right GeoDataFrame that are closest to points in left GeoDataFrame
  closest_points = right.loc[closest]

  # Ensure that the index corresponds the one in left_gdf
  closest_points = closest_points.reset_index(drop=True)

  # Add distance if requested
  if return_dist:
      # Convert to meters from radians
      earth_radius = 6371000  # meters
      closest_points['distance'] = dist * earth_radius

  return closest_points

def geolocation_filter(gdf, geolocated_error_thresh, stdev_from_mean, crs):
  gdf = gdf.reset_index()
  gdf = gdf.to_crs(crs="EPSG:4326")
  k = math.floor(len(gdf.index) * geolocated_error_thresh)+1 #Since k=1 finds distnace to self add 1 to counter act
  dist_gdf = nearest_neighbor(gdf,gdf,k)
  # add distance measure to old dataframe
  gdf['distance'] = dist_gdf['distance']

  # Calculate Summary Stats and filter out distance outliers
  stdev_dis = statistics.stdev(gdf['distance'])
  mean_dis = statistics.mean(gdf['distance'])
  lb_dis = mean_dis - (stdev_from_mean*stdev_dis)
  ub_dis = mean_dis + (stdev_from_mean*stdev_dis)

  # Cleaning data by removing outliers
  gdf = gdf[gdf['distance'] >= lb_dis]
  gdf = gdf[gdf['distance'] <= ub_dis]

  # Return to static CRS and drop distance column
  gdf = gdf.to_crs(crs)
  gdf.drop(columns='distance', inplace = True)

  return gdf