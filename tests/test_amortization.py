"""Tests for calculator/amortization.py"""

import pytest

from calculator.amortization import build_schedule
from calculator.math_core import compute_payment, monthly_rate_from_ea

ANNUAL_RATE = 0.127
LOAN = 190_000_000.0
N_MONTHS = 180
MONTHLY_RATE = monthly_rate_from_ea(ANNUAL_RATE)
PAYMENT = compute_payment(LOAN, MONTHLY_RATE, N_MONTHS)


@pytest.fixture
def schedule():
    return build_schedule(LOAN, MONTHLY_RATE, PAYMENT, N_MONTHS)


class TestScheduleShape:
    def test_row_count(self, schedule):
        assert len(schedule) == N_MONTHS

    def test_columns_present(self, schedule):
        expected = {
            "month",
            "remaining_principal",
            "interest_this_month",
            "principal_this_month",
            "cumulative_interest",
            "cumulative_principal",
            "net_cumulative_cost",
        }
        assert expected.issubset(set(schedule.columns))

    def test_month_index_starts_at_1(self, schedule):
        assert schedule["month"].iloc[0] == 1

    def test_month_index_ends_at_n(self, schedule):
        assert schedule["month"].iloc[-1] == N_MONTHS


class TestFirstRow:
    def test_first_interest_equals_loan_times_rate(self, schedule):
        expected_interest = LOAN * MONTHLY_RATE
        assert abs(schedule["interest_this_month"].iloc[0] - expected_interest) < 1.0

    def test_first_principal_plus_interest_equals_payment(self, schedule):
        row = schedule.iloc[0]
        assert abs(row["interest_this_month"] + row["principal_this_month"] - PAYMENT) < 1.0

    def test_first_remaining_principal_less_than_loan(self, schedule):
        assert schedule["remaining_principal"].iloc[0] < LOAN

    def test_first_cumulative_principal_equals_first_principal_paid(self, schedule):
        row = schedule.iloc[0]
        assert abs(row["cumulative_principal"] - row["principal_this_month"]) < 1.0


class TestLastRow:
    def test_remaining_principal_is_zero(self, schedule):
        assert schedule["remaining_principal"].iloc[-1] == 0.0

    def test_cumulative_principal_equals_loan(self, schedule):
        assert abs(schedule["cumulative_principal"].iloc[-1] - LOAN) < 1.0

    def test_cumulative_interest_positive(self, schedule):
        assert schedule["cumulative_interest"].iloc[-1] > 0


class TestMonotonicity:
    def test_remaining_principal_is_decreasing(self, schedule):
        principal = schedule["remaining_principal"]
        assert (principal.diff().dropna() <= 0).all()

    def test_cumulative_interest_is_increasing(self, schedule):
        cum_int = schedule["cumulative_interest"]
        assert (cum_int.diff().dropna() > 0).all()

    def test_cumulative_principal_is_increasing(self, schedule):
        cum_pri = schedule["cumulative_principal"]
        assert (cum_pri.diff().dropna() > 0).all()

    def test_interest_portion_is_decreasing_over_time(self, schedule):
        # In French amortization, the interest portion shrinks each month
        interest = schedule["interest_this_month"]
        assert (interest.diff().dropna() < 0).all()

    def test_principal_portion_is_increasing_over_time(self, schedule):
        principal = schedule["principal_this_month"]
        assert (principal.diff().dropna() > 0).all()


class TestTotals:
    def test_total_paid_equals_payment_times_months(self, schedule):
        total = (
            schedule["interest_this_month"].sum()
            + schedule["principal_this_month"].sum()
        )
        assert abs(total - PAYMENT * N_MONTHS) < 1.0

    def test_cumulative_principal_plus_remaining_equals_loan(self, schedule):
        for _, row in schedule.iterrows():
            total = row["cumulative_principal"] + row["remaining_principal"]
            assert abs(total - LOAN) < 1.0


class TestRentalColumn:
    def test_no_rental_net_cost_equals_cumulative_interest(self):
        sched = build_schedule(LOAN, MONTHLY_RATE, PAYMENT, N_MONTHS, monthly_rental=0)
        diff = (sched["net_cumulative_cost"] - sched["cumulative_interest"]).abs()
        assert (diff < 1.0).all()

    def test_rental_reduces_net_cumulative_cost(self):
        rental = 1_000_000
        sched = build_schedule(LOAN, MONTHLY_RATE, PAYMENT, N_MONTHS, monthly_rental=rental)
        assert (sched["net_cumulative_cost"] < sched["cumulative_interest"]).all()

    def test_net_cost_can_be_negative_with_high_rental(self):
        # Rental larger than average monthly interest → eventually net cost goes negative
        high_rental = PAYMENT  # extreme case: rental covers entire payment
        sched = build_schedule(LOAN, MONTHLY_RATE, PAYMENT, N_MONTHS, monthly_rental=high_rental)
        assert sched["net_cumulative_cost"].iloc[-1] < 0
