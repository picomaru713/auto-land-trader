import requests
from bs4 import BeautifulSoup
import yfinance as yf
from config import LOGIN_URL, ORDER_URL, LOGIN_SUCCESS_TEXT, LOGIN_DATA, ORDER_DATA, STOCK_DATA_URL

def login(session, url, data):
    """ログインを試みる"""
    response = session.post(url, data=data)
    if LOGIN_SUCCESS_TEXT in response.text:
        print("ログイン成功")
        return True
    else:
        print("ログイン失敗")
        return False

def send_order(session, url, data):
    """注文を送信する"""
    response = session.post(url, data=data)
    if response.status_code == 200:
        print("注文送信成功")
    else:
        print("注文送信失敗")
        
def get_stock_data(session):
    """株を持っているかどうかを取得する"""
    
    response = session.get(STOCK_DATA_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    divs = soup.find_all('div', class_='table_wrapper')
    
    if len(divs) < 2:
        print("2番目のdivが見つかりませんでした")
        return False, []
    
    second_div = divs[1]
    table = second_div.find('table', class_='Dealings sp_layout')
    rows = table.find_all('tr')[1:]  # ヘッダー行をスキップ
    
    data = [
        [col.text.strip().replace(',', '') for col in row.find_all('td')]
        for row in rows
    ]
    
    return bool(data), data

def get_total_assets(session):
    """資産合計を取得する"""
    response = session.get('https://www.ssg.ne.jp/performances/team')
    soup = BeautifulSoup(response.text, 'html.parser')
    temo_stock_div = soup.find('div', id='temoStock')
    if temo_stock_div:
        table = temo_stock_div.find('table')
        if table:
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                if len(rows) >= 2:
                    second_row = rows[1]
                    cols = second_row.find_all('td')
                    if cols:
                        total_assets = cols[0].text.strip().replace(',', '')
                        return total_assets
    print("資産合計が見つかりませんでした")
    return None

def get_land_stock_price():
    stock = yf.Ticker("8918.T")  # ランドの銘柄コード
    hist = stock.history(period="1d")
    if not hist.empty:
        return hist['Close'].iloc[0]
    else:
        print("ランドの株価が取得できませんでした")
        return None

def main():
    session = requests.Session()
    if login(session, LOGIN_URL, LOGIN_DATA):
        has_stock, stock_data = get_stock_data(session)
        land_stock_price = get_land_stock_price()
        if has_stock and land_stock_price == 8.0:
            ORDER_DATA['order_01[ticker_symbol]'] = '8918'
            ORDER_DATA['order_01[volume]'] = stock_data[0][2]
            ORDER_DATA['order_01[selling]'] = 'true'
            
            print("ランド売ります")
        elif not has_stock and land_stock_price == 7.0:
            total_assets = int(get_total_assets(session))
            num_shares = total_assets // (land_stock_price * 100)
            
            print(f"ランドの株を買える数: {num_shares * 100}株")
            
            ORDER_DATA['order_01[ticker_symbol]'] = '8918'
            ORDER_DATA['order_01[volume]'] = str(num_shares * 100)
            ORDER_DATA['order_01[selling]'] = 'false'
            
            print("ランド買います")
        else:
            print("注文条件を満たさないため注文を送信しませんでした")
            return
        print(ORDER_DATA)
        send_order(session, ORDER_URL, ORDER_DATA)

if __name__ == "__main__":
    main()