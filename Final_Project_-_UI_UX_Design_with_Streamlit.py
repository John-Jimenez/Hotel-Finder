import streamlit as st
import pandas as pd
import numpy as np
import requests
import time, datetime
import altair as alt


headers = {
	"X-RapidAPI-Key": "abffd08c1amsh82ab8531837f925p1f272bjsn8cc92b23debe",
	"X-RapidAPI-Host": "hotels-com-provider.p.rapidapi.com"
}

st.set_page_config(
    layout = "wide",
    page_title = "Hotel Search",
    menu_items = {
        'Get Help' : 'https://docs.streamlit.io./',
        'Report a bug' : 'https://streamlit.io/',
        'About' : '# Developed by John Jimenez using the hotels.com api'
    }
)

category = st.sidebar.selectbox("Choose a category", 
                ["By City, State, and Country",
                 "Get Hotel Details by ID"])

if category == "By City, State, and Country":

    st.image("photos/winding road1.jpg")

    col1, col2 = st.columns(2)
    with col1:
        
        st.title("Book Your Next Trip")
        st.header("Search for hotels anywhere")
        check_in_date = st.date_input("Check-in date")
        checkout_date = st.date_input("Check-out date") + datetime.timedelta(days=1)  # Add 1 day to the checkout date
        if check_in_date > checkout_date:
            st.error("Check-in date must be before check-out date")
        elif check_in_date == checkout_date:
            st.error("Check-in date and check-out date must be different")
        elif checkout_date < datetime.date.today():
            st.error("Check-out date must be after today's date")
        num_of_adults = st.select_slider("Number of Adults", options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        any_children = st.toggle("Children")
        num_of_children = 0
        children_ages = []
        if any_children:
            num_of_children = st.select_slider("Number of children", options=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
            children_ages = "5," * num_of_children     # the api needs the ages of the children, seperated by commas, so 5,5,5 are three 5 year olds
            children_ages = children_ages.rstrip(",")  # Remove the trailing comma

        lodging_type = st.multiselect("Lodging Type:", ["HOTEL", "HOSTEL", "APARTMENT HOTEL", "CHALET", "BED AND BREAKFAST"])
        if lodging_type is None:
            lodging_type = "HOTEL"

        price_min = 0
        price_max = 1000
        price_range = st.slider("Pricing", 0, 1000, (0, 1000), step = 5)
        price_min = price_range[0]
        price_max = price_range[1]

        amenities_toggled = st.toggle("Amenities")
        amenities_chosen = []
        if amenities_toggled:
            amenities_chosen = []
            amenities = ["SPA", "WiFI", "HOT TUB", "FREE AIRPORT TRANSPORTATION", 
                        "POOL","GYM", "OCEAN VIEW", "WATER PARK",
                        "BALCONY OR TERRACE", "KITCHEN KITCHENETTE", 
                        "ELECTRIC CAR", "PARKING", "CRIB", 
                        "RESTAURANT IN HOTEL", "PETS", "WASHER/DRYER",
                        "CASINO", "AIR CONDITIONING"]

            for amenity in amenities:
                if st.checkbox(amenity):
                    amenities_chosen.append(amenity)
        

        if category == "By City, State, and Country":
            countries_list=["", "US", "AE","AR","AS","AT","AU","BE","BR","CA","CH","CL","CN","CO",
                            "DE","DK","ES","FI","FR","GB","GR","HK","HU","ID","IE","IN",
                            "IS","IT","JP","KR","MX","MY","NL","NO","NZ","PE","PH","PT",
                            "SE","SG","TH","TR","TW","US","VN","XE","ZA"]
            country_selected = st.selectbox("Select a country (e.g. US)", options=countries_list)

            if country_selected:
                domains_list = pd.read_json("domains_list.JSON")  # domains_list has the conversion from a country to get the selected "locale"
                selected_locale = list(domains_list[country_selected]["supported_locales"].values())[0]["key"]

                city_state = st.text_input("Enter a city and/or state (e.g. San Francisco, CA)")

                if city_state:
                    url1 = "https://hotels-com-provider.p.rapidapi.com/v2/regions"
                    querystring = {"query":city_state,"domain": country_selected,"locale":selected_locale}

                    city_data_response = requests.get(url1, headers=headers, params=querystring)
                    city_data = city_data_response.json()
                    

                    region_id = city_data["data"][0]["essId"]["sourceId"]
                    latitude = city_data["data"][0]["coordinates"]["lat"]
                    longitude = city_data["data"][0]["coordinates"]["long"]

                    search_button = st.button("Search")

                if longitude and latitude and search_button:
                        
                    searching_message = st.info("Searching...")
                    time.sleep(3)
                    searching_message.empty()  # removes the searching_message
                    success_message = st.success("Done!")
                    

                with col2:
                    if longitude and latitude and search_button:        
                        # getting the long and lat confirms it's a place we have info on
                        url2 = "https://hotels-com-provider.p.rapidapi.com/v2/hotels/search"

                        querystring = {"region_id":region_id,"locale":selected_locale,"checkin_date":check_in_date,"sort_order":"RECOMMENDED",
                                        "adults_number":num_of_adults,"domain": country_selected,"checkout_date":checkout_date,"children_ages":children_ages,
                                        "lodging_type":lodging_type,"price_min":price_min,"star_rating_ids":"3,4,5",
                                        "meal_plan":"FREE_BREAKFAST","page_number":"1","price_max":price_max,"amenities":amenities_chosen,
                                        "payment_type":"PAY_LATER,FREE_CANCELLATION","guest_rating_min":"8","available_filter":"SHOW_AVAILABLE_ONLY"}

                        hotel_data_response = requests.get(url2, headers=headers, params=querystring)
                        hotel_data = hotel_data_response.json()
                    
                    
                        hotel_df = pd.DataFrame(columns=["Property Name","ID", "Price per Night", "Miles from Destination",
                                                        "Review Rating", "Star-Rating"])
                        coordinates_df = pd.DataFrame(columns=["Property Name","Latitude", "Longitude", "Color"])

                        bin0, bin1, bin2, bin3, bin4, bin5, bin6, bin7, bin8, bin9 = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

                        for property_info in hotel_data["properties"]:
                            if property_info is not None and "propertyImage" in property_info and property_info["propertyImage"] is not None:
                                property_name = property_info["name"]
                                property_id = property_info["id"]
                                property_image_info = property_info["propertyImage"]["image"]
                                
                                if "url" in property_image_info and property_image_info["url"] is not None:
                                    property_image = property_image_info["url"]
                                else:
                                    property_image = st.image("photos/winding road1.jpg")
                                property_price = property_info["price"]["options"][0]["formattedDisplayPrice"]
                                property_distance = property_info["destinationInfo"]["distanceFromDestination"]["value"]
                                property_reviews = property_info["reviews"]["score"]
                                property_star_rating = property_info["star"]
                                property_latitude = property_info["mapMarker"]["latLong"]["latitude"]
                                property_longitude = property_info["mapMarker"]["latLong"]["longitude"]

                                new_row = {"Property Name": property_name, "ID": property_id, 
                                        "Price per Night": property_price, "Miles from Destination": property_distance, 
                                        "Review Rating":property_reviews, "Star-Rating":property_star_rating}
                                hotel_df = pd.concat([hotel_df, pd.DataFrame([new_row])], ignore_index=True)  #appending the info to the hotel df

                                random_color = "#{:06x}".format(np.random.randint(0, 0xFFFFFF))
                                new_coordinates_row = {"Property Name": property_name,"LATITUDE": property_latitude, 
                                                    "LONGITUDE": property_longitude, "Color": random_color}
                                coordinates_df = pd.concat([coordinates_df, pd.DataFrame([new_coordinates_row])], ignore_index=True) #appending the lat & long to coord_df

                                st.subheader(property_name)
                                st.markdown(f'<p style="color: blue; text-align: center;">Property ID: {property_id}</p>', unsafe_allow_html=True)
                                st.markdown(f'<p style="color: green;">Cost per night: {property_price}</p>', unsafe_allow_html=True)
                                st.write("Miles from Destination:", property_distance)
                                st.image(property_image)
                                st.write("---")

                                modified_property_price = property_price.replace("$", "")         #remove $ and , so we can convert to int
                                modified_property_price = modified_property_price.replace("€", "" )
                                modified_property_price = modified_property_price.replace(",", "")
                                modified_property_price = int(modified_property_price)


                                if modified_property_price < 100:
                                    bin0 += 1
                                elif modified_property_price < 200 and modified_property_price >= 100:
                                    bin1 += 1
                                elif modified_property_price < 300 and modified_property_price >= 200:
                                    bin2 += 1
                                elif modified_property_price < 400 and modified_property_price >= 300:
                                    bin3 += 1
                                elif modified_property_price < 500 and modified_property_price >= 400:
                                    bin4 += 1
                                elif modified_property_price < 600 and modified_property_price >= 500:
                                    bin5 += 1
                                elif modified_property_price < 700 and modified_property_price >= 600:
                                    bin6 += 1
                                elif modified_property_price < 800 and modified_property_price >= 700:
                                    bin7 += 1
                                elif modified_property_price < 900 and modified_property_price >= 800:
                                    bin8 += 1
                                elif modified_property_price >= 900:
                                    bin9 += 1
                            

                        with col1: 
                            st.write(hotel_df)
                            st.write("---")
                            st.map(coordinates_df, color="Color")
                            st.write("---")
                            
                            source = pd.DataFrame({
                                'Number of Hotels': [bin0, bin1, bin2, bin3, bin4, bin5, bin6, bin7, bin8, bin9],
                                '($) Price Range': ['0-99', '100-199', '200-299', '300-399', '400-499', '500-599', '600-699', '700-799', '800-899', '900+']
                            })
                            #1st chart
                            bar_chart = alt.Chart(source).mark_bar().encode(
                                y = 'Number of Hotels',
                                x = '($) Price Range',
                            )
                        
                            st.altair_chart(bar_chart, use_container_width=True)    

                            
                            #2nd chart
                            chart = alt.Chart(hotel_df).mark_point().encode(
                                x = 'Review Rating',
                                y = 'Star-Rating',
                                tooltip=['ID', 'Review Rating', 'Star-Rating']
                            )

                            st.altair_chart(chart)
                        

                    elif not longitude or not latitude:
                        st.error("Please try another location")
                
                                

if category == "Get Hotel Details by ID":

    st.image("photos/cinqueterre.jpg")

    st.title("Get Hotel Details by ID")
    countries_list=[
                "", "US", "AE","AR","AS","AT","AU","BE","BR","CA","CH","CL","CN","CO",
                "DE","DK","ES","FI","FR","GB","GR","HK","HU","ID","IE","IN",
                "IS","IT","JP","KR","MX","MY","NL","NO","NZ","PE","PH","PT",
                "SE","SG","TH","TR","TW","US","VN","XE","ZA"
                ]
    
    country_selected = st.selectbox("Select a country (e.g. US)", options=countries_list)

    if country_selected:
        domains_list = pd.read_json("domains_list.JSON")
        selected_locale = list(domains_list[country_selected]["supported_locales"].values())[0]["key"]
   

    hotel_id_input = st.number_input("Input the Hotel ID Number", step=1)
    hotel_id_search_button = st.button("Search ID")

    
    if hotel_id_search_button and country_selected:
        try:
            url3 = "https://hotels-com-provider.p.rapidapi.com/v2/hotels/details"

            querystring = {"domain":country_selected,"hotel_id":hotel_id_input,"locale": selected_locale}

            hotel_details_by_id = requests.get(url3, headers=headers, params=querystring)
            hotel_details_by_id = hotel_details_by_id.json()

            amenities_listed = hotel_details_by_id["summary"]["amenities"]["topAmenities"]["items"]

            st.markdown('<h3 style="text-align: center;">Top Amenities</h3>', unsafe_allow_html=True)
            
            for amenity in amenities_listed:
                st.write("•", amenity["text"])

            photos_listed = hotel_details_by_id["propertyGallery"]["images"]

            st.markdown('<h3 style="text-align: center;">Hotel Photos</h3>', unsafe_allow_html=True)

            for photo in photos_listed:
                st.markdown(
                    f'<div style="display: flex; justify-content: center;"><img src="{photo["image"]["url"]}" alt="hotel photo" style="width: 50%;"></div>',
                    unsafe_allow_html=True)
                # Center the caption
                st.markdown(f'<p style="text-align: center;">{photo["image"]["description"]}</p>', unsafe_allow_html=True)
            
        except: 
            raise Exception("Please try another hotel ID, English information is not available.")
            