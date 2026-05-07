'''
Name: Jake Schunke
Class: CS 230 - 8
Data: Lego Stores in the USA and Canada
URL:

Description:
This Streamlit app explores the LEGO store locations in the USA and in Canada.
The users are able to filter stores by country, state/province and city.
Then they can view summary metrics, bar and pie charts, a sorted table, and an interactive
map to see where stores are most popular.

AI Usage:
Parts of the header, data cleaning, charts, sidebar filters, tabs and maps
were made with help from AI tools. I put all information in the AI Report
Section 1-5 of AI Report show all prompts, output and revisions
'''

import pandas as pd
import streamlit as st
import pydeck as pdk
import matplotlib.pyplot as plt

# [ST4] Page setup and custom styling

st.set_page_config(page_title="LEGO Store Explorer", page_icon="LEGO_logo.png", layout="wide")

st.markdown("""
<style>
.main{
    background: linear-gradient(180deg, #f4f9ff 0%, #ffffff 40%);
}
h1, h2, h3{
    color: #12355b;
}
.story-box{
    background-color: #eaf4ff;
    color: #12355b;
    padding: 10px;
    border-left: 6px solid #1f77b4;
    padding: 16px;
    border-radius: 10px;
    margin-bottom: 12px;
}
.metric-box{
    background-color: #f8fbff;
    padding: 10px;
    border-radius: 10px;
}
.small-text{
    color: #4f4f4f;
    font-size: 0.95rem;
}
</style>
""",unsafe_allow_html=True)

# [PY1] Function with 2+ parameters and one default value

def read_data(file_name= "LegoUSACanada.csv", drop_empty = True):
    df = pd.read_csv(file_name)
    if drop_empty:
        df = df.dropna(how="all")
    return df

# [DA1] Clean Data
# [PY3] Error checking with try.except

def clean_data(df):
    try:
        df.columns = df.columns.str.strip()
        df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
        df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
        df["Store Name"] = df["Store Name"].astype(str).str.strip()
        df["Phone"] = df["Phone"].astype(str).str.strip()
        df["Full Address"] = df["Full Address"].astype(str).str.strip()
        df["Street"] = df["Street"].astype(str).str.strip()
        df["City"] = df["City"].astype(str).str.strip().str.title()
        df["State"] = df["State"].astype(str).str.strip().str.upper()
        df["Country"] = df["Country"].astype(str).str.strip().str.upper()
        df["Zip"] = df["Zip"].astype(str).str.strip()

        df = df.dropna(subset = ["Longitude", "Latitude", "Store Name", "City", "State", "Country"])
        df = df.drop_duplicates(subset = ["Store Name", "City", "State", "Country"])

        return df
    except Exception as e:
        st.error(f"There was an error cleaning the data: {e}")
        return pd.DataFrame()

# [PY2] Function that requires more than one value
def get_summary(df):
    total_stores = len(df)
    total_states = df["State"].nunique()
    total_cities = df["City"].nunique()
    total_countries = df["Country"].nunique()
    return total_stores, total_states, total_cities, total_countries

# Get unique countries

def get_all_countries(df):
    country_list = []
    for index, row in df.iterrows():
        if row["Country"] not in country_list:
            country_list.append(row["Country"])
    country_list.sort()
    return country_list

# Get states for chosen country

def get_states_by_country(df, selected_country):
    state_list = []
    for index, row in df.iterrows():
        if row["Country"] == selected_country:
            if row["State"] not in state_list:
                state_list.append(row["State"])
    state_list.sort()
    return state_list

# [DA4] [DA5] Filter data

def filter_data(selected_country, selected_states, city_name):
    df = read_data()
    df = clean_data(df)

    df = df.loc[df["Country"] == selected_country]

    if len(selected_states) > 0:
        df = df.loc[df["State"].isin(selected_states)]

    if city_name != "":
        df = df.loc[df["City"].str.contains(city_name, case=False, na=False)]

    return df

# Count stores by state

def count_states(state_list, df):
    counts = []
    for state in state_list:
        count = df.loc[df["State"] == state].shape[0]
        counts.append(count)
    return counts

