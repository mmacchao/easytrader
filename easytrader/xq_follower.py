# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

import json
import re
from datetime import datetime
from numbers import Number
from threading import Thread

from easytrader.follower import BaseFollower
from easytrader.log import logger
from easytrader.utils.misc import parse_cookies_str


class XueQiuFollower(BaseFollower):
    LOGIN_PAGE = "https://www.xueqiu.com"
    LOGIN_API = "https://xueqiu.com/snowman/login"
    TRANSACTION_API = "https://xueqiu.com/cubes/rebalancing/history.json"
    PORTFOLIO_URL = "https://xueqiu.com/p/"
    WEB_REFERER = "https://www.xueqiu.com"

    def __init__(self):
        super().__init__()
        self._adjust_sell = None
        self._adjust_buy = None
        self._users = None

    def login(self, user=None, password=None, **kwargs):
        """
        雪球登陆， 需要设置 cookies
        :param cookies: 雪球登陆需要设置 cookies， 具体见
            https://smalltool.github.io/2016/08/02/cookie/
        :return:
        """
        cookies = kwargs.get("cookies")
        if cookies is None:
            raise TypeError(
                "雪球登陆需要设置 cookies， 具体见" "https://smalltool.github.io/2016/08/02/cookie/"
            )
        headers = self._generate_headers()
        self.s.headers.update(headers)

        self.s.get(self.LOGIN_PAGE)

        cookie_dict = parse_cookies_str(cookies)
        self.s.cookies.update(cookie_dict)

        logger.info("登录成功")

    def follow(  # type: ignore
            self,
            users,
            strategies,
            total_assets=10000,
            initial_assets=None,
            adjust_sell=False,
            adjust_buy=False,
            track_interval=10,
            trade_cmd_expire_seconds=120,
            cmd_cache=True,
            slippage: float = 0.0,
    ):
        """跟踪 joinquant 对应的模拟交易，支持多用户多策略
        :param users: 支持 easytrader 的用户对象，支持使用 [] 指定多个用户
        :param strategies: 雪球组合名, 类似 ZH123450
        :param total_assets: 雪球组合对应的总资产， 格式 [组合1对应资金, 组合2对应资金]
            若 strategies=['ZH000001', 'ZH000002'],
                设置 total_assets=[10000, 10000], 则表明每个组合对应的资产为 1w 元
            假设组合 ZH000001 加仓 价格为 p 股票 A 10%,
                则对应的交易指令为 买入 股票 A 价格 P 股数 1w * 10% / p 并按 100 取整
        :param adjust_sell: 是否根据用户的实际持仓数调整卖出股票数量，
            当卖出股票数大于实际持仓数时，调整为实际持仓数。目前仅在银河客户端测试通过。
            当 users 为多个时，根据第一个 user 的持仓数决定
        :type adjust_sell: bool
        :param initial_assets: 雪球组合对应的初始资产,
            格式 [ 组合1对应资金, 组合2对应资金 ]
            总资产由 初始资产 × 组合净值 算得， total_assets 会覆盖此参数
        :param track_interval: 轮训模拟交易时间，单位为秒
        :param trade_cmd_expire_seconds: 交易指令过期时间, 单位为秒
        :param cmd_cache: 是否读取存储历史执行过的指令，防止重启时重复执行已经交易过的指令
        :param slippage: 滑点，0.0 表示无滑点, 0.05 表示滑点为 5%
        """
        super().follow(
            users=users,
            strategies=strategies,
            track_interval=track_interval,
            trade_cmd_expire_seconds=trade_cmd_expire_seconds,
            cmd_cache=cmd_cache,
            slippage=slippage,
        )

        self._adjust_sell = adjust_sell
        self._adjust_buy = adjust_buy

        self._users = self.warp_list(users)

        strategies = self.warp_list(strategies)
        total_assets = self.warp_list(total_assets)
        initial_assets = self.warp_list(initial_assets)

        if cmd_cache:
            self.load_expired_cmd_cache()

        self.start_trader_thread(self._users, trade_cmd_expire_seconds)

        for strategy_url, strategy_total_assets, strategy_initial_assets in zip(
            strategies, total_assets, initial_assets
        ):
            assets = self.calculate_assets(
                strategy_url, strategy_total_assets, strategy_initial_assets
            )
            try:
                strategy_id = self.extract_strategy_id(strategy_url)
                strategy_name = self.extract_strategy_name(strategy_url)
            except:
                logger.error("抽取交易id和策略名失败, 无效模拟交易url: %s", strategy_url)
                raise
            strategy_worker = Thread(
                target=self.track_strategy_worker,
                args=[strategy_id, strategy_name],
                kwargs={"interval": track_interval, "assets": assets},
            )
            strategy_worker.start()
            logger.info("开始跟踪策略: %s", strategy_name)

    def calculate_assets(self, strategy_url, total_assets=None, initial_assets=None):
        # 都设置时优先选择 total_assets
        if total_assets is None and initial_assets is not None:
            net_value = self._get_portfolio_net_value(strategy_url)
            total_assets = initial_assets * net_value
        if total_assets is None and initial_assets is None:
            user = self._users[0]
            total_assets = user.balance["总资产"]
        if not isinstance(total_assets, Number):
            raise TypeError("input assets type must be number(int, float)")
        if total_assets < 1e3:
            raise ValueError("雪球总资产不能小于1000元，当前预设值 {}".format(total_assets))

        return total_assets

    @staticmethod
    def extract_strategy_id(strategy_url):
        return strategy_url

    def extract_strategy_name(self, strategy_url):
        base_url = "https://xueqiu.com/cubes/nav_daily/all.json?cube_symbol={}"
        url = base_url.format(strategy_url)
        rep = self.s.get(url)
        info_index = 0
        return rep.json()[info_index]["name"]

    def extract_transactions(self, history):
        if history["count"] <= 0:
            return []
        rebalancing_index = 0
        raw_transactions = history["list"][rebalancing_index]["rebalancing_histories"]
        transactions = []
        for transaction in raw_transactions:
            if transaction["price"] is None:
                logger.info("该笔交易无法获取价格，疑似未成交，跳过。交易详情: %s", transaction)
                continue
            transactions.append(transaction)

        return transactions

    # 仅测试用
    # def extract_transactions(self, history):
    #     if history["count"] <= 0:
    #         return []
    #     transactions = []
    #     for item in history["list"]:
    #         # rebalancing_index = 0
    #         raw_transactions = item["rebalancing_histories"]
    #         for transaction in raw_transactions:
    #             if transaction["price"] is None:
    #                 logger.info("该笔交易无法获取价格，疑似未成交，跳过。交易详情: %s", transaction)
    #                 continue
    #             transactions.append(transaction)
    #     return transactions

    def create_query_transaction_params(self, strategy):
        params = {"cube_symbol": strategy, "page": 1, "count": 1}
        return params

    # noinspection PyMethodOverriding
    def none_to_zero(self, data):
        if data is None:
            return 0
        return data

    # noinspection PyMethodOverriding
    def project_transactions(self, transactions, assets):
        for transaction in transactions:
            weight_diff = self.none_to_zero(transaction["weight"]) - self.none_to_zero(
                transaction["prev_weight_adjusted"]
            )

            initial_amount = abs(weight_diff) / 100 * assets / transaction["price"]

            transaction["datetime"] = datetime.fromtimestamp(
                transaction["created_at"] // 1000
            )

            transaction["stock_code"] = transaction["stock_symbol"].lower()

            transaction["action"] = "buy" if weight_diff > 0 else "sell"

            transaction["amount"] = int(round(initial_amount, -2))

            if transaction["action"] == "sell" and self._adjust_sell:
                transaction["amount"] = self._adjust_sell_amount(
                    transaction["stock_code"], transaction["amount"], transaction, assets
                )
            if transaction["action"] == "buy" and self._adjust_buy:
                transaction["amount"] = self._adjust_buy_amount(
                    transaction, transaction["stock_code"], transaction["amount"], transaction["price"], assets
                )

    def _adjust_sell_amount(self, stock_code, amount, transaction, assets):
        """
        根据实际持仓值计算雪球卖出股数
          因为雪球的交易指令是基于持仓百分比，在取近似值的情况下可能出现不精确的问题。
        导致如下情况的产生，计算出的指令为买入 1049 股，取近似值买入 1000 股。
        而卖出的指令计算出为卖出 1051 股，取近似值卖出 1100 股，超过 1000 股的买入量，
        导致卖出失败
        :param stock_code: 证券代码
        :type stock_code: str
        :param amount: 卖出股份数
        :type amount: int
        :return: 考虑实际持仓之后的卖出股份数
        :rtype: int
        """
        if amount == 0:
            return 0
        stock_code = stock_code[-6:]
        if stock_code == "511880":
            return 0
        weight = self.none_to_zero(transaction['weight'])
        prevWeight = self.none_to_zero(transaction["prev_weight_adjusted"])
        # startWeight = round(self.none_to_zero(transaction["prev_weight"]))
        diff = prevWeight - weight
        # 5.5 -> 5, 6 -> 5
        if weight % 5 == 0 and diff < 3.5:
            return 0

        try:
            user = self._users[0]
            position = user.position
            stock = next(s for s in position if s["证券代码"] == stock_code)
        except StopIteration:
            logger.info("卖：指令时间：%s 根据持仓调整 %s 卖出额，发现未持有股票 %s, 调仓无效。", transaction["datetime"], transaction["stock_name"],
                        transaction["stock_name"])
            return 0

        available_amount = stock["可用余额"]
        totalMoney = stock["市值"]
        # 策略调仓到0，那直接全买

        if self.none_to_zero(transaction['weight']) == 0:
            # 当天不可卖仓位
            leftWeight = round(stock["冻结数量"] * stock["市价"] / assets, 2)
            logger.info("卖：指令时间：%s 股票：%s 策略从 %s -> %s, 清空股票, 账户当前股票仓位为 %s， 不可买仓位为 %s", transaction["datetime"],
                        transaction["stock_name"], transaction["prev_target_weight"], transaction["weight"],
                        round(totalMoney / assets * 100, 2), leftWeight)
            return available_amount
        if available_amount >= amount:
            currentWeight = round(totalMoney/assets * 100, 2)
            diff = self.none_to_zero(transaction["prev_target_weight"]) - self.none_to_zero(transaction["weight"])
            logger.info("卖：指令时间：%s 股票：%s 策略从 %s -> %s, 账户当前股票仓位为 %s, 卖出仓位 %s, 剩余仓位 %s",
                        transaction["datetime"],
                        transaction["stock_name"],
                        transaction["prev_target_weight"],
                        transaction["weight"],
                        currentWeight,
                        diff,
                        currentWeight - diff )
            return amount // 100 * 100
        adjust_amount = available_amount // 100 * 100
        logger.info(
            "卖：指令时间：%s 股票 %s 实际可用余额 %s, 指令卖出股数为 %s, 调整为 %s。",
            transaction["datetime"],
            transaction["stock_name"],
            available_amount,
            amount,
            adjust_amount
        )
        return adjust_amount

    def _adjust_buy_amount(self, transaction, stock_code, amount, price, assets):
        if amount == 0:
            return amount
        price = price * (1 + self.slippage)
        stock_code = stock_code[-6:]
        # 511880这个是货币基金，买入这个相当于无效调仓
        if stock_code == "511880":
            return 0
        # user = self._users[0]

        # weight是5的倍数，且diff小于3.5，则认为是无效调仓
        # weight不是5的倍数
        # 进行下面的判断
        #  判断账户的仓位realWeight是否大于weight，
        #  如果realWeight >= weight，无效调仓
        #  如果realWeight < weight，则weight先往上靠，得到新的5的倍数仓位adjustWeight，实际调仓为adjustWeight - realWeight
        weight = self.none_to_zero(transaction['weight'])
        prevWeight = self.none_to_zero(transaction["prev_weight_adjusted"])
        startWeight = round(self.none_to_zero(transaction["prev_weight"]))
        diff = weight - prevWeight
        # diff小于3.5，且不是调仓到5的整数倍，大概率就是微调，直接放弃
        if weight % 5 == 0 and diff < 3.5:
            # logger.info("买：指令时间：%s 股票名称 %s: 策略调仓从 %s 调到 %s, 调仓幅度 %s, 小于3.5丢弃。", transaction["datetime"], transaction["stock_name"], prevWeight,
            #             weight, diff)
            return 0

        # 0 -> 1, 5 -> 6
        if startWeight % 5 == 0 and weight % 5 != 0 and diff < 4.5:
            diff = 5
            amount = round(diff / 100 * assets / price, -2)
            logger.info("买：指令时间：%s 股票名称 %s: 策略从 %s -> %s 改为调仓5，调整后的买入数量为：%s, 买入金额为 %s",
                        transaction["datetime"], transaction["stock_name"], prevWeight, weight, amount, round(amount * price))
            return amount

        if weight % 5 != 0 and startWeight % 5 != 0:
            logger.info("买：指令时间：%s 股票名称 %s: 策略调仓从 %s -> %s, 放弃调仓",
                        transaction["datetime"], transaction["stock_name"], prevWeight,
                        weight)
            return 0

        # 0 -> 5, 11 -> 15, 11 -> 20
        if weight % 5 == 0 and diff >= 4:
            logger.info("买：指令时间：%s 股票名称 %s: 策略从 %s -> %s, 按实际值进行调仓",
                        transaction["datetime"], transaction["stock_name"], prevWeight, weight)

        return amount

        # 0 -> 5, 0 -> 10, 10 -> 15, 10 -> 20 都不会进来，直接就买了
        # 10 -> 11, 11 -> 15, 11 -> 16, 11 -> 20 都要进来和实际值比较一下

        # if weight % 5 != 0 or (startWeight % 5 != 0 and diff >= 4):
        #     try:
        #         position = user.position
        #         stock = next(s for s in position if s["证券代码"] == stock_code)
        #         # 有持仓
        #         realWeight = round(stock['市值'] / assets, 2) * 100
        #         if realWeight >= weight:
        #             logger.info("买：指令时间：%s 股票名称 %s: 策略从 %s 调仓到 %s,策略调仓幅度 %s, 已有持仓为 %s, 已有仓位大于策略目标调仓, 放弃调仓。",
        #                         transaction["datetime"], stock['证券名称'], prevWeight, weight, diff, realWeight)
        #             return 0
        #         else:
        #             # 以5为台阶往上靠
        #             adjustWeight = (weight // 5 + 1) * 5
        #             diff = adjustWeight - realWeight
        #             # 防止未知原因导致的调仓过大
        #             diff = 10 if diff > 10 else diff
        #             # 这个地方可能因为前面没有获取到最新持仓，导致多次产生过大错误调仓
        #             # 从15调整到20以下，一般就是调仓5
        #             # if transaction['prev_target_weight'] % 5 == 0:
        #             #     diff = 5 if planDiff > 7.5 else planDiff
        #             #     logger.info("股票名称 %s: 已有持仓为 %s, 目标调仓为 %s, 计划调仓是 %s, 调整为 %s", stock['证券名称'], realWeight, weight, planDiff, diff)
        #             # else:
        #             #     # 从15以上，20以下开始调仓，就不用调了
        #             #     logger.info("调仓起点为 %s, 不是5的倍数, 放弃此次调仓", transaction['prev_target_weight'])
        #             #     return 0
        #     except StopIteration:
        #         # 没有相关持仓
        #         diff = (diff // 5 + 1) * 5
        #         logger.info("买：指令时间：%s 股票名称：%s, 策略从 %s 调仓到 %s 策略调仓幅度 %s, 原有持仓为0，调整为 %s。",
        #                     transaction["datetime"],
        #                     transaction["stock_name"],
        #                     prevWeight, weight, weight - prevWeight,
        #                     diff)
        #     amount = diff * assets / price // 100 // 100 * 100

        # if weight % 5 == 0 and diff >= 4:
        #     logger.info("买：指令时间：%s 股票名称 %s: 策略从 %s 调仓到 %s,策略调仓幅度 %s, 调仓幅度大于4且目标仓位是5的倍数, 为节约时间，不进行账户仓位查询了",
        #                 transaction["datetime"], transaction["stock_name"], prevWeight, weight, diff)

        # 测试把可用余额这一段去了，看下能不能加快交易进度
        # can_use_balance = user.balance["可用金额"]
        # buy_balance = amount * price
        # if can_use_balance < buy_balance:
        #     amount = int(can_use_balance / price) // 100 * 100
        #     real_buy_balance = amount * price
        #     logger.info("买：指令时间：%s 股票名称：%s 账户实际可用余额 %s, 指令买入金额为 %s, 调整为买入 %s。", transaction["datetime"], transaction["stock_name"],
        #                 can_use_balance, buy_balance, real_buy_balance)
        # return amount

    def _get_portfolio_info(self, portfolio_code):
        """
        获取组合信息
        """
        url = self.PORTFOLIO_URL + portfolio_code
        portfolio_page = self.s.get(url)
        match_info = re.search(r"(?<=SNB.cubeInfo = ).*(?=;\n)", portfolio_page.text)
        if match_info is None:
            raise Exception("cant get portfolio info, portfolio url : {}".format(url))
        try:
            portfolio_info = json.loads(match_info.group())
        except Exception as e:
            raise Exception("get portfolio info error: {}".format(e))
        return portfolio_info

    def _get_portfolio_net_value(self, portfolio_code):
        """
        获取组合信息
        """
        portfolio_info = self._get_portfolio_info(portfolio_code)
        return portfolio_info["net_value"]
