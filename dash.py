import requests
import pandas as pd 
import streamlit as st
import plotly.express as px

url = "https://steamspy.com/api.php?request=top100in2weeks"

resposta = requests.get(url)
dados = resposta.json()

df= pd.DataFrame.from_dict(dados, orient='index')

st.title("Dashboard jogos Steam")

st.dataframe(df.head(100))