"""Tests for calculator/math_core.py

Reference case: 190,000,000 COP loan at 12.7% E.A. over 180 months.
All monetary values in COP (float). Tolerance for float comparisons: 1 COP.
"""

import math

import pytest

from calculator.math_core import (
    compute_months,
    compute_payment,
    danger_ceiling,
    min_payment,
    monthly_rate_from_ea,
    net_cost_after_rental,
    net_interest_after_rental,
    total_interest,
)

# --- Reference constants ---
ANNUAL_RATE = 0.127
LOAN = 190_000_000.0
N_MONTHS = 180
MONTHLY_RATE = monthly_rate_from_ea(ANNUAL_RATE)


class TestMonthlyRateFromEA:
    def test_known_value(self):
        # (1.127)^(1/12) - 1, verified externally
        r = monthly_rate_from_ea(0.127)
        assert abs(r - 0.010014) < 0.000001

    def test_annual_to_monthly_round_trip(self):
        # (1 + r)^12 - 1 should recover the annual rate
        r = monthly_rate_from_ea(0.12)
        recovered = (1 + r) ** 12 - 1
        assert abs(recovered - 0.12) < 1e-10

    def test_raises_on_zero_rate(self):
        with pytest.raises(ValueError):
            monthly_rate_from_ea(0.0)

    def test_raises_on_negative_rate(self):
        with pytest.raises(ValueError):
            monthly_rate_from_ea(-0.05)


class TestComputePayment:
    def test_reference_case(self):
        payment = compute_payment(LOAN, MONTHLY_RATE, N_MONTHS)
        # Expected ~2,280,000–2,290,000 COP range
        assert 2_200_000 < payment < 2_400_000

    def test_payment_exceeds_min_payment(self):
        payment = compute_payment(LOAN, MONTHLY_RATE, N_MONTHS)
        floor = min_payment(LOAN, MONTHLY_RATE)
        assert payment > floor

    def test_shorter_term_means_higher_payment(self):
        p_180 = compute_payment(LOAN, MONTHLY_RATE, 180)
        p_120 = compute_payment(LOAN, MONTHLY_RATE, 120)
        assert p_120 > p_180

    def test_higher_rate_means_higher_payment(self):
        r_low = monthly_rate_from_ea(0.08)
        r_high = monthly_rate_from_ea(0.15)
        p_low = compute_payment(LOAN, r_low, N_MONTHS)
        p_high = compute_payment(LOAN, r_high, N_MONTHS)
        assert p_high > p_low

    def test_raises_on_non_positive_loan(self):
        with pytest.raises(ValueError):
            compute_payment(0, MONTHLY_RATE, N_MONTHS)

    def test_raises_on_non_positive_months(self):
        with pytest.raises(ValueError):
            compute_payment(LOAN, MONTHLY_RATE, 0)


class TestComputeMonths:
    def test_round_trip_with_compute_payment(self):
        payment = compute_payment(LOAN, MONTHLY_RATE, N_MONTHS)
        recovered = compute_months(LOAN, MONTHLY_RATE, payment)
        assert abs(recovered - N_MONTHS) < 0.01

    def test_higher_payment_means_fewer_months(self):
        payment_low = compute_payment(LOAN, MONTHLY_RATE, 240)
        payment_high = compute_payment(LOAN, MONTHLY_RATE, 120)
        months_low = compute_months(LOAN, MONTHLY_RATE, payment_low)
        months_high = compute_months(LOAN, MONTHLY_RATE, payment_high)
        assert months_high < months_low

    def test_raises_when_payment_at_floor(self):
        floor = min_payment(LOAN, MONTHLY_RATE)
        with pytest.raises(ValueError):
            compute_months(LOAN, MONTHLY_RATE, floor)

    def test_raises_when_payment_below_floor(self):
        floor = min_payment(LOAN, MONTHLY_RATE)
        with pytest.raises(ValueError):
            compute_months(LOAN, MONTHLY_RATE, floor * 0.9)


class TestMinPayment:
    def test_reference_case(self):
        floor = min_payment(LOAN, MONTHLY_RATE)
        # 190M × ~0.010014 ≈ 1,902,660
        assert 1_800_000 < floor < 2_000_000

    def test_equals_interest_portion_of_first_payment(self):
        # The interest portion of the first payment should equal min_payment
        payment = compute_payment(LOAN, MONTHLY_RATE, N_MONTHS)
        first_interest = LOAN * MONTHLY_RATE
        floor = min_payment(LOAN, MONTHLY_RATE)
        assert abs(first_interest - floor) < 1.0  # within 1 COP


class TestDangerCeiling:
    def test_ceiling_greater_than_reference_loan(self):
        payment = compute_payment(LOAN, MONTHLY_RATE, N_MONTHS)
        ceiling = danger_ceiling(payment, MONTHLY_RATE)
        # The ceiling should be > the actual loan (since the payment does pay it off)
        assert ceiling > LOAN

    def test_ceiling_equals_loan_at_min_payment(self):
        # If payment exactly equals the interest floor, danger ceiling equals the loan
        floor = min_payment(LOAN, MONTHLY_RATE)
        ceiling = danger_ceiling(floor, MONTHLY_RATE)
        assert abs(ceiling - LOAN) < 1.0  # within 1 COP

    def test_raises_on_zero_rate(self):
        with pytest.raises(ValueError):
            danger_ceiling(1_000_000, 0.0)


class TestTotalInterest:
    def test_positive_for_reference_case(self):
        payment = compute_payment(LOAN, MONTHLY_RATE, N_MONTHS)
        interest = total_interest(payment, N_MONTHS, LOAN)
        assert interest > 0

    def test_total_paid_equals_loan_plus_interest(self):
        payment = compute_payment(LOAN, MONTHLY_RATE, N_MONTHS)
        interest = total_interest(payment, N_MONTHS, LOAN)
        total_paid = payment * N_MONTHS
        assert abs((LOAN + interest) - total_paid) < 1.0


class TestNetCostAfterRental:
    def test_no_rental_equals_total_paid(self):
        payment = compute_payment(LOAN, MONTHLY_RATE, N_MONTHS)
        total_paid = payment * N_MONTHS
        net = net_cost_after_rental(total_paid, 0, N_MONTHS)
        assert abs(net - total_paid) < 1.0

    def test_rental_reduces_net_cost(self):
        payment = compute_payment(LOAN, MONTHLY_RATE, N_MONTHS)
        total_paid = payment * N_MONTHS
        net = net_cost_after_rental(total_paid, 1_000_000, N_MONTHS)
        assert net < total_paid

    def test_can_be_negative(self):
        # If rental > total paid / n, net cost goes negative (rental arbitrage)
        payment = compute_payment(LOAN, MONTHLY_RATE, N_MONTHS)
        total_paid = payment * N_MONTHS
        high_rental = total_paid / N_MONTHS + 1
        net = net_cost_after_rental(total_paid, high_rental, N_MONTHS)
        assert net < 0


class TestNetInterestAfterRental:
    def test_no_rental_equals_total_interest(self):
        payment = compute_payment(LOAN, MONTHLY_RATE, N_MONTHS)
        interest = total_interest(payment, N_MONTHS, LOAN)
        net = net_interest_after_rental(interest, 0, N_MONTHS)
        assert abs(net - interest) < 1.0

    def test_rental_reduces_effective_interest(self):
        payment = compute_payment(LOAN, MONTHLY_RATE, N_MONTHS)
        interest = total_interest(payment, N_MONTHS, LOAN)
        net = net_interest_after_rental(interest, 500_000, N_MONTHS)
        assert net < interest
