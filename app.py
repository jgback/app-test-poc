import openai
import streamlit as st
import pandas as pd

# Load API Key from Streamlit Secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Set page layout to ensure sidebar is visible
st.set_page_config(layout="wide", initial_sidebar_state="expanded")

# Load cost data
@st.cache_data
def load_cost_data():
    return pd.read_csv("cost_data.csv", dtype={"ZIP Code": str})

# Load insurance plan data
@st.cache_data
def load_insurance_plans():
    return pd.read_csv("insurance_plans.csv")

df = load_cost_data()
insurance_df = load_insurance_plans()

# Streamlit UI - App Title
st.title("Healthcare Cost Estimator")

# User selects a procedure
procedure = st.selectbox("Select a Procedure", df["Procedure"].unique())

# User enters ZIP code
zip_code = st.text_input("Enter ZIP Code", "")

# Sidebar: Insurance Plan Selection
st.sidebar.header("Select Insurance Plan")
selected_plan = st.sidebar.selectbox("Choose a Plan", insurance_df["Plan Name"].unique())

# Get the selected plan details
plan_details = insurance_df[insurance_df["Plan Name"] == selected_plan].iloc[0]

# Auto-fill insurance details
deductible_total = plan_details["Total Deductible"]
deductible_remaining = plan_details["Remaining Deductible"]
co_pay = plan_details["Co-Pay (%)"] / 100
co_insurance = plan_details["Co-Insurance (%)"] / 100
out_of_pocket_max = plan_details["Out-of-Pocket Max"]

# Display selected plan details in sidebar
st.sidebar.write(f"**Total Deductible:** ${deductible_total}")
st.sidebar.write(f"**Remaining Deductible:** ${deductible_remaining}")
st.sidebar.write(f"**Co-Pay:** {plan_details['Co-Pay (%)']}%")
st.sidebar.write(f"**Co-Insurance:** {plan_details['Co-Insurance (%)']}%")
st.sidebar.write(f"**Out-of-Pocket Max:** ${out_of_pocket_max}")

# Filter cost data
filtered_df = df[(df["Procedure"] == procedure) & (df["ZIP Code"] == zip_code)]

if st.button("Estimate Cost"):
    if not filtered_df.empty:
        provider_fee = filtered_df["Provider Fee"].values[0]
        facility_fee = filtered_df["Facility Fee"].values[0]
        imaging_fee = filtered_df["Imaging Fee"].values[0]
        anesthesia_fee = filtered_df["Anesthesia Fee"].values[0]
        total_cost = filtered_df["Total Estimated Cost"].values[0]

        # Step 1: Apply Deductible to Each Component
        remaining_deductible = deductible_remaining  # Initialize deductible

        def apply_deductible(cost, remaining_deductible):
            """Deducts from the remaining deductible and returns the updated deductible value."""
            if remaining_deductible > cost:
                amount_applied = cost
                remaining_deductible -= cost
                return amount_applied, 0, remaining_deductible
            else:
                amount_applied = remaining_deductible
                remaining_to_pay = cost - amount_applied
                remaining_deductible = 0
                return amount_applied, remaining_to_pay, remaining_deductible

        # Apply deductible to each cost component
        provider_deductible, provider_remaining, remaining_deductible = apply_deductible(provider_fee, remaining_deductible)
        facility_deductible, facility_remaining, remaining_deductible = apply_deductible(facility_fee, remaining_deductible)
        imaging_deductible, imaging_remaining, remaining_deductible = apply_deductible(imaging_fee, remaining_deductible)
        anesthesia_deductible, anesthesia_remaining, remaining_deductible = apply_deductible(anesthesia_fee, remaining_deductible)

        # Step 2: Apply Co-Pay & Co-Insurance to Remaining Costs
        def calculate_insurance_coverage(remaining_cost):
            covered = remaining_cost * (co_pay + co_insurance)
            return covered, remaining_cost - covered  # Returns (insurance coverage, patient out-of-pocket)

        provider_covered, provider_out_of_pocket = calculate_insurance_coverage(provider_remaining)
        facility_covered, facility_out_of_pocket = calculate_insurance_coverage(facility_remaining)
        imaging_covered, imaging_out_of_pocket = calculate_insurance_coverage(imaging_remaining)
        anesthesia_covered, anesthesia_out_of_pocket = calculate_insurance_coverage(anesthesia_remaining)

        # Step 3: Calculate Totals
        total_applied_to_deductible = provider_deductible + facility_deductible + imaging_deductible + anesthesia_deductible
        total_covered_by_insurance = provider_covered + facility_covered + imaging_covered + anesthesia_covered
        total_out_of_pocket = provider_out_of_pocket + facility_out_of_pocket + imaging_out_of_pocket + anesthesia_out_of_pocket
        total_out_of_pocket = min(total_out_of_pocket, out_of_pocket_max)  # Ensure user doesn't exceed out-of-pocket max

        # Display Cost Breakdown Table
        breakdown_df = pd.DataFrame({
            "Category": ["Provider Fee", "Facility Fee", "Imaging Fee", "Anesthesia Fee", "Total"],
            "Cost": [provider_fee, facility_fee, imaging_fee, anesthesia_fee, total_cost],
            "Applied to Deductible": [provider_deductible, facility_deductible, imaging_deductible, anesthesia_deductible, total_applied_to_deductible],
            "Covered by Insurance": [provider_covered, facility_covered, imaging_covered, anesthesia_covered, total_covered_by_insurance],
            "Out-of-Pocket": [provider_out_of_pocket, facility_out_of_pocket, imaging_out_of_pocket, anesthesia_out_of_pocket, total_out_of_pocket]
        })

        st.write("### Cost Breakdown Per Category:")
        st.dataframe(breakdown_df.style.format({"Cost": "${:,.2f}", 
                                                "Applied to Deductible": "${:,.2f}", 
                                                "Covered by Insurance": "${:,.2f}", 
                                                "Out-of-Pocket": "${:,.2f}"}))

        # Summary Results
        st.write(f"**Total Estimated Cost:** :moneybag: **${total_cost:,.2f}**")

# Load OpenAI API key from Streamlit Secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

def ask_gpt(prompt):
    """Send a question to OpenAI's GPT and return the response."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are an assistant that provides cost breakdowns and insurance coverage explanations for healthcare procedures."},
                      {"role": "user", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ Error: {e}"
    
st.write("🚀 This is an early proof of concept for a healthcare cost estimator!")

st.write("### 🤖 Ask the AI About Your Healthcare Costs!")
user_question = st.chat_input("Ask a question about procedure costs, insurance coverage, or savings...")

if user_question:
    with st.chat_message("user"):
        st.write(user_question)

    response = ask_gpt(user_question)

    with st.chat_message("assistant"):
        st.write(response)