# Count stores by city

def count_cities(city_list, df):
    counts = []
    for city in city_list:
        count = df.loc[df["City"] == city].shape[0]
        counts.append(count)
    return counts

# Pie chart with explode

def generate_pie_chart(counts, labels, title):
    plt.figure(figsize=(4,4))
    explode = [0] * len(counts)

    if len(counts) > 0:
        max_index = counts.index(max(counts))
        explode[max_index] = 0.15

    plt.pie(counts, labels=labels, autopct="%1.1f%%", explode=explode)
    plt.title(title)
    return plt

# Bar chart
def generate_bar_chart(x_values, y_values, chart_title, x_label, y_label, color = "steelblue"):
    plt.figure(figsize=(8,4))
    plt.bar(x_values, y_values, color=color)
    plt.xticks(rotation=45, ha="right")
    plt.title(chart_title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.tight_layout()
    return plt

# [DA6] Pivot table

def make_pivot_table(df):
    pivot = df.pivot_table(index= "State", values= "Store Name", aggfunc= "count")
    pivot = pivot.rename(columns={"Store Name": "Store Count"})
    return pivot

# Extra Summary Function

def get_top_state_and_city(df):
    state_counts = df.groupby("State")["Store Name"].count().reset_index()
    state_counts.columns = ["State", "Store Count"]
    state_counts = state_counts.sort_values(by=["Store Count"], ascending=False)

    city_counts = df.groupby("City")["Store Name"].count().reset_index()
    city_counts.columns = ["City", "Store Count"]
    city_counts = city_counts.sort_values(by=["Store Count"], ascending=False)

    top_state = state_counts.iloc[0]["State"]
    top_state_count = state_counts.iloc[0]["Store Count"]

    top_city = city_counts.iloc[0]["City"]
    top_city_count = city_counts.iloc[0]["Store Count"]

    return top_state, top_state_count, top_city, top_city_count

# [MAP] Map

def generate_map(df):
    map_df = df[["Store Name", "Phone", "Longitude", "Latitude", "City", "State", "Full Address", "Country"]]

    view_state = pdk.ViewState(
        latitude = map_df["Latitude"].mean(),
        longitude = map_df["Longitude"].mean(),
        zoom = 3.2,
        pitch = 35
    )

    layer = pdk.Layer(
        "ScatterplotLayer",
        data = map_df,
        get_position = '[Longitude, Latitude]',
        get_radius = 35000,
        get_color = '[20, 110, 180, 180]',
        pickable = True,
    )

    tooltip = {
        "html": "<b>{Store Name}</b><br/>{Phone}<br/>{City},{State}<br/>{Country}<br/>{Full Address}",
        "style": {"backgroundColor": "#12344b", "color": "white"},
    }

    deck_map = pdk.Deck(
        initial_view_state = view_state,
        layers = [layer],
        tooltip = tooltip
    )

    st.pydeck_chart(deck_map)

# Main App

def main():
    col1, col2 = st.columns([1,6])

    with col1:
        st.image("LEGO_logo.png", width=90)

    with col2:
        st.title("LEGO Store Explorer")

    st.markdown(
        "<div class = 'story-box'> This website shows where LEGO stores are located in the USA and Canada. Use the filters to explore patterns by Country, State/Province, and City! </div>",
        unsafe_allow_html = True
    )

    df = read_data()
    df = clean_data(df)

    if df.empty:
        st.warning("The dataset could not be found")
        return

    # [PY5] Dictionary
    country_names = {
        "USA": "United States",
        "CAN": "Canada",
    }

    st.sidebar.header("Choose Your Filters")

    country_list = get_all_countries(df)

    # [ST1]
    selected_country = st.sidebar.selectbox("Select a Country", country_list)

    state_list = get_states_by_country(df, selected_country)

    # [ST2]
    selected_states = st.sidebar.multiselect("Select States/Provinces", state_list, default=state_list)

    # [ST3]
    city_name = st.sidebar.text_input("Search for a City")

    top_n = st.sidebar.slider("Top Number of Cities", 3, 15, 10)

    filtered_df = filter_data(selected_country, selected_states, city_name)

    if len(filtered_df) == 0:
        st.warning("No stores match your filters.")
        return

    # [DA9] Add new columns
    filtered_df["Store Count Value"] = 1
    filtered_df["City State"] = filtered_df["City"] + " " + filtered_df["State"]

    # [PY4] List comprehension
    city_examples = [city for city in filtered_df["City"].unique()]

    total_stores, total_states, total_cities, total_countries = get_summary(filtered_df)
    top_state, top_state_count, top_city, top_city_count = get_top_state_and_city(filtered_df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Stores", total_stores)
    c2.metric("States/Provinces", total_states)
    c3.metric("Cities", total_cities)
    c4.metric("Countries", total_countries)

    st.markdown(
        f"<p class= 'small-text'>Current country: <b> {country_names[selected_country]} </b>. Top State/Province: <b> {top_state}</b> ({top_state_count} stores. Top City: <b>{top_city}</b> ({top_city_count} stores.)</p>",
        unsafe_allow_html = True
    )

    tabs = st.tabs(["Overview", "Charts", "Table", "Map"])

    with tabs[0]:
        st.subheader("Project Story")

        st.write("This project shows how LEGO stores are distributed across geographic regions. Some places have more store concentration than others, which becomes easier to see after applying filters.")
        st.write("Example cities from the current filter: "+", ".join(city_examples[:10]))

        # [DA7] Group/Select columns
        grouped_df = filtered_df.groupby(["State", "City"])["Store Name"].count().reset_index()
        grouped_df.columns = ["State", "City", "Store Count"]
        st.subheader("Grouped Summary")
        st.dataframe(grouped_df, use_container_width = True)

    with tabs[1]:
        st.subheader("Charts")

        chosen_states = sorted(filtered_df["State"].unique())
        state_counts = count_states(chosen_states, filtered_df)

        city_count_df = filtered_df.groupby("City")["Store Name"].count().reset_index()
        city_count_df.columns = ["City", "Store Count"]
        city_count_df = city_count_df.sort_values(by="Store Count", ascending=False).head(top_n)

        country_count_df = df.groupby("Country")["Store Name"].count().reset_index()
        country_count_df.columns = ["Country", "Store Count"]

        st.write("This chart compares how many stores are in each selected state or province.")
        st.pyplot(generate_bar_chart(chosen_states, state_counts, "Stores by State/Province", "State/Province","Number of Stores"), width="content")

        st.write("This chart highlights the cities with the most LEGO stores in the current filter.")
        st.pyplot(generate_bar_chart(city_count_df["City"], city_count_df["Store Count"], "Top Cities", "City","Number of Stores", "orange"), width="content")

        st.write("This pie chart shows each country’s share of stores in the full dataset.")
        st.pyplot(generate_pie_chart(country_count_df["Store Count"].tolist(), country_count_df["Country"].tolist(),"Store Share by Country"), width="content")

        # [DA3] Top values
        st.write("The city with the most stores in the current filter is", top_city, "with", top_city_count, "stores.")

    with tabs[2]:
        st.subheader("Filtered store table")

        # [DA2] Sort data
        sorted_table = filtered_df[["Store Name", "Phone", "City", "State", "Zip", "Country", "Full Address"]]
        sorted_table = sorted_table.sort_values(by=["State", "City"], ascending=True)

        st.dataframe(sorted_table, use_container_width=True)

        # [DA6] Pivot table
        st.subheader("Pivot Table")
        st.dataframe(make_pivot_table(filtered_df), use_container_width=True)

    with tabs[3]:
        st.subheader("Interactive Map")
        st.write("The map uses latitude and longitude from the dataset. Hover over points to see store details.")
        generate_map(filtered_df)

        st.subheader("Sample Store Sentences")

        # [DA8] iterrows()
        for index, row in filtered_df.head(5).iterrows():
            st.write(row["Store Name"], "is located in", row["City"] + ",", row["State"])


main()