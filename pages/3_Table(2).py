import pandas as pd
import streamlit as st

st.title('Tabular data from the CSV file.')

df = pd.read_csv("open-meteo-subset.csv", encoding='UTF-8')
#df.head()
df["time"] = pd.to_datetime(df["time"], format="%Y-%m-%dT%H:%M")
st.write("1. Head of the given dataset.")
st.write(df.head(3))

st.write("2. Weather Data Summary - First Month with Line Chart Previews")

# the row-wise LineChartColumn() to display the first month of the data series
first_month = df[df["time"].dt.month == df["time"].dt.month.min()]

# DataFrame where: - Each row = a variable (column), - A small timeseries goes in the "chart" column
summary_data = {
    "Variable": [],
    "Preview": []
}

for col in df.columns:
    if col != "time":  # skiping the time column
        summary_data["Variable"].append(col)
        summary_data["Preview"].append(list(first_month[col].values))

summary_df = pd.DataFrame(summary_data)

# Display interactive table with line charts
st.dataframe(
    summary_df,
    column_config={
        "Variable": st.column_config.TextColumn("Variable Name"),
        "Preview": st.column_config.LineChartColumn(
            "First Month Trend",
            y_min=min(summary_df["Preview"][0]),  # auto scale
        )
    },
    hide_index=True
)