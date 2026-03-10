"""
Plotly figure builders. No st.* calls inside — returns go.Figure objects.
"""

import pandas as pd
import plotly.graph_objects as go


def build_amortization_chart(
    schedule: pd.DataFrame,
    show_rental_line: bool,
    payoff_month: int,
) -> go.Figure:
    """Build the interactive amortization chart.

    Traces:
        - Remaining Principal  (blue, decreasing)
        - Cumulative Interest   (red, increasing)
        - Cumulative Principal  (green, increasing)
        - Net Cost after Rental (orange dashed, only if show_rental_line=True)

    Args:
        schedule: DataFrame from amortization.build_schedule()
        show_rental_line: Whether to render the net cost trace
        payoff_month: Month number at which the loan is fully paid off

    Returns:
        A Plotly Figure ready to pass to st.plotly_chart().
    """
    months = schedule["month"]

    hover = "<b>Month %{x}</b><br>%{y:$,.0f}<extra></extra>"

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=months,
            y=schedule["remaining_principal"],
            name="Remaining Principal",
            line=dict(color="#2563EB", width=2),
            hovertemplate=hover,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=months,
            y=schedule["cumulative_interest"],
            name="Cumulative Interest Paid",
            line=dict(color="#DC2626", width=2),
            hovertemplate=hover,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=months,
            y=schedule["cumulative_principal"],
            name="Cumulative Principal Paid",
            line=dict(color="#16A34A", width=2),
            hovertemplate=hover,
        )
    )

    if show_rental_line:
        fig.add_trace(
            go.Scatter(
                x=months,
                y=schedule["net_cumulative_cost"],
                name="Net Cost (after Rental)",
                line=dict(color="#EA580C", width=2, dash="dash"),
                hovertemplate=hover,
            )
        )

    # Payoff marker
    fig.add_vline(
        x=payoff_month,
        line_dash="dot",
        line_color="#64748B",
        line_width=1.5,
        annotation_text=f"Payoff — month {payoff_month}",
        annotation_position="top left",
        annotation_font_color="#64748B",
    )

    fig.update_layout(
        title="Amortization Schedule",
        xaxis_title="Month",
        yaxis_title="Amount (COP)",
        yaxis_tickformat="$,.0f",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin=dict(t=80, b=40, l=20, r=20),
    )

    fig.update_xaxes(showgrid=True, gridcolor="#E2E8F0")
    fig.update_yaxes(showgrid=True, gridcolor="#E2E8F0")

    return fig
