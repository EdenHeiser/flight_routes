import pandas as pd
import numpy as np
from calculations_and_manipulations import calculate_distance
from calculations_and_manipulations import calculate_step_size
from geographiclib.geodesic import Geodesic
import folium
from folium import CircleMarker, Marker



def create_route_points(start_lon, start_lat, end_lon, end_lat, airplane_model, airplanes):
    '''
    The func take the start/end coordinates and the airplane model.
    It generates df with points on the shortest route between origin and destination.
    The shortest distance is calclated using great circle distance.

    :param start_lon:
    :param start_lat:
    :param end_lon:
    :param end_lat:
    :param airplane_model:
    :return:
    '''
    # calculate distance
    total_distance_km = calculate_distance(start_lon, start_lat, end_lon, end_lat)

    # Create geodesic line
    geod = Geodesic.WGS84
    line = geod.InverseLine(start_lat, start_lon, end_lat, end_lon)

    # Step size and number of steps
    step_km = calculate_step_size(airplane_model, airplanes)
    n_steps = int(total_distance_km // step_km) + 1

    # Compute points along the geodesic path
    route_points = []
    for i in range(n_steps + 1):
        s = min(step_km * i, total_distance_km) * 1000  # convert to meters
        position = line.Position(s, Geodesic.STANDARD | Geodesic.LONG_UNROLL)
        route_points.append({
            'latitude': position['lat2'],
            'longitude': position['lon2'],
            'distance_from_start_km': s / 1000,  # back to km
            'index': i
        })

    return pd.DataFrame(route_points)
def create_galap_id(result, min_danger_distance=600):
    '''
    create id for each steak of following dangerous points
    '''

    result['danger'] = np.where(result['min_distance_km'] > min_danger_distance, 1, 0)
    result['cumulative_sum'] = np.where(result['danger'] == 1, result['danger'].cumsum(), 0)

    result['galap_id'] = 0
    for i in range(1, len(result)):
        if result['cumulative_sum'][i] in (0, 1):
            result['galap_id'][i] = int(result['galap_id'][i - 1]) + 1
        else:
            result['galap_id'][i] = result['galap_id'][i - 1]
    return result
def plot_route_map(df, lat_col='latitude', lon_col='longitude', max_points_for_green = 3,
                   max_points_for_yellow = 6):
    """
    The func take points_Df, name of gg columns, max_points per color.
    each point difference represent 5 minutes of flight time
    so 3 points is 15 minutes.
    Its plot with folium a map with all the points in the route, and it
    color the points with green/yellow/red colors, each represent level of dager
    green- good
    yellow- more than 15 minutes that the closest approved airport is more than min_danger_distance kms
    red- more than 30 minutes
    """
    center = [df[lat_col].mean(), df[lon_col].mean()]
    m = folium.Map(location=center, zoom_start=6)

    def get_color(count):
        if count < max_points_for_green:
            return 'green'
        elif count < max_points_for_yellow:
            return 'yellow'
        else:
            return 'red'

    for _, row in df.iterrows():
        tooltip_txt = (
            f"Closest: {row['closest_airport_name']}<br>"
            f"Distance: {round(row['min_distance_km'], 3)} km"
        )
        CircleMarker(
            location=[row[lat_col], row[lon_col]],
            radius=5,
            color=get_color(row['galap_count']),
            fill=True,
            fill_color=get_color(row['galap_count']),
            fill_opacity=0.7,
            #popup=f"Index: {row['index']}, Count: {row['galap_count']}",
            tooltip = tooltip_txt,
            parse_html = True
        ).add_to(m)

    # origin
    o = df.iloc[0]
    Marker([o[lat_col], o[lon_col]], popup='Origin', icon=folium.Icon(color='blue', icon='play')).add_to(m)
    # destination
    d = df.iloc[-1]
    Marker([d[lat_col], d[lon_col]], popup='Destination', icon=folium.Icon(color='darkred', icon='stop')).add_to(m)
    return m
