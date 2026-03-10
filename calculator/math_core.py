"""
Pure math functions for French amortization (cuota fija).

All rates are decimals (e.g. 0.127 for 12.7%).
All monetary values are in the same currency unit (e.g. COP).
No Streamlit or UI imports.
"""

import math


def monthly_rate_from_ea(annual_rate_ea: float) -> float:
    """Convert annual effective rate (E.A.) to monthly effective rate.

    Args:
        annual_rate_ea: Annual effective rate as a decimal (e.g. 0.127 for 12.7%)

    Returns:
        Monthly effective rate as a decimal.
    """
    if annual_rate_ea <= 0:
        raise ValueError(f"Annual rate must be positive, got {annual_rate_ea}")
    return (1 + annual_rate_ea) ** (1 / 12) - 1


def compute_payment(loan: float, monthly_rate: float, n_months: int) -> float:
    """Compute fixed monthly payment for a French amortization loan.

    Formula: A = D₀ × r / (1 − (1+r)^−n)

    Args:
        loan: Principal amount (D₀)
        monthly_rate: Monthly effective rate as a decimal
        n_months: Total number of monthly payments

    Returns:
        Fixed monthly payment amount.
    """
    if loan <= 0:
        raise ValueError(f"Loan must be positive, got {loan}")
    if monthly_rate <= 0:
        raise ValueError(f"Monthly rate must be positive, got {monthly_rate}")
    if n_months <= 0:
        raise ValueError(f"Number of months must be positive, got {n_months}")

    return loan * monthly_rate / (1 - (1 + monthly_rate) ** (-n_months))


def compute_months(loan: float, monthly_rate: float, payment: float) -> float:
    """Solve for the number of months given a fixed monthly payment.

    Formula: n = −ln(1 − r×D₀/A) / ln(1+r)

    Args:
        loan: Principal amount (D₀)
        monthly_rate: Monthly effective rate as a decimal
        payment: Fixed monthly payment amount

    Returns:
        Number of months as a float (caller rounds/ceils as needed).

    Raises:
        ValueError: If payment does not exceed the interest-only floor (loan × rate),
                    meaning the loan would never be paid off.
    """
    floor = min_payment(loan, monthly_rate)
    if payment <= floor:
        raise ValueError(
            f"Payment ({payment:,.0f}) must exceed the interest-only floor "
            f"({floor:,.0f}). At this payment the principal never decreases."
        )
    return -math.log(1 - monthly_rate * loan / payment) / math.log(1 + monthly_rate)


def min_payment(loan: float, monthly_rate: float) -> float:
    """Minimum payment that covers only interest — zero principal reduction.

    Any payment at or below this value means the loan balance never decreases.

    Formula: A_min = D₀ × r
    """
    return loan * monthly_rate


def danger_ceiling(payment: float, monthly_rate: float) -> float:
    """The loan amount at which a given payment covers only perpetual interest.

    If the actual loan exceeds this value, the payment will never pay it off.

    Formula: D_danger = A / r
    """
    if monthly_rate <= 0:
        raise ValueError(f"Monthly rate must be positive, got {monthly_rate}")
    return payment / monthly_rate


def total_interest(payment: float, n_months: float, loan: float) -> float:
    """Total interest paid over the life of the loan.

    Formula: total_interest = (A × n) − D₀
    """
    return payment * n_months - loan


def net_cost_after_rental(
    total_paid: float, monthly_rental: float, n_months: float
) -> float:
    """Effective total cost after offsetting with rental income.

    Args:
        total_paid: Total amount paid to the bank (principal + interest)
        monthly_rental: Monthly rental income received from the property
        n_months: Duration of the loan in months

    Returns:
        Net cost. Can be negative if rental income exceeds total paid.
    """
    return total_paid - monthly_rental * n_months


def net_interest_after_rental(
    total_interest_paid: float, monthly_rental: float, n_months: float
) -> float:
    """Effective interest paid after offsetting with rental income.

    Args:
        total_interest_paid: Total interest paid over the loan term
        monthly_rental: Monthly rental income received
        n_months: Duration of the loan in months

    Returns:
        Net interest. Can be negative if rental fully offsets interest.
    """
    return total_interest_paid - monthly_rental * n_months
