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