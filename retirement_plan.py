import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Sidebar Inputs
st.sidebar.title("Retirement Plan")

# User Inputs
age = st.sidebar.number_input("Your Current Age", min_value=18, max_value=100, value=30, step=1)
preretirement_start_age = st.sidebar.number_input("Start of Preretirement Phase (Age)", min_value=40, max_value=100, value=55, step=1)
retirement_age = st.sidebar.number_input("Desired Retirement Age", min_value=50, max_value=100, value=60, step=1)
life_expectancy = st.sidebar.number_input("Life Expectancy", min_value=60, max_value=120, value=85, step=1)

# Financial Inputs
current_savings = st.sidebar.number_input("Current Savings (in your currency)", min_value=0.0, step=100.0, value=100000.0)
monthly_savings = st.sidebar.number_input("Monthly Contribution to Savings", min_value=0.0, step=100.0, value=500.0)
accumulation_return = st.sidebar.slider("Accumulation Phase Return Rate (%)", min_value=0.0, max_value=15.0, value=7.0)
preretirement_return = st.sidebar.slider("Preretirement Phase Return Rate (%)", min_value=0.0, max_value=15.0, value=5.0)
post_retirement_return = st.sidebar.slider("Retirement Phase Return Rate (%)", min_value=0.0, max_value=10.0, value=3.0)
inflation_rate = st.sidebar.slider("Expected Inflation Rate (%)", min_value=0.0, max_value=10.0, value=2.5)

# Expense Inputs
current_need_expenses = st.sidebar.number_input("Current Monthly Need Expenses", min_value=0.0, step=100.0, value=1500.0)
current_want_expenses = st.sidebar.number_input("Current Monthly Want Expenses", min_value=0.0, step=100.0, value=500.0)

# Adjust for Inflation
future_need_expenses = current_need_expenses * ((1 + inflation_rate / 100) ** (retirement_age - age))
future_want_expenses = current_want_expenses * ((1 + inflation_rate / 100) ** (retirement_age - age))
future_monthly_expenses = future_need_expenses + future_want_expenses

# Helper Functions
def calculate_phase_balance(start_balance, monthly_contrib, rate, years):
    rate = rate / 100 / 12  # Convert annual rate to monthly
    months = years * 12
    for month in range(round(months)):
        start_balance = start_balance * (1 + rate) + monthly_contrib
    
    return start_balance

def calculate_cumulative_balance(start_balance, monthly_contrib, rate, years):
    rate = rate / 100 / 12  # Convert annual rate to monthly
    months = years * 12
    balance = start_balance
    cumulative_balance = []
    for month in range(months):
        balance = balance * (1 + rate) + monthly_contrib
        cumulative_balance.append(balance)
    # return balance at the end of each year
    print(len(cumulative_balance))
    return cumulative_balance

def simulate_withdrawals(start_balance, monthly_expenses, post_retirement_rate, inflation_rate, years):
    annual_rate = post_retirement_rate / 100
    inflation_rate = inflation_rate / 100
    balances = []
    cumulative_expenses = []
    total_expenses = 0

    for year in range(years):
        annual_expenses = monthly_expenses * 12
        start_balance = start_balance * (1 + annual_rate) - annual_expenses
        total_expenses += annual_expenses
        balances.append(max(start_balance, 0))
        cumulative_expenses.append(total_expenses)

        # Adjust expenses for inflation
        monthly_expenses *= (1 + inflation_rate)

        if start_balance <= 0:
            break
    return balances, cumulative_expenses

# Phase Calculations
accumulation_years = max(preretirement_start_age - age, 0)
preretirement_years = max(retirement_age - preretirement_start_age, 0)
retirement_years = max(life_expectancy - retirement_age, 0)

# Accumulation Phase
accumulation_balance = calculate_phase_balance(current_savings, monthly_savings, accumulation_return, accumulation_years)

# Preretirement Phase
preretirement_balance = calculate_phase_balance(accumulation_balance, monthly_savings, preretirement_return, preretirement_years)

