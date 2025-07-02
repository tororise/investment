import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Define the investment calculation function (from previous turn)
def calculate_investment_growth(
    one_time_investment,
    monthly_sip_amount,
    annual_interest_rate_percent,
    sip_duration_years,
    total_investment_duration_years
):
    """
    Simulates investment growth based on a one-time investment and monthly SIP.

    Args:
        one_time_investment (float): The initial lump sum investment.
        monthly_sip_amount (float): The amount invested monthly via SIP.
        annual_interest_rate_percent (float): Annual interest rate (e.g., 8 for 8%).
        sip_duration_years (int): Duration for which monthly SIPs are made (e.g., 10 years).
        total_investment_duration_years (int): Total period the money remains invested
                                               (e.g., 20 years).

    Returns:
        dict: A dictionary containing details of the investment simulation.
    """

    if not all(isinstance(arg, (int, float)) and arg >= 0 for arg in [
        one_time_investment, monthly_sip_amount, annual_interest_rate_percent,
        sip_duration_years, total_investment_duration_years
    ]):
        st.error("All investment amounts, rates, and durations must be non-negative numbers.")
        return None

    if total_investment_duration_years < sip_duration_years:
        st.error("Total investment duration must be greater than or equal to SIP duration.")
        return None

    # Convert annual percentage rate to a decimal monthly rate
    monthly_interest_rate = (annual_interest_rate_percent / 100) / 12
    annual_interest_rate = annual_interest_rate_percent / 100

    results = {
        'initial_one_time_investment': one_time_investment,
        'monthly_sip_amount': monthly_sip_amount,
        'annual_interest_rate_percent': annual_interest_rate_percent,
        'sip_duration_years': sip_duration_years,
        'total_investment_duration_years': total_investment_duration_years,
        'total_contributed': 0,
        'final_value': 0,
        'growth_over_time': [] # To store values for plotting
    }

    # --- 1. Calculate growth of One-Time Investment ---
    # This grows for the entire total_investment_duration_years
    final_value_one_time = one_time_investment * ((1 + annual_interest_rate) ** total_investment_duration_years)
    results['final_value_one_time_investment'] = round(final_value_one_time, 2)
    results['total_contributed'] += one_time_investment

    # --- 2. Calculate growth of Monthly SIP ---
    final_value_sip_at_sip_end = 0
    if monthly_sip_amount > 0:
        # Calculate the future value of the annuity at the end of the SIP duration
        num_sip_months = sip_duration_years * 12
        if monthly_interest_rate > 0:
            final_value_sip_at_sip_end = monthly_sip_amount * (((1 + monthly_interest_rate)**num_sip_months - 1) / monthly_interest_rate)
        else: # Handle zero interest rate for SIP
             final_value_sip_at_sip_end = monthly_sip_amount * num_sip_months

        results['total_contributed_sip'] = monthly_sip_amount * num_sip_months
        results['total_contributed'] += results['total_contributed_sip']
        results['value_of_sip_at_sip_end'] = round(final_value_sip_at_sip_end, 2)

        # The SIP contributions stop after sip_duration_years, but that accumulated sum
        # then continues to grow for the remaining period until total_investment_duration_years
        holding_period_after_sip_end_years = total_investment_duration_years - sip_duration_years
        final_value_sip_after_full_period = final_value_sip_at_sip_end * ((1 + annual_interest_rate) ** holding_period_after_sip_end_years)
        results['final_value_monthly_sip'] = round(final_value_sip_after_full_period, 2)
    else:
        results['total_contributed_sip'] = 0
        results['value_of_sip_at_sip_end'] = 0
        results['final_value_monthly_sip'] = 0

    # --- 3. Total Final Value ---
    results['final_value'] = round(final_value_one_time + results['final_value_monthly_sip'], 2)
    results['total_earnings'] = round(results['final_value'] - results['total_contributed'], 2)

    # --- Data for plotting growth over time ---
    current_one_time_value = one_time_investment
    current_sip_value = 0
    total_value_at_year_end = 0

    for year in range(1, total_investment_duration_years + 1):
        # Calculate one-time investment growth for the current year
        current_one_time_value = one_time_investment * ((1 + annual_interest_rate) ** year)

        # Calculate SIP growth for the current year
        if year <= sip_duration_years:
            # SIP is still ongoing, calculate value of annuity up to this year
            num_sip_months_this_year = year * 12
            if monthly_interest_rate > 0:
                current_sip_value = monthly_sip_amount * (((1 + monthly_interest_rate)**num_sip_months_this_year - 1) / monthly_interest_rate)
            else:
                current_sip_value = monthly_sip_amount * num_sip_months_this_year
        else:
            # SIP has stopped, the accumulated value from sip_duration_years continues to grow
            # We use the 'value_of_sip_at_sip_end' as the principal for the remaining years
            # This logic assumes 'value_of_sip_at_sip_end' is correctly calculated at the end of SIP period
            # and then compounds from that point.
            # For plotting, we need to compound the *final* SIP value from SIP end year to current year
            if sip_duration_years > 0 and results['value_of_sip_at_sip_end'] > 0:
                current_sip_value = results['value_of_sip_at_sip_end'] * ((1 + annual_interest_rate) ** (year - sip_duration_years))
            else:
                current_sip_value = 0 # No SIP or SIP duration is 0

        total_value_at_year_end = current_one_time_value + current_sip_value
        results['growth_over_time'].append({
            'year': year,
            'one_time_value': round(current_one_time_value, 2),
            'sip_value': round(current_sip_value, 2),
            'total_value': round(total_value_at_year_end, 2)
        })

    return results

