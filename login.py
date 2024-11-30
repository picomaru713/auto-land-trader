import requests
from bs4 import BeautifulSoup
import yfinance as yf
from config import LOGIN_URL, ORDER_URL, LOGIN_SUCCESS_TEXT, LOGIN_DATA, ORDER_DATA, STOCK_DATA_URL

def login_and_create_session() -> requests.Session | None:
    """ログインしてセッションを作成します。成功すればセッションを返します。"""
    session = requests.Session()
    if LOGIN_SUCCESS_TEXT in session.post(LOGIN_URL, data=LOGIN_DATA).text:
        print("ログイン成功")
        return session
    print("ログイン失敗")
    return None

def fetch_stock_data(session: requests.Session) -> tuple[list, int]:
    """保有株データと資産合計を取得します。"""
    stock_data_response = session.get(STOCK_DATA_URL)
    soup = BeautifulSoup(stock_data_response.text, 'html.parser')
    stock_table = soup.find_all('div', class_='table_wrapper')[1].find('table', class_='Dealings sp_layout')
    stock_data = [
        [col.text.strip().replace(',', '') for col in row.find_all('td')]
        for row in stock_table.find_all('tr')[1:]  # ヘッダーを除く
    ] if stock_table else []

    total_assets_response = session.get('https://www.ssg.ne.jp/performances/team')
    total_assets_div = BeautifulSoup(total_assets_response.text, 'html.parser').find('div', id='temoStock')
    total_assets = int(total_assets_div.find('table').find('tbody').find_all('tr')[1].find_all('td')[0].text.replace(',', '')) if total_assets_div else 0

    return stock_data, total_assets

def fetch_land_stock_price() -> float | None:
    """ランド社の株価を取得します。"""
    stock = yf.Ticker("8918.T")
    hist = stock.history(period="1d")
    return hist['Close'].iloc[0] if not hist.empty else None

def place_order(session: requests.Session, ticker: str, volume: int, selling: bool) -> None:
    """注文を送信します。"""
    ORDER_DATA.update({
        'order_01[ticker_symbol]': ticker,
        'order_01[volume]': str(volume),
        'order_01[selling]': 'true' if selling else 'false'
    })
    if session.post(ORDER_URL, data=ORDER_DATA).status_code == 200:
        print("注文送信成功")
    else:
        print("注文送信失敗")

def main() -> None:
    """メイン処理を行います。"""
    session = login_and_create_session()
    if not session:
        return

    stock_data, total_assets = fetch_stock_data(session)
    land_stock_price = fetch_land_stock_price()

    if not land_stock_price:
        print("ランドの株価が取得できませんでした")
        return

    if stock_data and land_stock_price == 9.0:
        print("ランド売ります")
        place_order(session, '8918', int(stock_data[0][2]), True)
    elif not stock_data and land_stock_price == 8.0:
        num_shares = total_assets // (land_stock_price * 100)
        print(f"ランドの株を買える数: {num_shares * 100}株")
        place_order(session, '8918', num_shares * 100, False)
    else:
        print("注文条件を満たさないため注文を送信しませんでした")

if __name__ == "__main__":
    main()
