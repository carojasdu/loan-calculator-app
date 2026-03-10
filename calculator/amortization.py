"""
Amortization schedule generator for French amortization (cuota fija).

No Streamlit or UI imports.
"""


import pandas as pd


def build_schedule(
    loan: float,
    monthly_rate: float,
    payment: float,
    n_months: int,
    monthly_rental: float = 0.0,
) -> pd.DataFrame:
    """Generate the full amortization schedule row by row.

    Args:
        loan: Principal amount at t=0
        monthly_rate: Monthly effective rate as a decimal
        payment: Fixed monthly payment amount
        n_months: Total number of payments
        monthly_rental: Monthly rental income (used for net cost column); default 0

    Returns:
        DataFrame with columns:
            month                      int   — payment number (1..n_months)
            remaining_principal        float — principal balance after this payment
            interest_this_month        float — interest portion of this payment
            principal_this_month       float — principal portion of this payment
            cumulative_interest        float — total interest paid up to this month
            cumulative_principal       float — total principal paid up to this month
            net_cumulative_cost        float — cumulative_interest minus total rental received
    """
    rows = []
    balance = loan
    cum_interest = 0.0
    cum_principal = 0.0

    for month in range(1, n_months + 1):
        interest = balance * monthly_rate
        principal = payment - interest

        # Guard against floating-point overshoot on the last payment
        if principal > balance:
            principal = balance
        balance -= principal

        # Clamp residual floating-point error on the final row
        if month == n_months:
            balance = 0.0

        cum_interest += interest
        cum_principal += principal
        rental_received = monthly_rental * month

        rows.append(
            {
                "month": month,
                "remaining_principal": balance,
                "interest_this_month": interest,
                "principal_this_month": principal,
                "cumulative_interest": cum_interest,
                "cumulative_principal": cum_principal,
                "net_cumulative_cost": cum_interest - rental_received,
            }
        )

    return pd.DataFrame(rows)
