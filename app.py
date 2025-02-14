import openai
import streamlit as st
import pandas as pd

# Load API Key from Streamlit Secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- Load Data Functions ---
@st.cache_data
def load_cost_data():
    return pd.read_csv("cost_data.csv", dtype={"ZIP Code": str})

@st.cache_data
def load_insurance_plans():
    return pd.read_csv("insurance_plans.csv")

# --- Load Data ---
df = load_cost_data()
insurance_df = load_insurance_plans()

# --- Ensure Default Values Exist Before Button Click ---
provider_fee = 0
facility_fee = 0
imaging_fee = 0
anesthesia_fee = 0
total_cost = 0
total_out_of_pocket = 0
total_covered_by_insurance = 0

provider_deductible = 0
facility_deductible = 0
imaging_deductible = 0
anesthesia_deductible = 0

provider_covered = 0
facility_covered = 0
imaging_covered = 0
anesthesia_covered = 0

provider_out_of_pocket = 0
facility_out_of_pocket = 0
imaging_out_of_pocket = 0
anesthesia_out_of_pocket = 0

# --- Define OpenAI Chat Function ---
def ask_gpt(prompt, procedure, zip_code, total_cost, out_of_pocket_cost, insurance_covered):
    """Send a question to OpenAI's GPT with context about procedure costs and insurance coverage."""
    try:
        client = openai.OpenAI()

        context = f"""
        You are a helpful assistant that provides cost breakdowns and insurance coverage details for healthcare procedures.
        Here is the user's data:
        - Procedure: {procedure}
        - ZIP Code: {zip_code}
        - Total Estimated Cost: ${total_cost:,.2f}
        - Out-of-Pocket Cost (User Pays): ${out_of_pocket_cost:,.2f}
        - Covered by Insurance: ${insurance_covered:,.2f}

        Use this information to answer the user's question.
        """

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error: {e}"

# --- Streamlit UI ---
st.title("Healthcare Cost Estimator")

# --- User Input: Procedure and ZIP Code ---
procedure = st.selectbox("Select a Procedure", df["Procedure"].unique())
zip_code = st.text_input("Enter ZIP Code", "")

# --- Sidebar: Insurance Plan Selection ---
st.sidebar.header("Select Insurance Plan")
selected_plan = st.sidebar.selectbox("Choose a Plan", insurance_df["Plan Name"].unique())

# --- Get Selected Plan Details ---
plan_details = insurance_df[insurance_df["Plan Name"] == selected_plan].iloc[0]

# --- Extract Insurance Information ---
deductible_total = plan_details["Total Deductible"]
deductible_remaining = plan_details["Remaining Deductible"]
co_pay = plan_details["Co-Pay (%)"] / 100
co_insurance = plan_details["Co-Insurance (%)"] / 100
out_of_pocket_max = plan_details["Out-of-Pocket Max"]

# --- Display Insurance Plan Details in Sidebar ---
st.sidebar.write(f"**Total Deductible:** ${deductible_total}")
st.sidebar.write(f"**Remaining Deductible:** ${deductible_remaining}")
st.sidebar.write(f"**Co-Pay:** {plan_details['Co-Pay (%)']}%")
st.sidebar.write(f"**Co-Insurance:** {plan_details['Co-Insurance (%)']}%")
st.sidebar.write(f"**Out-of-Pocket Max:** ${out_of_pocket_max}")

# --- Filter Cost Data Based on User Input ---
filtered_df = df[(df["Procedure"] == procedure) & (df["ZIP Code"] == zip_code)]

# --- Cost Estimation Section ---
if st.button("Estimate Cost"):
    if not filtered_df.empty:
        # ✅ Get actual cost data from CSV
        provider_fee = filtered_df["Provider Fee"].values[0]
        facility_fee = filtered_df["Facility Fee"].values[0]
        imaging_fee = filtered_df["Imaging Fee"].values[0]
        anesthesia_fee = filtered_df["Anesthesia Fee"].values[0]
        total_cost = filtered_df["Total Estimated Cost"].values[0]

        # 🔹 Perform deductible & insurance calculations here...
        total_out_of_pocket = total_cost * 0.2  # Placeholder Calculation
        total_covered_by_insurance = total_cost - total_out_of_pocket

        # --- Display Cost Breakdown Table ---
        breakdown_df = pd.DataFrame({
            "Category": ["Provider Fee", "Facility Fee", "Imaging Fee", "Anesthesia Fee", "Total"],
            "Cost": [provider_fee, facility_fee, imaging_fee, anesthesia_fee, total_cost],
            "Covered by Insurance": [provider_covered, facility_covered, imaging_covered, anesthesia_covered, total_covered_by_insurance],
            "Out-of-Pocket": [provider_out_of_pocket, facility_out_of_pocket, imaging_out_of_pocket, anesthesia_out_of_pocket, total_out_of_pocket]
        })

        st.write("### Cost Breakdown Per Category:")
        st.dataframe(breakdown_df.style.format({
            "Cost": "${:,.2f}",
            "Covered by Insurance": "${:,.2f}",
            "Out-of-Pocket": "${:,.2f}"
        }))

        # --- Display Summary ---
        st.write(f"**Total Estimated Cost:** :moneybag: **${total_cost:,.2f}**")

# --- Chatbot Section ---
st.write("### 🤖 Ask the AI About Your Healthcare Costs!")

user_question = st.chat_input("Ask a question about procedure costs, insurance coverage, or savings...")

if user_question:
    with st.chat_message("user"):
        st.write(user_question)

    if not filtered_df.empty:
        response = ask_gpt(user_question, procedure, zip_code, total_cost, total_out_of_pocket, total_covered_by_insurance)

        with st.chat_message("assistant"):
            st.write(response)
    else:
        with st.chat_message("assistant"):
            st.write("⚠️ No cost data found for the selected procedure and ZIP code.")
