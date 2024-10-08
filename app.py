import alpaca_trade_api as tradeapi
import time
import os
from datetime import datetime, timedelta
from alpaca_trade_api.rest import TimeFrame
from pytz import timezone  # Ensure this line is present

# Alpaca API keys from environment variables
API_KEY = os.getenv('APCA_API_KEY_ID')
SECRET_KEY = os.getenv('APCA_API_SECRET_KEY')
BASE_URL = os.getenv('APCA_API_BASE_URL')  # Paper trading URL

# Initialize Alpaca API
api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL)

def get_opening_price(stock):
    try:
        # Set Eastern Timezone
        eastern = timezone('US/Eastern')
        # Get today's date and market open time in Eastern Time
        today = datetime.now(eastern).date()
        market_open = eastern.localize(datetime.combine(today, datetime.min.time()).replace(hour=9, minute=30))
        # Get the first minute bar of the day
        start = market_open
        end = market_open + timedelta(minutes=1)
    
        # Fetch the bar data
        bars = api.get_bars(
            stock,
            TimeFrame.Minute,
            start,
            end,
            adjustment='raw'
        ).df

        if not bars.empty:
            opening_price = bars.iloc[0]['open']
            print(f"Opening price for {stock}: {opening_price}")
            return opening_price
        else:
            print(f"No opening price data for {stock}")
            return None
    except Exception as e:
        print(f"Error fetching opening price for {stock}: {e}")
        return None

def create_order(stock, qty):
    try:
        order = api.submit_order(
            symbol=stock,
            qty=qty,  # Adjust quantity as needed
            side='buy',
            type='market',
            time_in_force='day'  # Good for the day
        )
        print(f"Market order created for {stock}")
        return order
    except Exception as e:
        print(f"Failed to create order for {stock}: {e}")
        return None

def place_trailing_stop_order(stock, qty, trail_percent):
    try:
        order = api.submit_order(
            symbol=stock,
            qty=qty,
            side='sell',
            type='trailing_stop',
            trail_percent=str(trail_percent),  # trail_percent should be a string
            time_in_force='day'
        )
        print(f"Trailing stop order placed for {stock}")
    except Exception as e:
        print(f"Error placing trailing stop order for {stock}: {e}")

def trade_stock(stock):
    opening_price = get_opening_price(stock)
    if opening_price is None:
        return

    max_time = 2 * 60 * 60  # 2 hours in seconds
    start_time = time.time()

    while time.time() - start_time < max_time:
        try:
            # Get the latest trade price
            latest_trade = api.get_latest_trade(stock)
            current_price = latest_trade.price
            print(f"Current price for {stock}: {current_price}")
            
            if current_price > opening_price:
                qty = 10  # Adjust quantity as needed
                order = create_order(stock, qty)
                if order:
                    place_trailing_stop_order(stock, qty, trail_percent=5)
                break  # Exit the loop after placing the order
        except Exception as e:
            print(f"Error fetching current price for {stock}: {e}")
        
        time.sleep(60)  # Wait for 1 minute before checking the price again

    print(f"Trading for {stock} finished or time expired")

def main():
    print("Trading bot has started.")

    # Test API connection
    try:
        account = api.get_account()
        print(f"API connection successful. Account status: {account.status}")
    except Exception as e:
        print(f"Failed to connect to Alpaca API: {e}")
        return

    # Input stocks you want to trade each day
    stocks_to_trade = ['AAPL', 'TSLA']  # Replace with your stocks
    
    for stock in stocks_to_trade:
        trade_stock(stock)

if __name__ == '__main__':
    main()
