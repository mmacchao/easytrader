import easytrader
from easytrader import refresh_strategies

user = easytrader.use('htzq_client')

# refresh_btn_index 指的是刷新按钮在工具栏的排序，默认为第四个，根据客户端实际情况调整
user.refresh_strategy = refresh_strategies.Toolbar(refresh_btn_index=4)
user.prepare(
    user="",
    password="",
    exe_path=r'C:\海通证券委托\xiadan.exe',
    comm_password=""
)

# 跟踪雪球组合
xq_follower = easytrader.follower('xq')
xq_follower.login(cookies='')
# 总金额50万 下单时浮动2个点
xq_follower.follow(
    user,
    'ZH974199', # 威廉
    # 'ZH2358246', # 君临
    # 'ZH2342584',  # 生叔
    # total_assets=1000,
    total_assets=600000,
    initial_assets=None,
    # initial_assets=1000000,
    track_interval=3,
    slippage=0.02,
    adjust_sell=True,
    adjust_buy=True,
    # send_interval=5,
    trade_cmd_expire_seconds=30,
    cmd_cache=True
)