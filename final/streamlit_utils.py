from calculations_and_manipulations import *
from fix_dbs import *
from route_and_galaps import *
from filters_for_destination import *
import streamlit as st
from streamlit_folium import st_folium
from folium import Marker, PolyLine

def generate_segment():
    '''
    Generate the route for the closest airport from specific clicked point
    :return:
    '''
    click = st.session_state.get('last_click')
    if not click:
        st.error("Please click a route point on the first map first.")
        return
    lat, lon = click['lat'], click['lng']
    airports_df = make_airport_gg_df(fixed_airports)
    lat_col = 'latitude_deg' if 'latitude_deg' in airports_df.columns else 'latitude'
    lon_col = 'longitude_deg' if 'longitude_deg' in airports_df.columns else 'longitude'
    airports_df['dist'] = (
        (airports_df[lat_col] - lat) ** 2 +
        (airports_df[lon_col] - lon) ** 2
    ) ** 0.5
    nearest = airports_df.loc[airports_df['dist'].idxmin()]
    st.session_state['segment_ready'] = True
    st.session_state['segment_info']  = {
        'origin':    (lat, lon),
        'dest':      (nearest[lat_col], nearest[lon_col]),
        'dest_name': 'airport name:' + nearest['airport_name'] + '.   wpi rank:  ' + str(nearest['rank'])
    }

def create_flags():
    '''
    Create flags of session states for streamlit
    '''
    st.session_state.setdefault('show_route', False)
    st.session_state.setdefault('segment_ready', False)

    st.session_state.setdefault('segment_info', None)

def create_streamlit(fixed_airports, fixed_runways, airplanes, passports, min_danger_dist = 600):
    '''
    Create the streamlit app
    '''
    st.title("🛫 Interactive Route Map Between Airports")

    # placeholder for the second (segment) map
    # segment_placeholder = st.empty()

    # initialize flags
    create_flags()

    # 1) Origin & plane selectors
    airport_list    = sorted(fixed_airports['airport_name'].dropna().unique())
    airplane_models = sorted(airplanes['Aircraft Model'].dropna().unique())

    origin         = st.selectbox("Select Origin Airport", airport_list, key="ui_origin")
    airplane_model = st.selectbox("Select Airplane Model", airplane_models, key="ui_model")

    # 2) Generate Destinations button
    if st.button("Generate Destinations", key="btn_gen_dest"):
        st.session_state['show_route']    = True
        st.session_state['segment_ready'] = False
        st.session_state.pop('last_click', None)

    # 3) Destination dropdown + first map
    if st.session_state.show_route:
        origin_country = fixed_airports.loc[
            fixed_airports['airport_name'] == origin, 'country'
        ].iloc[0]
        countries    = valid_countries_for_landing(origin_country, passports)
        runways      = valid_landing_runways_based_on_airplane(
            airplane_model, airplanes, fixed_runways
        )
        destinations = valid_airports_for_landing(
            fixed_airports, countries, runways
        )

        if not destinations:
            st.warning(f"No approved destinations for {origin}")
            st.session_state['show_route'] = False
        else:
            destination = st.selectbox("Select Destination Airport", destinations, key="ui_dest")
            st.write(f"✈️ From **{origin}** to **{destination}**")

            # compute route DataFrame
            gg        = origin_and_destination(fixed_airports, origin, destination)
            route_df  = create_route_points(*gg, airplane_model, airplanes)
            result    = find_closest_airport(route_df, make_airport_gg_df(fixed_airports))
            result    = result.sort_values('index')
            result    = create_galap_id(result, min_danger_dist)
            result['galap_count'] = result.groupby('galap_id')['galap_id'].transform('count')

            if result.empty:
                st.error("No route data available.")
            else:
                click_ctx = st_folium(
                    plot_route_map(result, max_points_for_green=3, max_points_for_yellow=6),
                    width=700, height=500,
                    returned_objects=['last_object_clicked'],
                    key="route_map"
                )
                clicked = click_ctx.get('last_object_clicked')
                if clicked:
                    raw_lat, raw_lng = clicked['lat'], clicked['lng']
                    pts = result[['latitude', 'longitude']].copy()
                    pts['dist'] = (
                        (pts['latitude'] - raw_lat)**2 +
                        (pts['longitude'] - raw_lng)**2
                    )**0.5
                    snap = pts.loc[pts['dist'].idxmin()]
                    st.session_state['last_click']    = {'lat': snap['latitude'], 'lng': snap['longitude']}
                    st.session_state['segment_ready'] = True



                    # 4) Generate Segment button
                    if st.session_state.get('last_click'):
                        if st.button("Generate Closest Route", key="btn_gen_seg"):
                            generate_segment()

                        # *** Create the placeholder right here, below the button: ***
                        segment_placeholder = st.empty()

                    # 5) Render the second map into that placeholder
                    if st.session_state.segment_ready:
                        info = st.session_state['segment_info']
                        if info is None:
                            info = {}
                            info['origin'] = [0, 0]
                        lat, lon = info['origin']
                        ap_lat, ap_lon = info.get('dest', (0, 0))

                        with segment_placeholder.container():
                            st.subheader("🛬 Route Segment to Closest Airport")
                            seg_map = folium.Map(location=[lat, lon], zoom_start=8)
                            Marker(
                                [lat, lon],
                                popup=f"Latitude: {lat:.6f}, Longitude: {lon:.6f}",
                                icon=folium.Icon(color='blue', icon='play')
                                ).add_to(seg_map)
                            Marker([ap_lat, ap_lon], popup=info.get('dest_name', 'Unknown Destination'),
                                   icon=folium.Icon(color='green', icon='plane')
                                   ).add_to(seg_map)


                            geod = Geodesic.WGS84
                            line = geod.InverseLine(lat, lon, ap_lat, ap_lon)
                            arc = [
                                (line.Position(line.s13 * i / 99)['lat2'],
                                 line.Position(line.s13 * i / 99)['lon2'])
                                for i in range(100)
                            ]
                            PolyLine(locations=arc, weight=3, color='red').add_to(seg_map)
                            st_folium(seg_map, width=700, height=500, key="segment_map")