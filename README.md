# Project Work, Part 1 - Dashboard Basics
## 1. Introduction
This project involves analyzing data in a Jupyter Notebook and creating a multi-page online app with Streamlit, with all work and code shared on GitHub. AI tools (e.g., ChatGPT) were utilized during the project to clarify requirements and to gain a deeper understanding of the technologies used.

## 2. App Links

Streamlit app: https://ind320-k2r8aymxk9takanegm8e3y.streamlit.app

## 3. Project Log
Before starting the actual task, I created a public repository on GitHub and signed up for a Streamlit account. Since we had to work with weather data, I found it straightforward to load the data into a DataFrame, but plotting different columns together required some extra research. Using Jupyter Notebook allowed me to quickly prototype and visualize the data, and the built-in markdown functionality helped me document my process step by step.

Building the Streamlit app was a completely new experience for me. I followed the lecture materials, read online articles, and checked my progress with the TA during lab sessions. By following the instructions to create a minimum working example, I set up four pages with dummy headers and implemented a sidebar menu for navigation. My biggest challenge was understanding the layout system in Streamlit and connecting it properly to GitHub. However, the Streamlit documentation was clear, and after some trial and error, I managed to display the data table and set up navigation as required.

Additionally, I committed my code to GitHub regularly, writing clear commit messages each time I worked on the project. This helped me keep track of my progress and made it easier to revisit or undo changes when needed.

Throughout the project, I used an AI assistant (ChatGPT) for guidance on certain coding tasks and to review my markdown documentation. This was particularly helpful when I got stuck with some plotting functions in Plotly and needed to find best practices for presenting data on a Streamlit app.

Overall, I feel more confident using Jupyter,GitHub, and Streamlit. And I successfully implemented and tested the project part-1 as requested.

# Project Work, Part 2 - Data Source
## 1. Introduction
This project visualizes hourly energy production data across Norwegian price areas using Spark, Cassandra, MongoDB, Interactive Jupyter Notebook, and Streamlit dashboards. AI tools (e.g., ChatGPT) were utilized during the project to clarify requirements and to gain a deeper understanding of the technologies used.

## 2. App Links

Streamlit app: https://ind320-k2r8aymxk9takanegm8e3y.streamlit.app

### 2. AI Usage Description
In this project, AI (ChatGPT) was used as a supportive tool to help with coding, data handling, visualization, and project structuring. The AI assisted in debugging Spark-Cassandra connections, converting Pandas DataFrames to Spark DataFrames, designing interactive Streamlit dashboards, and generating Plotly charts. Additionally, the AI provided guidance on best practices for managing MongoDB connections, structuring Streamlit pages, and organizing project files. All suggestions from the AI were reviewed and adapted before use in the project.

### 3. Project Log
For the compulsory work, I first established a local Cassandra database and connected it to Spark using the PySpark connector. I verified the connection by inserting sample data and retrieving it successfully from a Jupyter Notebook. Once the Spark-Cassandra integration was confirmed, I used the Elhub API to fetch hourly production data for 2021 using the PRODUCTION_PER_GROUP_MBA_HOUR dataset. The data was extracted as a list of production events, transformed into a Pandas DataFrame, and inserted into Cassandra using Spark’s DataFrame .write functionality.

After storing the raw data in Cassandra, I used Spark to extract the columns priceArea, productionGroup, startTime, and quantityKwh for further analysis. To visualize energy production, I created two interactive charts in Jupyter Notebook. First, a pie chart showing total annual production per production group for a selected price area. Second, a line plot for the first month of the year with separate lines for each production group, allowing easy comparison of hourly energy production. During this stage, AI assistance helped troubleshoot DataFrame pivoting, handling datetime operations, and resolving Spark-Cassandra integration issues.

Once the data was validated, I curated it and stored the processed dataset in a MongoDB Atlas instance. This step allowed the data to be accessed directly from a Streamlit app. In Streamlit, I set up the secrets for MongoDB, and I structured page four with two columns as requested: the left column contains radio buttons for selecting a price area and displays a corresponding pie chart. The right column allows users to select production groups via multi-select pills and choose a month for the line plot. The charts update dynamically based on user selections. Below the columns, I added an expander with a description of the data source (Elhub API) and processing steps.

