from aquant.lhb import classify_seat


def test_institution():
    assert classify_seat("机构专用") == ("inst", None)


def test_northbound():
    assert classify_seat("深股通专用") == ("north", None)
    assert classify_seat("沪股通专用") == ("north", None)


def test_hotmoney_named():
    t, name = classify_seat("中国银河证券股份有限公司绍兴证券营业部")
    # 绍兴 = 章盟主系（示例词典命中）
    assert t == "hotmoney"
    assert name


def test_normal():
    assert classify_seat("平安证券股份有限公司某某路证券营业部") == ("normal", None)
