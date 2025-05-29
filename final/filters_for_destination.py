from fix_dbs import fix_passport

def valid_countries_for_landing(origin_country, passports):
    '''
    The func take the origin country and passports dataframe
    and return a list of all the valid countries for landing.
    '''
    #reshape the passports DB
    fixed_passport = fix_passport(passports)
    #retrieve only the rows for the specific origin country
    fixed_passport = fixed_passport[fixed_passport['from'] == origin_country]
    #make a list for all the approved countries based on the DB + th origin country
    approved_countries_for_landing = list(fixed_passport[fixed_passport['approved'] == 1]['to']) + [origin_country]
    return approved_countries_for_landing


def valid_landing_runways_based_on_airplane(airplane, airplane_models, fixed_runways):
    '''
    The func take the airplane and airplane_models dataframe and the fixed_runways
    and return a list of idents of the airports that the specific airplane model
    that given can land there based on the length of the longest runway in the airport
    '''
    min_landing_length = (
        airplane_models
        .loc[airplane_models['Aircraft Model'] == airplane, 'Minimum Runway Length (m)']
        .iloc[0]
    )
    valid_idents_for_landing = list(fixed_runways[fixed_runways['length_meters'] > min_landing_length]['ident'])
    return valid_idents_for_landing


def valid_airports_for_landing(fixed_airports, approved_countries_for_landing, valid_idents_for_landing):
    '''
    The func take the fixed_airports csv, the countries that the plane that came from
    the origin country can land in it and all the airport idents that the specific
    airplane model can land in it based on the runway length.
    It returns a list of all of the aiports that it can land in it.
    '''
    valid_airports_lst = list(fixed_airports[(fixed_airports['country'].isin(approved_countries_for_landing))
    & (fixed_airports['ident'].isin(valid_idents_for_landing))]['airport_name'])
    return valid_airports_lst
