import pandas as pd
import numpy as np
from calculations_and_manipulations import add_country_name_to_airports
from calculations_and_manipulations import replace_country_name_for_airports
from calculations_and_manipulations import replace_country_name_for_wpi


def fix_wpi(wpi):
    wpi = replace_country_name_for_wpi(wpi)
    wpi['score'] = wpi['score\xa0']
    wpi = wpi[['rank', 'region', 'score']]
    return wpi


def add_wpi_to_airports(airports, wpi):
    '''
    Add column of wpi rank to airports csv, based on the country.
    '''
    airports = pd.merge(airports, wpi, left_on='country', right_on = 'region', how = 'left')
    airports =airports.drop(columns=['region', 'score'])
    return airports

def fix_airports(airports, fixed_wpi):
    airports = add_country_name_to_airports(airports)
    #filter out the non-relevant columns
    airports = airports[['id', 'ident', 'type', 'name_x', 'latitude_deg', 'longitude_deg', 'iso_country', 'name_y']]
    #rename columns
    airports = airports.rename(columns={
    'name_x': 'airport_name',
    'name_y': 'country'
    })
    #add manually countries to specific isos with problems
    #XK is kosovo and XP is also china
    airports['country'] = np.where(
    (airports['iso_country']=='XK') & (airports['country'].isna()),
    'Kosovo',
    np.where(
        (airports['iso_country']=='XP') & (airports['country'].isna()),
        'China',
        airports['country']
        )
    )

    #also for namibia
    airports['iso_country'] = np.where(
    (airports['country'] == 'Namibia') & (airports['iso_country'].isna()),
    'NA',
    airports['iso_country']
    )

    airports = replace_country_name_for_airports(airports)
    #dump all of the seaplane bases and closed ones
    #also beacuse there are some mistakes in the lengths
    #I will also dump the balloonports and heliports
    airports = airports[~airports['type'].isin(['seaplane_base', 'closed', 'heliport', 'balloonport'])]
    airports = add_wpi_to_airports(airports, fixed_wpi)
    airports['rank'] = airports['rank'].apply(lambda x : int(x) if x > 0 else -1)
    airports['airport_name'] = airports.apply(lambda x : x['airport_name'] + ' - ' + x['country'], axis = 1)
    return airports

def fix_runways(runways, updated_airports):
    def ft_to_m(feet):
        return feet * 0.3048

    # the func take the og runways and update_airports csvs and
    # return the runways fixed, only the longest airstrip for each airport will
    # be returned

    #filter out the non-relevant columns
    runways = runways[['id', 'airport_ref', 'airport_ident', 'length_ft','lighted', 'closed']]
    #retrieve for each airport the longest runway
    longest_runway = runways.groupby('airport_ident').max('length_ft')
    #create type-indent df, later we will use it for inject
    #the median lengths for nulls
    types = updated_airports[['ident', 'type']]
    #merge it with our df
    merged_with_type = pd.merge(longest_runway, types, left_on = 'airport_ident', right_on = 'ident')
    #calculate the median length for each type of airport
    median_runways_per_airport_type = merged_with_type[['type', 'length_ft']].groupby('type').median('length_ft')
    #merge it with our df
    longest_runway = pd.merge(merged_with_type, median_runways_per_airport_type, on='type')
    #inject all the nulls with the median values
    longest_runway['length_ft_x'] = longest_runway['length_ft_x'].fillna(longest_runway['length_ft_y'])
    #drop unneccesary columns
    longest_runway.drop(['type', 'length_ft_y'], axis=1, inplace=True)
    #convert the lengths from ft to meters
    longest_runway['length_ft_x'] = longest_runway['length_ft_x'].apply(lambda x: ft_to_m(x))
    #rename the columns
    longest_runway.rename(columns={'length_ft_x': 'length_meters'}, inplace=True)
    return longest_runway


def fix_passport(passport):
    passport['approved'] = passport['value'].apply(lambda x : 0 if x == 'no admission' else 1)
    passport = passport.drop(columns=['value', 'Unnamed: 0'], axis = 1)
    return passport


wpi = pd.read_csv(
    r"C:\Users\97254\Downloads\world_peace_index.csv",
    encoding="cp1252"        # or try "latin-1"
)
wpi = fix_wpi(wpi)

airports = pd.read_csv(r"C:\Users\97254\Downloads\airports.csv")
fixed_airports = fix_airports(airports, wpi)


runways = pd.read_csv(r"C:\Users\97254\PyCharmMiscProject\data cleaning\runways.csv")
fixed_runways = fix_runways(runways, fixed_airports)

passports = pd.read_csv(r"C:\Users\97254\PyCharmMiscProject\data cleaning\passport_index_reshaped.csv")
airplanes = pd.read_csv(r"C:\Users\97254\PyCharmMiscProject\data cleaning\airplane_models.csv")

fixed_passport = fix_passport(passports)