# Retirement Phase
retirement_balances, cumulative_expenses = simulate_withdrawals(
    preretirement_balance, future_monthly_expenses, post_retirement_return, inflation_rate, retirement_years
)

# Combine Data
total_years = range(age, life_expectancy + 1)
balance_data = {year: None for year in total_years}

# Fill balances for each phase
current_balance = current_savings
for year in range(age, preretirement_start_age):
    current_balance = calculate_phase_balance(current_balance, monthly_savings, accumulation_return, 1) 
    balance_data[year] = current_balance
    print(current_balance)
    print()
    

for year in range(preretirement_start_age, retirement_age):
    current_balance = calculate_phase_balance(current_balance, monthly_savings, preretirement_return, 1)
    balance_data[year] = current_balance

retirement_years_range = range(retirement_age, retirement_age + len(retirement_balances))
for i, year in enumerate(retirement_years_range):
    balance_data[year] = retirement_balances[i]

# Convert to DataFrame
balance_df = pd.DataFrame.from_dict(balance_data, orient='index', columns=["Balance"])
balance_df["Cumulative Expenses"] = [None] * len(balance_df)
for i, year in enumerate(range(retirement_age, retirement_age + len(cumulative_expenses))):
    balance_df.at[year, "Cumulative Expenses"] = cumulative_expenses[i]

# Visualization
st.title("Retirement Plan Overview")

st.subheader("Retirement Balance and Cumulative Expenses")
if not balance_df.empty:
    fig = go.Figure()

    # Plot Balance
    fig.add_trace(go.Scatter(
        x=balance_df.index,
        y=balance_df["Balance"],
        mode='lines',
        name="Retirement Balance",
        line=dict(color='blue')
    ))

    # Plot Cumulative Expenses
    fig.add_trace(go.Scatter(
        x=balance_df.index,
        y=balance_df["Cumulative Expenses"],
        mode='lines',
        name="Cumulative Expenses",
        line=dict(color='red')
    ))

    # Vertical lines for phases
    fig.add_vline(x=preretirement_start_age, line_dash="dash", line_color="orange", annotation_text="Preretirement Start Age")
    fig.add_vline(x=retirement_age, line_dash="dash", line_color="green", annotation_text="Retirement Age")
    fig.add_vline(x=life_expectancy, line_dash="dash", line_color="purple", annotation_text="End of Life Expectancy")

    # Update layout
    fig.update_layout(
        title="Retirement Plan Overview",
        xaxis_title="Age",
        yaxis_title="Amount",
        legend=dict(x=0, y=1),
        template="plotly_white"
    )

    # Show the figure in Streamlit
    st.plotly_chart(fig)

    # Check if funds last
    if retirement_balances and retirement_balances[-1] > 0:
        st.success("Your savings will last through retirement!")
    else:
        st.error("Your savings may run out during retirement. Consider saving more or reducing expenses.")
else:
    st.error("Your savings will not last into retirement based on the current plan.")

# Expense Breakdown
st.subheader("Expense Breakdown")
st.metric("Future Monthly Need Expenses", f"{future_need_expenses:,.2f}")
st.metric("Future Monthly Want Expenses", f"{future_want_expenses:,.2f}")

# Detailed Plan
st.subheader("Details of Your Plan")
st.write(f"- **Current Age**: {age}")
st.write(f"- **Preretirement Start Age**: {preretirement_start_age}")
st.write(f"- **Retirement Age**: {retirement_age}")
st.write(f"- **Life Expectancy**: {life_expectancy}")
st.write(f"- **Accumulation Phase Return Rate**: {accumulation_return}%")
st.write(f"- **Preretirement Phase Return Rate**: {preretirement_return}%")
st.write(f"- **Retirement Phase Return Rate**: {post_retirement_return}%")
st.write(f"- **Expected Inflation Rate**: {inflation_rate}%")
st.write(f"- **Current Need Expenses**: {current_need_expenses:,.2f}")
st.write(f"- **Current Want Expenses**: {current_want_expenses:,.2f}")
st.write(f"- **Projected Monthly Expenses at Retirement**: {future_monthly_expenses:,.2f}")