# --- Streamlit App Layout ---

st.set_page_config(layout="wide", page_title="Investment Simulator")

st.title("💰 Simple Investment Simulator")
st.markdown("""
    Calculate the future value of your investments based on a one-time lump sum and/or monthly SIPs.
    The SIP contributions can stop before the total investment duration ends.
""")

# Input Section
st.sidebar.header("Investment Parameters")

one_time_investment = st.sidebar.number_input(
    "One-Time Investment (₹)",
    min_value=0,
    value=100000,
    step=10000
)

monthly_sip_amount = st.sidebar.number_input(
    "Monthly SIP Amount (₹)",
    min_value=0,
    value=5000,
    step=500
)

annual_interest_rate_percent = st.sidebar.slider(
    "Expected Annual Interest Rate (%)",
    min_value=1.0,
    max_value=30.0,
    value=10.0,
    step=0.5
)

sip_duration_years = st.sidebar.slider(
    "SIP Contribution Period (Years)",
    min_value=0,
    max_value=50,
    value=10
)

total_investment_duration_years = st.sidebar.slider(
    "Total Investment Period (Years)",
    min_value=1,
    max_value=60,
    value=20
)

# Ensure total duration is at least SIP duration
if total_investment_duration_years < sip_duration_years:
    st.sidebar.warning("Total Investment Period cannot be less than SIP Contribution Period. Adjusting Total Investment Period.")
    total_investment_duration_years = sip_duration_years
    st.sidebar.slider(
        "Total Investment Period (Years)",
        min_value=1,
        max_value=60,
        value=total_investment_duration_years,
        key="adjusted_total_duration" # Use a unique key for the adjusted slider
    )


if st.sidebar.button("Calculate Investment"):
    results = calculate_investment_growth(
        one_time_investment,
        monthly_sip_amount,
        annual_interest_rate_percent,
        sip_duration_years,
        total_investment_duration_years
    )

    if results:
        st.subheader("📊 Investment Summary")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label="Total Amount Contributed",
                value=f"₹ {results['total_contributed']:,}"
            )
        with col2:
            st.metric(
                label=f"Final Value after {total_investment_duration_years} Years",
                value=f"₹ {results['final_value']:,}"
            )
        with col3:
            st.metric(
                label="Total Earnings (Profit)",
                value=f"₹ {results['total_earnings']:,}"
            )

        st.markdown("---")

        st.subheader("📈 Detailed Breakdown")
        st.write(f"**One-Time Investment:** ₹ {one_time_investment:,}")
        st.write(f"**Monthly SIP Amount:** ₹ {monthly_sip_amount:,}")
        st.write(f"**Annual Interest Rate:** {annual_interest_rate_percent}%")
        st.write(f"**SIP Contribution Period:** {sip_duration_years} Years")
        st.write(f"**Total Investment Period:** {total_investment_duration_years} Years")

        st.write(f"---")
        st.write(f"**Final Value from One-Time Investment:** ₹ {results['final_value_one_time_investment']:,}")
        if monthly_sip_amount > 0:
            st.write(f"**Total Contributed via SIP:** ₹ {results['total_contributed_sip']:,}")
            st.write(f"**Value of SIP at end of Contribution Period ({sip_duration_years} years):** ₹ {results['value_of_sip_at_sip_end']:,}")
            st.write(f"**Final Value from Monthly SIP (after full {total_investment_duration_years} years):** ₹ {results['final_value_monthly_sip']:,}")

        st.markdown("---")

        st.subheader("Growth Over Time")

        years = [d['year'] for d in results['growth_over_time']]
        total_values = [d['total_value'] for d in results['growth_over_time']]
        one_time_values = [d['one_time_value'] for d in results['growth_over_time']]
        sip_values = [d['sip_value'] for d in results['growth_over_time']]

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(years, total_values, label='Total Investment Value', color='blue', linewidth=2)
        if one_time_investment > 0:
            ax.plot(years, one_time_values, label='One-Time Investment Growth', linestyle='--', color='green')
        if monthly_sip_amount > 0:
            ax.plot(years, sip_values, label='Monthly SIP Growth', linestyle=':', color='orange')

        ax.set_title('Investment Growth Over Time')
        ax.set_xlabel('Years')
        ax.set_ylabel('Value (₹)')
        ax.grid(True)
        ax.legend()
        plt.tight_layout()
        st.pyplot(fig)

        st.markdown("---")
        st.info("Note: Values are rounded to 2 decimal places. Interest is compounded annually for the one-time investment and monthly for SIPs, then the accumulated SIP value is compounded annually for the remaining period.")

