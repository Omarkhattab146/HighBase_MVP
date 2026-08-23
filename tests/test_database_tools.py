from app.tools.database import DatabaseTools
from scripts.generate_dummy_data import generate

def test_database_tools_are_read_only_and_bounded():
    tools=DatabaseTools(generate())
    rows=tools.search_products(query='water',limit=100)
    assert len(rows)<=20
    assert rows and {'name','price','availability','product_url'} <= rows[0].keys()
    assert '_id' not in rows[0]
    assert tools.get_database_overview()['collections']['products'] > 0

def test_inventory_and_analytics_tools():
    tools=DatabaseTools(generate())
    inventory=tools.check_inventory(query='coffee')
    assert inventory
    summary=tools.get_analytics_summary()
    assert 'top_products' in summary and 'category_sales' in summary

def test_offers_and_trending_products_are_structured():
    tools=DatabaseTools(generate())
    offers=tools.get_offers(limit=20)
    trends=tools.get_trending_products(limit=5)
    assert offers
    assert all(row['offer']['offer_price'] < row['price'] for row in offers)
    assert len(trends)<=5
    assert all(row['trend_growth'] is not None for row in trends)
