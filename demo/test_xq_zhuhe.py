import easytrader

user = easytrader.use('xq')
user.prepare(
    cookies="device_id=24700f9f1986800ab4fcc880530dd0ed; s=c611jy83d1; bid=7130b0353c7fe2b0cac18d13ce0ba33e_kfhri08p; __utmz=1.1601009405.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); cookiesu=721609119310509; remember=1; xq_a_token=033322615e2b2708e6c80827868f32c360b7427c; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOjY1NjE2NTI1OTQsImlzcyI6InVjIiwiZXhwIjoxNjExNzExMjk2LCJjdG0iOjE2MDkyMTA4NjExNjksImNpZCI6ImQ5ZDBuNEFadXAifQ.Ci0VGpXOSvqLE2OOAOQYVUdclK44xdC1hhw2wfRW_owouECJgp89RstWExVvuopmAH_jEjNUxKNsyKXI8Dy4w4m8nDTqfKEDHAysyH-AOztVWdra74d0Ebspgdcn02UyfBaKBKY-qeaMn2jjNbVAreP1C9WrZwT5HkPMVyJTx62ASClAdt2PMfP9Eeu2baiGn2jDLHGp-1exroYyeggynCaRmbaYCsH4C-1sM_17Ljw6OmvF5FV_3cLY0NCSs7781MI-36hSa5KpgaGlCjqFNKq9GeYpX6ki2mNyp4rnqOn9bwRW8LQeawLuoYROywViDwVLiGDV8PSvrYGsWVtjGQ; xqat=033322615e2b2708e6c80827868f32c360b7427c; xq_r_token=c5258ce8ff96caa5a21bea59443ba531cd3d7a63; xq_is_login=1; u=6561652594; Hm_lvt_1db88642e346389874251b5a1eded6e3=1609827151,1609827202,1609827252,1609827306; acw_tc=2760820116098333450666290ecfcebc35f0d9d101be6dd73ad4ace7659238; is_overseas=0; __utma=1.1792023165.1601009405.1609724608.1609833358.55; __utmc=1; __utmt=1; __utmb=1.2.10.1609833358; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1609833427",
    # portfolio_code="ZH2394354",
    # portfolio_code="ZH2342584",
    portfolio_code="ZH2348461",
    portfolio_market="cn",
)

# 跟踪雪球组合
xq_follower = easytrader.follower('xq')
xq_follower.login(
    cookies='device_id=24700f9f1986800ab4fcc880530dd0ed; s=c611jy83d1; bid=7130b0353c7fe2b0cac18d13ce0ba33e_kfhri08p; __utmz=1.1601009405.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); cookiesu=721609119310509; remember=1; xq_a_token=033322615e2b2708e6c80827868f32c360b7427c; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOjY1NjE2NTI1OTQsImlzcyI6InVjIiwiZXhwIjoxNjExNzExMjk2LCJjdG0iOjE2MDkyMTA4NjExNjksImNpZCI6ImQ5ZDBuNEFadXAifQ.Ci0VGpXOSvqLE2OOAOQYVUdclK44xdC1hhw2wfRW_owouECJgp89RstWExVvuopmAH_jEjNUxKNsyKXI8Dy4w4m8nDTqfKEDHAysyH-AOztVWdra74d0Ebspgdcn02UyfBaKBKY-qeaMn2jjNbVAreP1C9WrZwT5HkPMVyJTx62ASClAdt2PMfP9Eeu2baiGn2jDLHGp-1exroYyeggynCaRmbaYCsH4C-1sM_17Ljw6OmvF5FV_3cLY0NCSs7781MI-36hSa5KpgaGlCjqFNKq9GeYpX6ki2mNyp4rnqOn9bwRW8LQeawLuoYROywViDwVLiGDV8PSvrYGsWVtjGQ; xqat=033322615e2b2708e6c80827868f32c360b7427c; xq_r_token=c5258ce8ff96caa5a21bea59443ba531cd3d7a63; xq_is_login=1; u=6561652594; Hm_lvt_1db88642e346389874251b5a1eded6e3=1609827151,1609827202,1609827252,1609827306; acw_tc=2760820116098333450666290ecfcebc35f0d9d101be6dd73ad4ace7659238; is_overseas=0; __utma=1.1792023165.1601009405.1609724608.1609833358.55; __utmc=1; __utmt=1; __utmb=1.2.10.1609833358; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1609833427')
# 总金额50万 下单时浮动2个点
xq_follower.follow(user,
                   'ZH974199', # 威廉
                   total_assets=1180000,
                   slippage=0.02,
                   trade_cmd_expire_seconds=120,
                   # adjust_sell=True,
                   track_interval=5,
                   cmd_cache=True
                   )
