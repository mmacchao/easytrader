balance = {'资金余额': 440100.0, '可用金额': 450000.72, '可取金额': 440100.0, '总资产': 450000.72}

position = {'证券代码': '002385', '证券名称': '大北农', '股票余额': 4500, '可用余额': 0, '冻结数量': 4500, '盈亏': 309.93, '成本价': 11.271,
            '盈亏比例(%)': 0.612, '市价': 11.34, '市值': 51030.0, '交易市场': '深圳Ａ股', '股东帐户': 258950267, '汇率': 1.0, '成本价港币': 11.271,
            '买入成本价港币': 0.0, '买入在途数量': 0, '卖出在途数量': 0, 'Unnamed: 17': ''}

# 策略发出的值
transcation = {'id': 233724016, 'rebalancing_id': 87539127, 'stock_id': 1000648, 'stock_name': '中航重机',
               'stock_symbol': 'SH600765', 'volume': 0.0, 'price': 24.37, 'net_value': 0.0, 'weight': 0.0,
               'target_weight': 0.0, 'prev_weight': 4.96, 'prev_target_weight': 4.96, 'prev_weight_adjusted': 4.94,
               'prev_volume': 0.02124333, 'prev_price': 24.4, 'prev_net_value': 0.51833725, 'proactive': True,
               'created_at': 1610417751751, 'updated_at': 1610417751751, 'target_volume': 0.0,
               'prev_target_volume': 0.02125884, 'datetime': datetime.datetime(2021, 1, 12, 10, 15, 51),
               'stock_code': 'sh600765', 'action': 'sell', 'amount': 0}

# 程序构建的交易命令
trade_cmd = {'strategy': 'ZH974199', 'strategy_name': '一蓑烟雨任平生', 'action': 'sell', 'stock_code': 'sh600765',
             'amount': 0, 'price': 24.37, 'datetime': datetime.datetime(2021, 1, 12, 10, 15, 51)}

# // weight是5的倍数，且diff小于3.5，则认为是无效调仓
# // weight不是5的倍数
# // 进行下面的判断
# //  判断账户的仓位realWeight是否大于weight，
# //  如果realWeight >= weight，无效调仓
# //  如果realWeight < weight，则weight先往上靠，得到新的5的倍数仓位adjustWeight，实际调仓为adjustWeight - realWeight
weight = 15
diff = 5
# weight是5的倍数且diffd大于3.5，才是
if weight % 5 == 0 and diff < 3.5:
    print(0)
if weight % 5 != 0:
    realWeight = round(position['市值'] / balance['总资产'], 2)
    if realWeight >= weight:
        print(0)
    else:
        adjustWeight = (weight // 5 + 1) * 5
        diff = adjustWeight - realWeight
        print(diff)
print(diff)
