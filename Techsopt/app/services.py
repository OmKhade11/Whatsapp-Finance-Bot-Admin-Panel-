from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

MONEY = Decimal('0.01')

def money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)

def calculate_income_allocation(monthly_income: Decimal, needs_percent=Decimal('50'), investment_percent=Decimal('30'), savings_percent=Decimal('20')):
    percentages = {'needs': Decimal(needs_percent), 'investment': Decimal(investment_percent), 'savings': Decimal(savings_percent)}
    if sum(percentages.values()) != Decimal('100') or any(v < 0 for v in percentages.values()):
        raise ValueError('allocation percentages must total 100% and be non-negative')
    income = Decimal(monthly_income)
    result = {key: money(income * value / 100) for key, value in percentages.items()}
    result['total'] = sum(result.values(), Decimal('0.00'))
    return result

def calculate_balance(total_income: Decimal, total_expenses: Decimal):
    balance = money(Decimal(total_income) - Decimal(total_expenses))
    status = 'SURPLUS' if balance > 0 else 'DEFICIT' if balance < 0 else 'BALANCED'
    return {'total_income': money(total_income), 'total_expenses': money(total_expenses), 'balance': balance, 'status': status,
            'savings_ratio': money(max(balance, Decimal('0')) / Decimal(total_income) * 100) if total_income > 0 else None}

def calculate_capital_requirement(costs: dict[str, Decimal], assumptions: list[str] | None = None):
    if not costs or any(Decimal(value) < 0 for value in costs.values()): raise ValueError('costs must be non-negative')
    return {'costs': {k: money(v) for k, v in costs.items()}, 'total': money(sum((Decimal(v) for v in costs.values()), Decimal('0'))), 'assumptions': assumptions or []}

def calculate_markup_price(total_cost: Decimal, markup_percentage: Decimal):
    return {'method': 'MARKUP', 'total_cost': money(total_cost), 'percentage': Decimal(markup_percentage), 'selling_price': money(Decimal(total_cost) * (1 + Decimal(markup_percentage) / 100))}

def calculate_margin_price(total_cost: Decimal, margin_percentage: Decimal):
    margin = Decimal(margin_percentage)
    if margin >= 100: raise ValueError('margin percentage must be less than 100')
    return {'method': 'MARGIN', 'total_cost': money(total_cost), 'percentage': margin, 'selling_price': money(Decimal(total_cost) / (1 - margin / 100))}

SWOT_SECTIONS = ('Strengths', 'Weaknesses', 'Opportunities', 'Threats')
BUSINESS_PLAN_SECTIONS = ('Executive Summary', 'Business Overview', 'Problem / Opportunity', 'Product or Service', 'Target Customer', 'Market Overview', 'Operating Approach', 'Marketing & Sales Approach', 'Capital Requirement', 'Pricing Strategy', 'SWOT Analysis', 'Risks & Assumptions', 'Recommended Next Steps')

def validate_swot(value: dict):
    if tuple(value.keys()) != SWOT_SECTIONS or any(not isinstance(value[k], list) for k in SWOT_SECTIONS): raise ValueError('SWOT must contain exactly the four required sections')
    return value

def market_analysis(statement: str, source: str | None = None):
    return {'analysis': statement, 'source': source or 'user-provided information/assumptions', 'live_data_available': False}
