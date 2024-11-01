import requests
from bs4 import BeautifulSoup
import yfinance as yf
from config import url, login_data

session = requests.Session()

# データの初期化
buy_data = {
    "limit": "",
    **{f"order_{i:02d}[ticker_symbol]": "" for i in range(1, 11)},
    **{f"order_{i:02d}[volume]": "" for i in range(1, 11)},
    **{f"order_{i:02d}[selling]": None for i in range(1, 11)}
}
submit_data = {
    "limit": "",
    "order_01[ticker_symbol]": "",
    "order_01[volume]": "", 
    "order_01[selling]": None,
}

def login():
    response = session.post(url, data=login_data)
        return True
    return False

def get_stock_data():
    response = session.get('https://www.ssg.ne.jp/performances/team')
    soup = BeautifulSoup(response.text, 'html.parser')
    divs = soup.find_all('div', class_='table_wrapper')
    if len(divs) >= 2:
        second_div = divs[1]
        table = second_div.find('table', class_='Dealings sp_layout')
        rows = table.find_all('tr')[1:]  # ヘッダー行をスキップ
        data = []
        for row in rows:
            cols = row.find_all('td')
            cols = [col.text.strip().replace(',', '') for col in cols]
            data.append(cols)
        return bool(data), data
    else:
        print("2番目のdivが見つかりませんでした")
        return False, []

def get_land_stock_price():
    stock = yf.Ticker("8918.T")  # ランドの銘柄コード
    hist = stock.history(period="1d")
    if not hist.empty:
        return hist['Close'].iloc[0]
    else:
        print("ランドの株価が取得できませんでした")
        return None

def get_total_assets():
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

login()
has_stock_data, data = get_stock_data()
print(f"株を所有しているか: {has_stock_data}")
# ランドの株価を取得
land_stock_price = get_land_stock_price()
print(f"ランドの株価: {land_stock_price}")

# 資産合計を取得
total_assets = get_total_assets()
#print(f"資産合計: {total_assets}")

if land_stock_price == 7.0 and not has_stock_data:
    print("購入します")
    if total_assets is not None:
        total_assets = int(total_assets)
        num_shares = total_assets // (land_stock_price * 100)
        print(f"ランドの株を買える数: {num_shares * 100}株")
        buy_data["order_01[ticker_symbol]"] = "8918.T"
        buy_data["order_01[volume]"] = str(num_shares * 100)
        buy_data["order_01[selling]"] = "false"
        response = session.post("https://www.ssg.ne.jp/orders/form", data=buy_data)
        if response.status_code == 200:
            print("注文が正常に送信されました")
        else:
            print(f"注文の送信に失敗しました。ステータスコード: {response.status_code}")
        submit_data["order_01[ticker_symbol]"] = "8918"
        submit_data["order_01[volume]"] = str(num_shares * 100)
        submit_data["order_01[selling]"] = "false"
        session.post("https://www.ssg.ne.jp/orders/bulk", data=submit_data)  # URLを再度修正
    else:
        print("資産合計が取得できなかったため、ランドの株を買える数を計算できませんでした")
elif land_stock_price == 8.0 and has_stock_data:
    print("売ります")
    buy_data["order_01[ticker_symbol]"] = "8918.T"
    buy_data["order_01[volume]"] = data[0][2]
    buy_data["order_01[selling]"] = "true"
    session.post("https://www.ssg.ne.jp/orders/form", data=buy_data)
    print("ランドの保有数: {}".format(data[0][2]))
    submit_data["order_01[ticker_symbol]"] = "8918.T"
    submit_data["order_01[volume]"] = data[0][2]
    submit_data["order_01[selling]"] = "true"
    session.post("https://www.ssg.ne.jp/orders/bulk", data=submit_data)  # URLを再度修正
else:
    print("do nothing")