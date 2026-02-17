"""
Financial Engine - Core financial calculations and metrics.
Handles all business logic for financial analysis.
"""
import pandas as pd
from typing import Dict, Any, Tuple


def calculate_financials(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate core financial metrics from ledger data.
    
    Args:
        df: Ledger DataFrame with columns: type, amount, status, client
        
    Returns:
        Dictionary containing all financial metrics
    """
    # Revenue calculations
    income_df = df[df["type"] == "income"]
    revenue = float(income_df["amount"].sum())
    
    # Expense calculations
    expense_df = df[df["type"] == "expense"]
    expenses = float(expense_df["amount"].sum())
    
    # Profit
    profit = revenue - expenses
    
    # Outstanding receivables (unpaid income)
    receivables = float(
        df[(df["type"] == "income") & (df["status"] == "unpaid")]["amount"].sum()
    )
    
    # Client concentration analysis
    client_concentration = (
        income_df.groupby("client")["amount"]
        .sum()
        .sort_values(ascending=False)
    )
    
    top_client_share = 0.0
    top_client_name = "N/A"
    if len(client_concentration) > 0 and revenue > 0:
        top_client_share = (client_concentration.iloc[0] / revenue) * 100
        top_client_name = client_concentration.index[0]
    
    return {
        "revenue": revenue,
        "expenses": expenses,
        "profit": profit,
        "receivables": receivables,
        "top_client_share": top_client_share,
        "top_client_name": top_client_name,
        "client_concentration": client_concentration,
        "profit_margin": (profit / revenue * 100) if revenue > 0 else 0,
        "receivables_ratio": (receivables / revenue * 100) if revenue > 0 else 0
    }


def get_overdue_clients(df: pd.DataFrame) -> list:
    """
    Get list of clients with unpaid invoices.
    
    Args:
        df: Ledger DataFrame
        
    Returns:
        List of client names with outstanding payments
    """
    overdue = df[(df["type"] == "income") & (df["status"] == "unpaid")]
    return overdue["client"].unique().tolist()


def assess_financial_health(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assess overall financial health based on metrics.
    
    Args:
        metrics: Dictionary of financial metrics
        
    Returns:
        Health assessment with risk flags and scores
    """
    risks = []
    score = 100  # Start with perfect score
    
    # Check profitability
    if metrics["profit"] < 0:
        risks.append({
            "type": "critical",
            "message": "Business is running at a loss",
            "recommendation": "Immediate cost review required"
        })
        score -= 30
    
    # Check receivables ratio
    if metrics["receivables_ratio"] > 30:
        risks.append({
            "type": "warning",
            "message": f"High receivables ({metrics['receivables_ratio']:.1f}% of revenue)",
            "recommendation": "Initiate collection follow-ups"
        })
        score -= 20
    
    # Check client concentration
    if metrics["top_client_share"] > 50:
        risks.append({
            "type": "warning",
            "message": f"Revenue dependency risk - {metrics['top_client_name']} represents {metrics['top_client_share']:.1f}%",
            "recommendation": "Diversify client base"
        })
        score -= 15
    
    # Determine health status
    if score >= 80:
        status = "healthy"
    elif score >= 60:
        status = "moderate"
    else:
        status = "critical"
    
    return {
        "score": max(0, score),
        "status": status,
        "risks": risks
    }


def format_financial_state(metrics: Dict[str, Any]) -> str:
    """
    Format financial metrics as a string for AI agent context.
    
    Args:
        metrics: Dictionary of financial metrics
        
    Returns:
        Formatted string representation
    """
    return f"""
    Revenue: ₹{metrics['revenue']:,.2f}
    Expenses: ₹{metrics['expenses']:,.2f}
    Profit: ₹{metrics['profit']:,.2f}
    Profit Margin: {metrics['profit_margin']:.2f}%
    Outstanding Receivables: ₹{metrics['receivables']:,.2f}
    Receivables Ratio: {metrics['receivables_ratio']:.2f}%
    Top Client: {metrics['top_client_name']} ({metrics['top_client_share']:.2f}% of revenue)
    """
