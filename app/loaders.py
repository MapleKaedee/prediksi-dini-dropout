"""Pemuatan artefak dengan cache Streamlit (APP-03). Logika pemuatannya ada di core.py."""

import core
import streamlit as st


@st.cache_data(show_spinner=False)
def json_file(name):
    return core.load_json(name)


@st.cache_data(show_spinner=False)
def test_rows():
    return core.load_test_rows()


@st.cache_data(show_spinner=False)
def priority(model):
    return core.priority_table(json_file("test_predictions.json"), model)


@st.cache_resource(show_spinner="Memuat model...")
def model(model_id):
    return core.load_model(model_id)


@st.cache_resource(show_spinner="Menyiapkan penjelasan SHAP...")
def explainer(model_id):
    return core.make_explainer(model(model_id))
