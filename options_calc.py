import pandas as pd

# Load the CSV file
file_path = './options.csv'
#file_path = './tester_options.csv'
df = pd.read_csv(file_path)

# Clean and prepare the data
df['Price'] = pd.to_numeric(df['Price'].str.replace('$', '', regex=True), errors='coerce')
df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
df['Amount'] = pd.to_numeric(df['Amount'].str.replace('[$()]', '', regex=True), errors='coerce').mul(df['Amount'].str.contains('\(').map({True: -1, False: 1}))

# Filter out non-options transactions (keep only options transactions)
options_df = df[df['Action'].isin(['Buy to Open', 'Sell to Close'])]

# Separate buy and sell transactions
buy_transactions = options_df[options_df['Action'] == 'Buy to Open'].copy()
sell_transactions = options_df[options_df['Action'] == 'Sell to Close'].copy()

# Sort transactions to ensure FIFO processing
buy_transactions.sort_values(by=['Date'], inplace=True)
sell_transactions.sort_values(by=['Date'], inplace=True)

# Track the quantities and total costs of buys for each symbol
buys_by_symbol = {}

# Process buys
for index, row in buy_transactions.iterrows():
    symbol = row['Symbol']
    if symbol not in buys_by_symbol:
        buys_by_symbol[symbol] = {'total_quantity': 0, 'weighted_average_price': 0, 'total_cost': 0}
    
    current_info = buys_by_symbol[symbol]
    new_total_quantity = current_info['total_quantity'] + row['Quantity']
    current_info['total_cost'] += (row['Price'] * row['Quantity'])
    current_info['weighted_average_price'] = current_info['total_cost'] / new_total_quantity
    current_info['total_quantity'] = new_total_quantity

# Calculate realized gains/losses
realized_gains_losses = []

for index, row in sell_transactions.iterrows():
    symbol = row['Symbol']
    if symbol in buys_by_symbol:
        sell_quantity = row['Quantity']
        sell_quantity = min(sell_quantity, buys_by_symbol[symbol]['total_quantity'])
        if sell_quantity > 0:
            sell_total = (row['Price'] * sell_quantity)
            buy_cost = buys_by_symbol[symbol]['weighted_average_price'] * sell_quantity
            realized_gain_loss = sell_total - buy_cost
            realized_gains_losses.append(realized_gain_loss)
            buys_by_symbol[symbol]['total_quantity'] -= sell_quantity
            if buys_by_symbol[symbol]['total_quantity'] > 0:
                buys_by_symbol[symbol]['total_cost'] -= buy_cost
            else:
                buys_by_symbol[symbol] = {'total_quantity': 0, 'weighted_average_price': 0, 'total_cost': 0}

# Total realized gain or loss
total_realized_gain_loss = sum(realized_gains_losses) * 100
if total_realized_gain_loss > 0:
    print(f"Congratulations! You have a profit of\n${total_realized_gain_loss:.2f}")
else:
    print(f"You dumbass, you lost\n-${-total_realized_gain_loss:.2f}.")
