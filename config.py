# 定数
LOGIN_URL = 'https://www.ssg.ne.jp/session'
ORDER_URL = 'https://www.ssg.ne.jp/orders/bulk'
LOGIN_SUCCESS_TEXT = (
    '<a class="el_btn el_btn__small el_btn__greenVer2 logoutBtn_sp" '
    'href="/logout" data-turbolinks="false">ログアウト</a>'
)
STOCK_DATA_URL = 'https://www.ssg.ne.jp/performances/team'

# ログインデータ
LOGIN_DATA = {
    'course_code': "57226",
    'course_password': "480362",
    'user_code': "0307",
    'user_password': "577163",
    'button': ''
}

# 注文データ
ORDER_DATA = {'limit': ''}
for i in range(1, 11):
    ORDER_DATA.update({
        f'order_{i:02}[ticker_symbol]': '',
        f'order_{i:02}[volume]': '',
        f'order_{i:02}[selling]': 'null'
    })
