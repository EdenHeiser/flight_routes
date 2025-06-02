import pandas as pd
import numpy as np
from geopy.distance import geodesic
from sklearn.neighbors import BallTree


def add_country_name_to_airports(airports):
    '''
    The airports csv have only iso country code, so to add country name,
    the func take csv of iso_code-country name and merge it to the airports csv
    :param airports:
    :return:
    '''
    iso = pd.read_csv(r'C:\Users\97254\PyCharmMiscProject\csvs\country_iso.csv')
    iso = iso[['name', 'alpha-2']]
    airports = pd.merge(airports, iso, how='left', left_on='iso_country', right_on='alpha-2')
    return airports

def replace_country_name_for_airports(airports):
    '''
    There are difference in the country names in airports and in passports
    This func have dictionary of the original names and the good ones based on passport.csv
    It replace the old names with the good ones
    '''
    fix_countries_dict = {
    'Bolivia, Plurinational State of' : 'Bolivia',
    'Anguilla' : 'United Kingdom',
    'Aruba' : 'Netherlands',
    'Bermuda' : 'United Kingdom',
    'Bonaire, Sint Eustatius and Saba' : 'Netherlands',
    'British Indian Ocean Territory' : 'United Kingdom',
    'Brunei Darussalam' : 'Brunei',
    'Cabo Verde' : 'Cape Verde',
    'Christmas Island' : 'Australia',
    'Cocos (Keeling) Islands' : 'Australia',
    'Cook Islands' : 'New Zealand',
    'Czechia' : 'Czech Republic',
    'Congo, Democratic Republic of the' : 'DR Congo',
    "Côte d'Ivoire" : 'Ivory Coast',
    'Eswatini' : 'Swaziland',
    'Falkland Islands (Malvinas)' : 'United Kingdom',
    'French Guiana' : 'France',
    'French Polynesia' : 'France',
    'French Southern Territories' : 'France',
    'Gibraltar' : 'United Kingdom',
    'Greenland' : 'Denmark',
    'Guadeloupe' : 'France',
    'Guam' : 'United States',
    'Guernsey' : 'United Kingdom',
    'Iran, Islamic Republic of' : 'Iran',
    'Isle of Man' : 'United Kingdom',
    'Jersey' : 'United Kingdom',
    "Korea, Democratic People's Republic of" : 'North Korea',
    'Korea, Republic of' : 'South Korea',
    "Lao People's Democratic Republic" : 'Laos',
    'Martinique' : 'France',
    'Mayotte' : 'France',
    'Micronesia, Federated States of' : 'Micronesia',
    'Moldova, Republic of' : 'Moldova',
    'Montserrat' : 'United Kingdom',
    'Netherlands, Kingdom of the' : 'Netherlands',
    'New Caledonia' : 'France',
    'Niue' : 'New Zealand',
    'Norfolk Island' : 'Australia',
    'Northern Mariana Islands' : 'United States',
    'Puerto Rico' : 'United States',
    'Russian Federation' : 'Russia',
    'Réunion' : 'France',
    'Saint Barthélemy' : 'France',
    'Saint Helena, Ascension and Tristan da Cunha' : 'United Kingdom',
    'Saint Martin (French part)' : 'France',
    'Saint Pierre and Miquelon' : 'France',
    'Sint Maarten (Dutch part)' : 'Netherlands',
    'Syrian Arab Republic' : 'Syria',
    'Taiwan, Province of China' : 'Taiwan',
    'Tanzania, United Republic of' : 'Tanzania',
    'Turks and Caicos Islands' : 'United Kingdom',
    'Türkiye' : 'Turkey',
    'United Kingdom of Great Britain and Northern Ireland' : 'United Kingdom',
    'United States Minor Outlying Islands' : 'United States',
    'United States of America' : 'United States',
    'Venezuela, Bolivarian Republic of' : 'Venezuela',
    'Viet Nam' : 'Vietnam',
    'Virgin Islands (British)' : 'United Kingdom',
    'Virgin Islands (U.S.)' : 'United States',
    'Wallis and Futuna' : 'France',
    'Western Sahara' : 'Morocco',
    'American Samoa' : 'United States',
    'Cayman Islands' : 'United Kingdom'
    }
    airports['country'] = airports['country'].replace(fix_countries_dict)
    return airports


