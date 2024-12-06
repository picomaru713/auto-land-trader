import logging
import requests
from bs4 import BeautifulSoup
import yfinance as yf
from datetime import datetime, timedelta, timezone
import os
import json

JST = timezone(timedelta(hours=9))

class JSTFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        record_time = datetime.fromtimestamp(record.created, JST)
        if datefmt:
            return record_time.strftime(datefmt)
        else:
            return record_time.strftime('%Y-%m-%d %H:%M:%S')

LOG_FILE = "trading_log.txt"
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

for handler in logging.getLogger().handlers:
    handler.setFormatter(JSTFormatter('[%(asctime)s] %(message)s'))

# 環境変数からJSON文字列を取得
credentials_json = os.environ.get('USERS_CREDENTIALS', '{}')
data = json.loads(credentials_json)
USERS = data.get('users', [])

# 以下、USERSを使ってループすることで、ユーザーが何人増えても同じコードで処理できる
# USERSは [{'course_code':..., 'course_password':..., 'user_code':..., 'user_password':...}, {...}] というリスト形式

LOGIN_URL = 'https://www.ssg.ne.jp/session'
ORDER_URL = 'https://www.ssg.ne.jp/orders/bulk'
LOGIN_SUCCESS_TEXT = (
    '<a class="el_btn el_btn__small el_btn__greenVer2 logoutBtn_sp" '
    'href="/logout" data-turbolinks="false">ログアウト</a>'
)
STOCK_DATA_URL = 'https://www.ssg.ne.jp/performances/team'

BASE_ORDER_DATA = {'limit': ''}
for i in range(1, 11):
    BASE_ORDER_DATA.update({
        f'order_{i:02}[ticker_symbol]': '',
        f'order_{i:02}[volume]': '',
        f'order_{i:02}[selling]': 'null'
    })

def log_divider():
    logging.info("=" * 55)

def login_and_create_session(login_data: dict) -> requests.Session | None:
    session = requests.Session()
    response = session.post(LOGIN_URL, data=login_data)
    if LOGIN_SUCCESS_TEXT in response.text:
        logging.info("ログイン成功")
        return session
    logging.error("ログイン失敗")
    return None

def fetch_stock_data(session: requests.Session) -> tuple[list, int]:
    logging.info("株式データを取得しています...")
    stock_data_response = session.get(STOCK_DATA_URL)
    soup = BeautifulSoup(stock_data_response.text, 'html.parser')
    stock_table = soup.find_all('div', class_='table_wrapper')[1].find('table', class_='Dealings sp_layout')
    stock_data = [
        [col.text.strip().replace(',', '') for col in row.find_all('td')]
        for row in stock_table.find_all('tr')[1:]
    ] if stock_table else []
    logging.info(f"保有株データ: {stock_data}")

    total_assets_response = session.get('https://www.ssg.ne.jp/performances/team')
    total_assets_div = BeautifulSoup(total_assets_response.text, 'html.parser').find('div', id='temoStock')
    total_assets = int(total_assets_div.find('table').find('tbody').find_all('tr')[1].find_all('td')[0].text.replace(',', '')) if total_assets_div else 0
    logging.info(f"資産合計: {total_assets:,}円")

    return stock_data, total_assets

def fetch_land_stock_data() -> tuple[float, float] | None:
    logging.info("ランド社の株価を取得しています...")
    stock = yf.Ticker("8918.T")
    hist = stock.history(period="1d")
    if not hist.empty:
        close_price = hist['Close'].iloc[0]
        low_price = hist['Low'].iloc[0]
        logging.info(f"ランドの終値: {close_price}円, 安値: {low_price}円")
        return close_price, low_price
    logging.error("ランドの株価が取得できませんでした")
    return None

def place_order(session: requests.Session, ticker: str, volume: int, selling: bool) -> None:
    action = "売却" if selling else "購入"
    logging.info(f"ランドの株を{action}します: 銘柄コード={ticker}, 数量={volume}")
    ORDER_DATA = BASE_ORDER_DATA.copy()
    ORDER_DATA.update({
        'order_01[ticker_symbol]': ticker,
        'order_01[volume]': str(int(volume)),
        'order_01[selling]': 'true' if selling else 'false'
    })
    logging.info(f"送信する注文データ: {ORDER_DATA}")
    response = session.post(ORDER_URL, data=ORDER_DATA)
    if response.status_code == 200:
        logging.info("注文送信成功")
        logging.info(f"レスポンス内容: {response.text}")
    else:
        logging.error(f"注文送信失敗: ステータスコード={response.status_code}")
        logging.error(f"レスポンス内容: {response.text}")

def run_single_user(login_data: dict) -> None:
    log_divider()
    logging.info("プログラム開始")
    session = login_and_create_session(login_data)
    if not session:
        logging.error("セッションが作成できなかったため終了します")
        log_divider()
        return

    stock_data, total_assets = fetch_stock_data(session)
    stock_prices = fetch_land_stock_data()

    if not stock_prices:
        logging.error("株価データが取得できなかったため終了します")
        log_divider()
        return

    close_price, low_price = stock_prices

    logging.info("株式データを取得しました")
    logging.info(f"  - 保有株データ: {stock_data}")
    logging.info(f"  - 資産合計: {total_assets:,}円")

    logging.info("ランド社の株価を取得しました")
    logging.info(f"  - 終値: {close_price}円")
    logging.info(f"  - 安値: {low_price}円")

    if stock_data and close_price > low_price:
        logging.info("株価が上昇しています。保有株を売却します。")
        place_order(session, '8918', int(stock_data[0][2]), True)
    elif not stock_data and close_price == low_price:
        num_shares = total_assets // (low_price * 100)
        logging.info(f"株価が安値にあります。新たに{num_shares * 100}株購入します。")
        place_order(session, '8918', int(num_shares * 100), False)
    elif stock_data and close_price == low_price:
        logging.info("株価は安値のままですが、すでに保有しているため購入を見送ります。")
    elif not stock_data and close_price > low_price:
        logging.info("株価が上昇していますが、保有していないため売却できません。")
    else:
        logging.info("条件に一致しないため、何もしません。")

    logging.info("プログラム終了")
    log_divider()

def main() -> None:
    for user_data in USERS:
        run_single_user(user_data)

if __name__ == "__main__":
    main()