The workflow demonstrates the end-to-end processing of energy production data: fetching via API, storing in Cassandra, processing with Spark, and visualizing in Jupyter and Streamlit while maintaining secure access via MongoDB.

# Project Work, Part 3 - Data Quality
## 1. Introduction
This project involves analyzing data in a Jupyter Notebook and creating a multi-page online app with Streamlit, with all work and code shared on GitHub. AI tools (e.g., ChatGPT) were utilized during the project to clarify requirements and to gain a deeper understanding of the technologies used.

- Task: Analysis of Norwegian electricity production (Elhub) and meteorological data (Open‑Meteo API).
- Goal: automate data collection, perform time‑series decomposition, periodic analysis, and anomaly detection; then visualize results in a Jupyter Notebook and Streamlit dashboard.

## 2. App Links

Streamlit app: https://ind320-k2r8aymxk9takanegm8e3y.streamlit.app

## 3. Project Overview
### 3.1 AI Usage Description
In this project, I used AI (ChatGPT) as a helpful assistant during development. It supported me in solving coding errors, generating code ideas, and improving my understanding of concepts. The AI explained topics such as STL decomposition, Discrete Cosine Transform (DCT) filtering, and Local Outlier Factor (LOF) anomaly detection, giving both theory and example code.

I also used it to debug Python and Streamlit issues, like fixing empty DataFrames, using st.session_state, avoiding runtime errors, and organizing the multi-page layout. During implementation, I followed AI suggestions to clean up functions, set better parameter defaults, and make the visualizations easier to read.

All AI outputs were carefully checked, tested, and modified to fit the project’s goals and my own coding style. Overall, the AI acted as a learning and support tool, helping me work faster and understand data analysis and software design more deeply.

### 3.2 Project Log
For the compulsory work, I began by defining representative cities for Norway’s five electricity price areas (NO1–NO5) and storing their latitude and longitude in a Pandas DataFrame. This mapping created the geographic foundation for the rest of the analyses. I then downloaded hourly electricity production data from the Elhub API for 2021, focusing on the *PRODUCTION_PER_GROUP_MBA_HOUR* dataset. The raw *JSON* responses were normalized into a clean DataFrame.

Next, I replaced my earlier CSV‑based meteorological import with live calls to the Open‑Meteo API. For each selected price area, the application automatically queries the API using the corresponding city’s coordinates, returning hourly temperature, precipitation, and wind observations for 2019 in a Notebook file and 2021 for the Streamlit app. The fetched data are transformed into a tidy format in a Pandas DataFrame and cached for efficient reuse.

Analytical development was divided into three main components, implemented and tested first in a Jupyter Notebook.
- Seasonal‑Trend decomposition using LOESS (STL): using the *statsmodels.tsa.seasonal.STL* class, I decomposed the production time series into trend, seasonal, and residual components.
- Spectrogram analysis: applying *scipy.signal.spectrogram*, I generated time–frequency plots to reveal changes in periodic behavior across the year.
- Outlier and Anomaly detection: I implemented a robust Statistical Process Control (SPC) method using *Median ± k × MAD* boundaries on filtered temperature data and applied the Local Outlier Factor (LOF) algorithm from *scikit‑learn* to identify precipitation anomalies.
Each analytical block was wrapped in a modular Python function with configurable parameters (area, group, window length, etc.) and tested interactively in the notebook before integration into the Streamlit app.

I then updated the Streamlit dashboard to follow the new required page order. The global area selector was moved to the second page (named *Energy Production(4)* in the app), ensuring that all subsequent analyses depend on the user’s chosen region. Between existing pages, I added *new A (STL and Spectrogram(A))* and *new B (Outliers and Anomalies (B))* pages, each built with *st.tabs()* for navigation. Both pages render Matplotlib plots directly and display them. Communication between pages is managed through *st.session_state*, allowing the selected price area imported meteorological data and production data to persist throughout the session.

The completed workflow demonstrates a full data pipeline: acquiring data dynamically via APIs, performing time‑series analysis, detecting anomalies, and presenting interactive results through a structured Streamlit interface and Jupyter Notebook.