def replace_country_name_for_wpi(wpi):
    '''
    There are difference in the country names in airports and in WPI'
    This func have dictionary of the original names and the good ones based on airports.csv
    It replace the old names with the good ones
    '''
    fix_countries_dict = {
        r'Cote d\' Ivoire' : 'Ivory Coast',
        'Czechia': 'Czech Republic',
        'Democratic Republic of the Congo': 'DR Congo',
        'Eswatini': 'Swaziland',
        'Kyrgyz Republic': 'Kyrgyzstan',
        'Palestine': 'Palestine, State of',
        'The Gambia': 'Gambia',
        'Turkiye': 'Turkey',
        'United States of America': 'United States',
        'Republic of the Congo' : 'Congo'}
    wpi['region'] = wpi['region'].replace(fix_countries_dict)
    return wpi



def make_airport_gg_df(airports_csv):
    ''''
    filter only the important columns for the min_dis calculation
    between route points and airports gg
    retrieve also the rank column to be able to show it when hover
    '''
    return airports_csv[['id', 'airport_name', 'longitude_deg', 'latitude_deg', 'rank']]

def calculate_distance(origin_lon, origin_lat, destination_lon, destination_lat):
    '''
    calculate the distance between two points using great circle distance
    :param origin_lon: start longitude
    :param origin_lat: start latitude
    :param destination_lon: end longitude
    :param destination_lat: end latitude
    :return: distance between two points in kilometers
    '''
    origin = (origin_lat, origin_lon)
    destination = (destination_lat, destination_lon)
    distance = geodesic(origin, destination).kilometers
    return distance

def calculate_step_size(airplane_model,airplane_models):
    '''
    calculate and return the step size for creating the route points
    it takes airplane model and return the step size in km
    it will make that the difference from the follwing points
    will be 5 minutes of cruising speed
    '''
    # models = pd.read_csv('airplane_models.csv')
    speed = airplane_models[airplane_models['Aircraft Model'] == airplane_model]['Cruising Speed'].iloc[0]
    km_difference = 5 * (speed/60)
    return km_difference

def find_closest_airport(points, airports):
    '''
    This func take the points on the route, and takes airports csv
    Then we calculate the closest airport from each point
    using balltree
    :param points:
    :param airports:
    :return:
    '''
    # used haversine calculation, its less accuracy the great-circle but has
    # better running time, we have to make a lot of distance calculation so....

    EARTH_RADIUS_KM = 6371.0088

    # Convert to radians for haversine
    query_radians = np.radians(points[['latitude', 'longitude']].values)
    candidates_radians = np.radians(airports[['latitude_deg', 'longitude_deg']].values)

    # Build BallTree with Haversine metric
    #use balltree to find the nearest neighbors - the closet point = closest airport
    tree = BallTree(candidates_radians, metric='haversine')

    # Query the nearest neighbor for each point
    # Returns distances in radians, so multiply by Earth's radius to get kilometers
    distances, indices = tree.query(query_radians, k=1)  # k=1 means closest point

    # Convert distance to kilometers
    distances_km = distances.flatten() * EARTH_RADIUS_KM

    # Match closest candidate points
    closest_points = airports.iloc[indices.flatten()].reset_index(drop=True)
    # Combine results
    result = points.copy()
    result['min_distance_km'] = distances_km
    result = pd.concat([result, closest_points.add_prefix('closest_')], axis=1)

    # Preview
    print(result['closest_airport_name'])
    return result

def origin_and_destination(airports, origin_airport_name, destination_airport_name):
    '''
    get origin and destination airports name
    return 4 arguments tuple that represents
    the lon lat for each airport
    in this specific order: tuple(origin_lon, origin_lat, destination_lon, destination_lat)
    '''
    origin_airport_lon = airports[airports['airport_name'] == origin_airport_name]['longitude_deg'].iloc[0]
    origin_airport_lat = airports[airports['airport_name'] == origin_airport_name]['latitude_deg'].iloc[0]
    destination_airport_lon = airports[airports['airport_name'] == destination_airport_name]['longitude_deg'].iloc[0]
    destination_airport_lat = airports[airports['airport_name'] == destination_airport_name]['latitude_deg'].iloc[0]
    return origin_airport_lon, origin_airport_lat, destination_airport_lon, destination_airport_lat
