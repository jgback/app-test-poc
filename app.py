import streamlit as st

st.title("Healthcare Cost Estimator POC")

procedure = st.selectbox("Select a Procedure", ["MRI", "CT Scan", "Knee Surgery", "X-ray"])
zip_code = st.text_input("Enter ZIP Code", "")

if st.button("Estimate Cost"):
    cost_estimates = {
        "MRI": "$1,000 - $3,000",
        "CT Scan": "$800 - $2,500",
        "Knee Surgery": "$15,000 - $35,000",
        "X-ray": "$100 - $500"
    }
    st.write(f"Estimated cost for **{procedure}** in ZIP **{zip_code}**: {cost_estimates.get(procedure, 'No data available')}")

st.write("🚀 This is a proof of concept for a healthcare cost estimator!")