def process_orders(orders):
    valid = []
    for order in orders:
        if order.get('status') == 'active' and order.get('amount', 0) > 0:
            if order.get('customer_id') and order.get('product_id'):
                valid.append(order)
    return valid

def process_returns(returns):
    valid = []
    for ret in returns:
        if ret.get('status') == 'active' and ret.get('amount', 0) > 0:
            if ret.get('customer_id') and ret.get('product_id'):
                valid.append(ret)
    return valid
