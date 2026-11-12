# -*- coding: utf-8 -*-
"""演示数据：全部客户、订单和政策均为虚构。"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List


POLICIES: List[Dict[str, Any]] = [
    {
        "id": "P-LOG-01",
        "title": "物流停滞处理规范",
        "section": "物流服务 / 3.2",
        "updated_at": "2026-10-18",
        "keywords": "物流 快递 停滞 延迟 没更新 转运 派送 签收 发货",
        "content": (
            "运输中断或超过预计时效24小时没有新轨迹时，客服应先核实最新物流节点，"
            "向客户说明可确认的事实，并在24小时内给出下一次反馈时间。未确认丢件前，"
            "不得直接承诺退款或赔付。"
        ),
    },
    {
        "id": "P-SHIP-01",
        "title": "发货与缺货处理规范",
        "section": "履约服务 / 2.4",
        "updated_at": "2026-09-30",
        "keywords": "发货 缺货 补发 拆单 仓库 预售 延时 揽收",
        "content": (
            "订单超过承诺发货时间仍未揽收时，应先向仓库确认库存与排期。存在缺货时，"
            "可提供等待、换款或取消三个选项；任何选项都需要客户确认，不应代替客户决定。"
        ),
    },
    {
        "id": "P-RET-01",
        "title": "七日无理由退货规范",
        "section": "售后服务 / 4.1",
        "updated_at": "2026-10-02",
        "keywords": "退货 退款 七天 无理由 不合适 拆封 吊牌 二次销售",
        "content": (
            "签收后七日内且商品保持完好、不影响二次销售，可申请无理由退货。定制、"
            "鲜活易腐、已激活数字商品以及明确标注不适用的商品除外。退款在仓库验收后处理。"
        ),
    },
    {
        "id": "P-DAM-01",
        "title": "破损与缺件处理规范",
        "section": "售后服务 / 4.3",
        "updated_at": "2026-10-20",
        "keywords": "破损 损坏 碎了 漏液 少件 缺件 空盒 包装 照片 换新 补发",
        "content": (
            "客户反馈破损或缺少配件时，应请客户提供外包装、面单和商品问题照片。核验后"
            "优先提供补发或换新；无法补发时可协商退货退款。未经审批不得直接承诺现金赔偿。"
        ),
    },
    {
        "id": "P-INV-01",
        "title": "电子发票开具规范",
        "section": "订单服务 / 5.2",
        "updated_at": "2026-08-16",
        "keywords": "发票 开票 抬头 税号 邮箱 电子票 红冲 重开",
        "content": (
            "订单完成且未申请退款后，可按客户提供的抬头、税号和邮箱开具电子发票。"
            "当月发票信息有误可申请红冲后重开；跨月处理需由财务审核，不得承诺固定完成时间。"
        ),
    },
    {
        "id": "P-CAN-01",
        "title": "订单取消与拦截规范",
        "section": "履约服务 / 2.6",
        "updated_at": "2026-10-08",
        "keywords": "取消 不想要 别发 未发货 拦截 已发货 拒收 退回",
        "content": (
            "订单未进入拣货前可尝试取消；已发货订单无法直接取消，应建议客户拒收或在签收后"
            "按退货流程处理。客服只能提交拦截申请，不得承诺一定拦截成功。"
        ),
    },
    {
        "id": "P-ESC-01",
        "title": "投诉与升级处理规范",
        "section": "风险服务 / 1.3",
        "updated_at": "2026-09-12",
        "keywords": "投诉 曝光 12315 律师 工商 差评 骗子 维权 监管",
        "content": (
            "出现投诉、监管、媒体曝光或法律威胁时，应立即停止自动化回复并转人工升级。"
            "先确认事实和客户核心诉求，不作事实之外的责任认定或赔偿承诺。"
        ),
    },
    {
        "id": "P-COMP-01",
        "title": "赔偿与补偿授权边界",
        "section": "风险服务 / 1.5",
        "updated_at": "2026-10-25",
        "keywords": "赔偿 补偿 赔钱 红包 优惠券 金额 现金 赔付 损失",
        "content": (
            "一线客服不得直接承诺现金赔偿。涉及较高订单金额、明显损失或多次沟通未解决时，"
            "应记录证据并提交主管审批。补偿方案须经授权后告知客户。"
        ),
    },
    {
        "id": "P-PRI-01",
        "title": "客户隐私与身份核验规范",
        "section": "安全合规 / 1.1",
        "updated_at": "2026-09-01",
        "keywords": "隐私 身份证 银行卡 密码 验证码 地址 电话 手机号 核验",
        "content": (
            "客服不得索取短信验证码、账户密码或完整银行卡信息。查询订单只使用订单号或平台内"
            "已绑定的联系渠道，展示时对手机号、地址等个人信息进行脱敏。"
        ),
    },
]


ORDERS: Dict[str, Dict[str, Any]] = {
    "SY20261108001": {
        "order_id": "SY20261108001",
        "items": "云感保温杯 · 雾蓝",
        "amount": 129.0,
        "status": "运输中",
        "logistics": "11月10日 22:14 到达上海转运中心，之后暂无更新",
        "eta": "11月12日",
        "customer_tier": "普通会员",
    },
    "SY20261109012": {
        "order_id": "SY20261109012",
        "items": "桌面收纳套装 · 奶油白",
        "amount": 269.0,
        "status": "已签收",
        "logistics": "11月11日 15:32 已由本人签收",
        "eta": "已签收",
        "customer_tier": "银卡会员",
    },
    "SY20261105036": {
        "order_id": "SY20261105036",
        "items": "手冲咖啡礼盒",
        "amount": 358.0,
        "status": "已签收",
        "logistics": "11月07日 10:08 已由门卫代收",
        "eta": "已签收",
        "customer_tier": "银卡会员",
    },
    "SY20261111008": {
        "order_id": "SY20261111008",
        "items": "轻量通勤双肩包 · 黑色",
        "amount": 399.0,
        "status": "待发货",
        "logistics": "仓库已接单，尚未揽收",
        "eta": "11月13日前发货",
        "customer_tier": "普通会员",
    },
    "SY20261110021": {
        "order_id": "SY20261110021",
        "items": "香氛扩香礼盒",
        "amount": 319.0,
        "status": "已发货",
        "logistics": "11月12日 08:20 已揽收，准备发往杭州分拨中心",
        "eta": "11月14日",
        "customer_tier": "金卡会员",
    },
    "SY20261106017": {
        "order_id": "SY20261106017",
        "items": "陶瓷马克杯两只装",
        "amount": 188.0,
        "status": "已签收",
        "logistics": "11月08日 18:40 已签收",
        "eta": "已签收",
        "customer_tier": "普通会员",
    },
    "SY20261103029": {
        "order_id": "SY20261103029",
        "items": "折叠露营桌",
        "amount": 599.0,
        "status": "已签收",
        "logistics": "11月06日 12:05 已签收",
        "eta": "已签收",
        "customer_tier": "金卡会员",
    },
    "SY20261111045": {
        "order_id": "SY20261111045",
        "items": "棉麻床品四件套",
        "amount": 529.0,
        "status": "已签收",
        "logistics": "11月12日 09:16 已签收",
        "eta": "已签收",
        "customer_tier": "普通会员",
    },
    "SY20261107033": {
        "order_id": "SY20261107033",
        "items": "便携榨汁杯",
        "amount": 219.0,
        "status": "已签收",
        "logistics": "11月09日 14:28 已签收",
        "eta": "已签收",
        "customer_tier": "普通会员",
    },
    "SY20261112002": {
        "order_id": "SY20261112002",
        "items": "旅行收纳袋六件套",
        "amount": 159.0,
        "status": "待发货",
        "logistics": "订单已进入仓库队列",
        "eta": "11月14日前发货",
        "customer_tier": "普通会员",
    },
}


DEMO_TICKETS: List[Dict[str, Any]] = [
    {
        "id": "T-1001",
        "order_id": "SY20261108001",
        "customer": "林女士",
        "channel": "淘宝",
        "created_at": "11月12日 09:42",
        "message": "你好，我的保温杯从昨天开始物流就不动了，预计今天到但一直没派送，能帮我看一下吗？",
        "status": "待处理",
        "priority": "普通",
    },
    {
        "id": "T-1002",
        "order_id": "SY20261106017",
        "customer": "周先生",
        "channel": "抖店",
        "created_at": "11月12日 09:58",
        "message": "杯子拆开发现两只都碎了，外包装也瘪了。我拍好照片了，希望尽快换新。",
        "status": "待处理",
        "priority": "较高",
    },
    {
        "id": "T-1003",
        "order_id": "SY20261111008",
        "customer": "陈女士",
        "channel": "京东",
        "created_at": "11月12日 10:16",
        "message": "公司报销要用，发票抬头和税号应该怎么填？电子票多久能开好？",
        "status": "待处理",
        "priority": "普通",
    },
    {
        "id": "T-1004",
        "order_id": "SY20261109012",
        "customer": "赵女士",
        "channel": "小红书",
        "created_at": "11月12日 10:35",
        "message": "收纳盒尺寸不合适，外包装还在，可以七天无理由退货吗？",
        "status": "待处理",
        "priority": "普通",
    },
    {
        "id": "T-1005",
        "order_id": "SY20261110021",
        "customer": "许先生",
        "channel": "淘宝",
        "created_at": "11月12日 10:47",
        "message": "我刚下单了香氛礼盒，但地址填错了，现在还能取消吗？",
        "status": "待处理",
        "priority": "较高",
    },
    {
        "id": "T-1006",
        "order_id": "SY20261103029",
        "customer": "何女士",
        "channel": "12315",
        "created_at": "11月12日 11:02",
        "message": "露营桌桌腿断了，我已经联系两次都没有解决。今天必须给我赔偿，不然我就投诉并曝光。",
        "status": "待处理",
        "priority": "紧急",
    },
    {
        "id": "T-1007",
        "order_id": "SY20261107033",
        "customer": "唐先生",
        "channel": "京东",
        "created_at": "11月12日 11:20",
        "message": "榨汁杯盒子里面没有说明书，杯盖也少了一个配件，这个怎么补发？",
        "status": "待处理",
        "priority": "普通",
    },
    {
        "id": "T-1008",
        "order_id": "SY20261112002",
        "customer": "吴女士",
        "channel": "淘宝",
        "created_at": "11月12日 11:31",
        "message": "还没有揽收，我现在不想要了，麻烦帮我取消，别发了。",
        "status": "待处理",
        "priority": "普通",
    },
    {
        "id": "T-1009",
        "order_id": "SY20261105036",
        "customer": "王女士",
        "channel": "微信小店",
        "created_at": "11月12日 11:45",
        "message": "咖啡礼盒里面有一个玻璃瓶碎了，订单金额比较高，我不希望来回折腾，能直接给我换一套吗？",
        "status": "已转人工",
        "priority": "较高",
    },
    {
        "id": "T-1010",
        "order_id": "SY20261111045",
        "customer": "孙女士",
        "channel": "天猫",
        "created_at": "11月12日 12:03",
        "message": "床品四件套已经洗过一次，但颜色和页面差很多，还能退吗？",
        "status": "已完成",
        "priority": "普通",
    },
    {
        "id": "T-1011",
        "order_id": "SY20261109012",
        "customer": "高先生",
        "channel": "淘宝",
        "created_at": "11月12日 12:18",
        "message": "发票上的公司名称写错了一个字，能改成新的抬头重开吗？",
        "status": "已完成",
        "priority": "普通",
    },
    {
        "id": "T-1012",
        "order_id": "SY20261106017",
        "customer": "梁女士",
        "channel": "抖音",
        "created_at": "11月12日 12:26",
        "message": "杯子不是坏了，但我拆封后发现颜色不喜欢，已经过了六天，还能退货吗？",
        "status": "待处理",
        "priority": "普通",
    },
]


INTENT_POLICIES = {
    "logistics_delay": ["P-LOG-01"],
    "damage_missing": ["P-DAM-01", "P-COMP-01"],
    "invoice": ["P-INV-01"],
    "return_refund": ["P-RET-01"],
    "cancel_order": ["P-CAN-01"],
    "complaint_escalation": ["P-ESC-01", "P-COMP-01"],
}


EVALUATION_BASES = [
    {
        "intent": "logistics_delay",
        "risk": False,
        "message": "快递两天没有新轨迹了，也没有派送，麻烦帮我查一下物流。",
    },
    {
        "intent": "logistics_delay",
        "risk": False,
        "message": "页面写今天送达，但是快递一直停在转运中心，什么时候能处理？",
    },
    {
        "intent": "logistics_delay",
        "risk": False,
        "message": "已经显示签收了，可是我本人没有收到，小区驿站也找不到。",
    },
    {
        "intent": "logistics_delay",
        "risk": False,
        "message": "物流显示已揽收但半天没更新，想确认是不是丢件了。",
    },
    {
        "intent": "damage_missing",
        "risk": False,
        "message": "商品外包装破损，里面的杯子碎了，我可以提供照片。",
    },
    {
        "intent": "damage_missing",
        "risk": False,
        "message": "盒子里少了一个配件，没有看到说明书和充电线。",
    },
    {
        "intent": "damage_missing",
        "risk": True,
        "message": "礼盒里的玻璃瓶漏液了，订单金额比较高，希望按流程尽快换新。",
    },
    {
        "intent": "damage_missing",
        "risk": False,
        "message": "收到的衣服有一道线头，吊牌还在，我想换一件。",
    },
    {
        "intent": "invoice",
        "risk": False,
        "message": "需要开电子发票，抬头和税号应该怎么提交？",
    },
    {
        "intent": "invoice",
        "risk": False,
        "message": "发票上的公司名称写错了，能不能红冲以后重开？",
    },
    {
        "intent": "invoice",
        "risk": False,
        "message": "订单已经签收，报销需要发票，多久可以发到邮箱？",
    },
    {
        "intent": "invoice",
        "risk": False,
        "message": "公司做账需要一张抬头写公司的正规票据，邮箱能收吗？",
    },
    {
        "intent": "return_refund",
        "risk": False,
        "message": "商品尺寸不合适，包装完好，我想申请七天无理由退货。",
    },
    {
        "intent": "return_refund",
        "risk": False,
        "message": "还没超过七天，衣服没有穿过，吊牌也在，可以退款吗？",
    },
    {
        "intent": "return_refund",
        "risk": False,
        "message": "商品拆封后发现和页面差别很大，不影响二次销售，想退货。",
    },
    {
        "intent": "return_refund",
        "risk": False,
        "message": "买错了尺码，包装都还在，能原样寄回吗？",
    },
    {
        "intent": "cancel_order",
        "risk": False,
        "message": "订单还没有揽收，我不想要了，请帮我取消。",
    },
    {
        "intent": "cancel_order",
        "risk": False,
        "message": "地址填错了，现在还没发货，可以取消重新下单吗？",
    },
    {
        "intent": "cancel_order",
        "risk": False,
        "message": "已经发货了，但我临时不想要，可以拦截快递吗？",
    },
    {
        "intent": "cancel_order",
        "risk": False,
        "message": "先别给我寄了，我地址需要重新确认。",
    },
    {
        "intent": "complaint_escalation",
        "risk": True,
        "message": "已经联系两次都没解决，我要投诉并且找平台介入。",
    },
    {
        "intent": "complaint_escalation",
        "risk": True,
        "message": "你们这是欺骗消费者，再不处理我就去12315投诉。",
    },
    {
        "intent": "complaint_escalation",
        "risk": True,
        "message": "如果今天不给赔偿，我会曝光聊天记录并让律师联系你们。",
    },
    {
        "intent": "complaint_escalation",
        "risk": True,
        "message": "如果今天还不处理，我就把事情发到网上让媒体来采访。",
    },
]


EVAL_NAMES = [
    "林女士",
    "周先生",
    "陈女士",
    "赵女士",
    "许先生",
    "何女士",
    "唐先生",
    "吴女士",
    "王女士",
    "孙女士",
    "高先生",
    "梁女士",
    "宋女士",
    "郑先生",
    "冯女士",
    "韩先生",
    "曹女士",
    "彭先生",
    "邓女士",
    "蒋先生",
]

PREFIXES = ["", "你好，", "麻烦看一下，", "客服在吗，", "我想咨询一下，"]


def evaluation_cases() -> List[Dict[str, Any]]:
    """生成 120 条可复现的合成评测样本。"""
    order_ids = list(ORDERS.keys())
    channels = ["淘宝", "京东", "抖店", "小红书", "天猫"]
    cases: List[Dict[str, Any]] = []
    index = 0
    for base in EVALUATION_BASES:
        for prefix in PREFIXES:
            index += 1
            cases.append(
                {
                    "id": f"EV-{index:03d}",
                    "message": prefix + base["message"],
                    "order_id": order_ids[(index - 1) % len(order_ids)],
                    "customer": EVAL_NAMES[(index - 1) % len(EVAL_NAMES)],
                    "channel": channels[(index - 1) % len(channels)],
                    "expected_intent": base["intent"],
                    "expected_risk": base["risk"],
                    "expected_policies": INTENT_POLICIES[base["intent"]],
                }
            )
    return cases


def policy_by_id(policy_id: str) -> Dict[str, Any]:
    for policy in POLICIES:
        if policy["id"] == policy_id:
            return policy
    raise KeyError(policy_id)


def now_label() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def recent_labels(days: int = 7) -> List[str]:
    today = datetime.now()
    return [(today - timedelta(days=i)).strftime("%m-%d") for i in range(days - 1, -1, -1)]
