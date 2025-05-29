from streamlit_utils import create_streamlit
from fix_dbs import *


wpi = pd.read_csv(r"C:\Users\97254\Downloads\world_peace_index.csv", encoding="cp1252")
wpi = fix_wpi(wpi)

#fix the airports csv
#add country and fix the country name
airports = pd.read_csv(r"C:\Users\97254\Downloads\airports.csv")
fixed_airports = fix_airports(airports, wpi)

runways = pd.read_csv(r"C:\Users\97254\PyCharmMiscProject\data cleaning\runways.csv")
fixed_runways = fix_runways(runways, fixed_airports)

passports = pd.read_csv(r"C:\Users\97254\PyCharmMiscProject\data cleaning\passport_index_reshaped.csv")
airplanes = pd.read_csv(r"C:\Users\97254\PyCharmMiscProject\data cleaning\airplane_models.csv")



create_streamlit(fixed_airports, fixed_runways, airplanes, passports, 600)