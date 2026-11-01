from decimal import Decimal
import pytest
from app.services import *

def test_allocation():
    assert calculate_income_allocation(Decimal('50000')) == {'needs': Decimal('25000.00'), 'investment': Decimal('15000.00'), 'savings': Decimal('10000.00'), 'total': Decimal('50000.00')}

def test_invalid_allocation():
    with pytest.raises(ValueError): calculate_income_allocation(100, 50, 20, 20)

@pytest.mark.parametrize(('expenses','status','balance'), [(40000,'SURPLUS',10000),(50000,'BALANCED',0),(55000,'DEFICIT',-5000)])
def test_balance_status(expenses, status, balance):
    result = calculate_balance(50000, expenses)
    assert result['status'] == status and result['balance'] == Decimal(balance)

def test_savings_ratio_and_zero_income():
    assert calculate_balance(50000, 40000)['savings_ratio'] == Decimal('20.00')
    assert calculate_balance(0, 100)['savings_ratio'] is None

def test_capital_markup_margin():
    assert calculate_capital_requirement({'Equipment': 100000, 'Marketing': 30000, 'Operations': 50000})['total'] == Decimal('180000.00')
    assert calculate_markup_price(420, 25)['selling_price'] == Decimal('525.00')
    assert calculate_margin_price(420, 25)['selling_price'] == Decimal('560.00')
    with pytest.raises(ValueError): calculate_margin_price(420, 100)

def test_structures_and_guardrail():
    assert validate_swot({k: [] for k in SWOT_SECTIONS})
    with pytest.raises(ValueError): validate_swot({'Strengths': []})
    assert market_analysis('unknown market')['live_data_available'] is False
