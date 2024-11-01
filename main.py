import requests
from bs4 import BeautifulSoup
import yfinance as yf
from config import url, login_data

session = requests.Session()
buy_data = {
    "limit":"",
    "order_01[ticker_symbol]":"",
    "order_01[volume]":"", 
    "order_01[selling]": None,
    "order_02[ticker_symbol]":"", 
    "order_02[volume]":"",
    "order_02[selling]": None,
    "order_03[ticker_symbol]":"", 
    "order_03[volume]":"", 
    "order_03[selling]": None,
    "order_04[ticker_symbol]":"", 
    "order_04[volume]":"", 
    "order_04[selling]": None,
    "order_05[ticker_symbol]":"", 
    "order_05[volume]":"", 
    "order_05[selling]": None,
    "order_06[ticker_symbol]":"", 
    "order_06[volume]":"", 
    "order_06[selling]": None,
    "order_07[ticker_symbol]":"", 
    "order_07[volume]":"", 
    "order_07[selling]": None,
    "order_08[ticker_symbol]":"", 
    "order_08[volume]":"",
    "order_08[selling]": None,
    "order_09[ticker_symbol]":"", 
    "order_09[volume]":"", 
    "order_09[selling]": None,
    "order_10[ticker_symbol]":"",
    "order_10[volume]":"",
    "order_10[selling]": None
}

def login():
    response = session.post(url, data=login_data)
    if '<a class="el_btn el_btn__small el_btn__greenVer2 logoutBtn_sp" href="/logout" data-turbolinks="false">ログアウト</a>' in response.text:
        print("ログイン成功")
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
        session.post("https://www.ssg.ne.jp/orders/form", data=buy_data)
    else:
        print("資産合計が取得できなかったため、ランドの株を買える数を計算できませんでした")
elif land_stock_price == 8.0 and has_stock_data:
    print("売ります")
    buy_data["order_01[ticker_symbol]"] = "8918.T"
    buy_data["order_01[volume]"] = data[0][2]
    buy_data["order_01[selling]"] = "true"
    session.post("https://www.ssg.ne.jp/orders/form", data=buy_data)
    print("ランドの保有数: {}".format(data[0][2]))
else:
    print("do nothing")