# -*- coding: utf-8 -*-
"""可离线运行的工单分类、BM25 检索、工作流编排与评测引擎。"""

from __future__ import annotations

import json
import math
import os
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from data import (
    DEMO_TICKETS,
    EVALUATION_BASES,
    INTENT_POLICIES,
    ORDERS,
    POLICIES,
    evaluation_cases,
    policy_by_id,
)


INTENT_META = {
    "logistics_delay": {"label": "物流停滞", "color": "blue", "owner": "物流客服组"},
    "damage_missing": {"label": "破损/缺件", "color": "orange", "owner": "售后处理组"},
    "invoice": {"label": "发票问题", "color": "violet", "owner": "订单服务组"},
    "return_refund": {"label": "退换货", "color": "green", "owner": "售后处理组"},
    "cancel_order": {"label": "取消订单", "color": "cyan", "owner": "履约支持组"},
    "complaint_escalation": {"label": "投诉升级", "color": "red", "owner": "客户关系组"},
}

INTENT_KEYWORDS = {
    "complaint_escalation": [
        "投诉",
        "曝光",
        "12315",
        "律师",
        "工商",
        "监管",
        "维权",
        "诈骗",
        "欺骗消费者",
    ],
    "damage_missing": [
        "破损",
        "损坏",
        "碎了",
        "漏液",
        "少件",
        "缺件",
        "配件",
        "勾丝",
        "瘪了",
        "压坏",
    ],
    "invoice": ["发票", "开票", "抬头", "税号", "红冲", "报销"],
    "return_refund": ["退货", "退款", "七天", "无理由", "不合适", "吊牌", "二次销售"],
    "cancel_order": ["取消", "别发", "不想要", "地址填错", "拦截", "重新下单"],
    "logistics_delay": [
        "物流",
        "快递",
        "没更新",
        "没有新轨迹",
        "派送",
        "签收",
        "揽收",
        "转运中心",
        "驿站",
        "丢件",
    ],
}

STOPWORDS = {
    "的",
    "了",
    "吗",
    "呢",
    "我",
    "你",
    "您",
    "请",
    "帮",
    "能",
    "可以",
    "怎么",
    "什么",
    "一个",
    "这个",
}


def _tokens(text: str) -> List[str]:
    text = text.lower()
    words = re.findall(r"[a-z0-9_]+|[\u4e00-\u9fff]+", text)
    tokens: List[str] = []
    for word in words:
        if re.fullmatch(r"[\u4e00-\u9fff]+", word):
            if len(word) == 1:
                candidates = [word]
            else:
                candidates = [word[i : i + 2] for i in range(len(word) - 1)]
                candidates += list(word)
        else:
            candidates = [word]
        tokens.extend(token for token in candidates if token not in STOPWORDS)
    return tokens


class BM25Retriever:
    def __init__(self, documents: Sequence[Dict[str, Any]], k1: float = 1.5, b: float = 0.75):
        self.documents = list(documents)
        self.k1 = k1
        self.b = b
        self.corpus = [
            _tokens(
                f"{doc['title']} {doc['keywords']} {doc['content']} {doc.get('section', '')}"
            )
            for doc in self.documents
        ]
        self.doc_lengths = [len(tokens) for tokens in self.corpus]
        self.avgdl = sum(self.doc_lengths) / max(len(self.doc_lengths), 1)
        self.doc_freqs = [Counter(tokens) for tokens in self.corpus]
        df = Counter()
        for counts in self.doc_freqs:
            df.update(counts.keys())
        total = len(self.documents)
        self.idf = {
            term: math.log(1 + (total - freq + 0.5) / (freq + 0.5))
            for term, freq in df.items()
        }

    def score(self, query: str, index: int) -> float:
        query_terms = _tokens(query)
        frequencies = self.doc_freqs[index]
        length = self.doc_lengths[index] or 1
        total = 0.0
        for term in query_terms:
            frequency = frequencies.get(term, 0)
            if frequency == 0:
                continue
            denominator = frequency + self.k1 * (
                1 - self.b + self.b * length / max(self.avgdl, 1)
            )
            total += self.idf.get(term, 0) * frequency * (self.k1 + 1) / denominator
        return total

    def search(self, query: str, limit: int = 3) -> List[Tuple[Dict[str, Any], float]]:
        ranked = [
            (document, self.score(query, index))
            for index, document in enumerate(self.documents)
        ]
        ranked.sort(key=lambda item: item[1], reverse=True)
        return [(document, round(score, 3)) for document, score in ranked[:limit] if score > 0]


RETRIEVER = BM25Retriever(POLICIES)


def classify_intent(message: str) -> Dict[str, Any]:
    scores = {intent: 0 for intent in INTENT_KEYWORDS}
    hits: Dict[str, List[str]] = {intent: [] for intent in INTENT_KEYWORDS}
    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in message:
                scores[intent] += 1
                hits[intent].append(keyword)

    # 投诉风险优先，避免被“破损/退款”等业务意图稀释。
    if scores["complaint_escalation"] > 0:
        scores["complaint_escalation"] += 3

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    intent, top_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0
    if top_score <= 0:
        intent = "logistics_delay"
        confidence = 0.42
    else:
        margin = max(0, top_score - second_score)
        confidence = min(0.97, 0.62 + top_score * 0.055 + margin * 0.045)
    return {
        "intent": intent,
        "label": INTENT_META[intent]["label"],
        "confidence": round(confidence, 2),
        "matched_keywords": hits[intent],
        "scores": scores,
    }


def classify_naive(message: str) -> str:
    """单轮 Prompt 基线使用的简单首命中规则。"""
    for intent in [
        "logistics_delay",
        "damage_missing",
        "invoice",
        "return_refund",
        "cancel_order",
        "complaint_escalation",
    ]:
        if any(keyword in message for keyword in INTENT_KEYWORDS[intent]):
            return intent
    return "logistics_delay"


def risk_assessment(message: str, intent: str, order: Dict[str, Any]) -> Dict[str, Any]:
    reasons: List[str] = []
    if intent == "complaint_escalation":
        reasons.append("命中投诉、监管或法律风险")
    if any(
        term in message
        for term in ["赔偿", "赔付", "损失", "全额", "媒体", "采访", "发到网上", "找记者"]
    ):
        reasons.append("客户提出赔偿或金额诉求")
    if intent == "damage_missing" and any(
        term in message for term in ["金额比较高", "金额较高", "金额很大", "几百元", "大额"]
    ):
        reasons.append("订单金额较高，破损处理需主管授权")
    if "验证码" in message or "银行卡" in message or "密码" in message:
        reasons.append("涉及敏感信息，需人工核验")
    return {
        "requires_review": bool(reasons),
        "level": "high" if reasons else "normal",
        "reasons": reasons,
        "handoff_team": "客户关系组" if intent == "complaint_escalation" else "售后主管",
    }


def _order(order_id: str) -> Dict[str, Any]:
    return ORDERS.get(
        order_id,
        {
            "order_id": order_id,
            "items": "订单信息待人工核验",
            "amount": 0.0,
            "status": "未知",
            "logistics": "暂无可用轨迹",
            "eta": "待确认",
            "customer_tier": "未知",
        },
    )


def _draft(intent: str, order: Dict[str, Any], risk: Dict[str, Any]) -> str:
    item = order["items"]
    order_id = order["order_id"]
    if intent == "logistics_delay":
        return (
            f"您好，已核对订单 {order_id}（{item}）。当前物流状态为："
            f"{order['logistics']}。我们会向承运商发起轨迹核查，并在核实后给您下一次反馈。"
            "在责任和件数确认前，暂无法直接承诺退款或赔付，请您留意后续进度。"
        )
    if intent == "damage_missing":
        if risk["requires_review"]:
            return (
                f"非常抱歉，订单 {order_id} 的{ item }出现了问题。请保留外包装和面单，"
                "并提供商品、包装与面单照片。因该单涉及较高金额或补偿判断，"
                "我已将资料升级给售后主管审核；未获授权前不会直接承诺现金赔偿。"
            )
        return (
            f"非常抱歉，订单 {order_id} 的{ item }出现了问题。请提供外包装、面单和"
            "问题部位照片；核验后可优先安排补发或换新。若无法补发，再按退货退款流程处理。"
        )
    if intent == "invoice":
        return (
            f"您好，订单 {order_id} 支持开具电子发票。请提交准确的发票抬头、税号和接收邮箱；"
            "订单完成且未申请退款后即可处理。若为当月信息有误，可申请红冲后重开。"
        )
    if intent == "return_refund":
        return (
            f"您好，订单 {order_id} 中的{ item }需结合签收时间和商品状态确认。"
            "签收后七日内且商品保持完好、不影响二次销售，可申请无理由退货；"
            "定制或已影响二次销售的商品不适用。您可补充商品现状照片，我们继续核验。"
        )
    if intent == "cancel_order":
        if order["status"] == "待发货":
            return (
                f"您好，订单 {order_id} 目前为待发货状态。我会提交取消申请，"
                "并请仓库尝试拦截；是否成功以系统回执为准，未确认前不会承诺已取消。"
            )
        return (
            f"您好，订单 {order_id} 当前状态为“{order['status']}”，已无法直接取消。"
            "我可以为您提交易拦截申请，但无法保证成功；若已派送，也可选择拒收，"
            "或签收后按退货流程处理。"
        )
    return (
        f"非常抱歉给您带来不好的体验。已记录订单 {order_id} 的问题和您当前的诉求，"
        "本工单已停止自动回复并升级至客户关系组。我们会先核实完整经过，"
        "不会在事实确认前作责任认定或赔偿承诺，并在约定的反馈时限内联系您。"
    )


def _policy_cards(policy_ids: Iterable[str], scores: Dict[str, float] | None = None) -> List[Dict[str, Any]]:
    scores = scores or {}
    cards = []
    for policy_id in policy_ids:
        policy = policy_by_id(policy_id)
        cards.append(
            {
                "id": policy["id"],
                "title": policy["title"],
                "section": policy["section"],
                "content": policy["content"],
                "score": scores.get(policy_id, 0),
            }
        )
    return cards


def _optional_llm_draft(
    message: str, order: Dict[str, Any], policies: List[Dict[str, Any]], fallback: str
) -> Tuple[str, str]:
    base_url = os.environ.get("LLM_BASE_URL", "").rstrip("/")
    api_key = os.environ.get("LLM_API_KEY", "")
    model = os.environ.get("LLM_MODEL", "")
    if not base_url or not api_key or not model:
        return fallback, "离线模板"

    policy_text = "\n".join(f"[{p['id']}] {p['content']}" for p in policies)
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是电商售后辅助助手。只能使用给定订单和政策事实，"
                    "不得承诺未经授权的退款、赔偿或办理结果，不得索取密码、验证码。"
                    "输出一段180字以内的中文客服草稿。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"客户消息：{message}\n订单：{json.dumps(order, ensure_ascii=False)}\n"
                    f"政策：{policy_text}\n参考草稿：{fallback}"
                ),
            },
        ],
    }
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            result = json.loads(response.read().decode("utf-8"))
        content = result["choices"][0]["message"]["content"].strip()
        forbidden = ["保证退款", "一定赔偿", "马上退款", "肯定能拦截"]
        if content and not any(term in content for term in forbidden):
            return content, "LLM 辅助生成"
    except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError):
        pass
    return fallback, "离线模板（LLM 不可用）"


def process_ticket(ticket: Dict[str, Any], use_llm: bool = False) -> Dict[str, Any]:
    started = time.perf_counter()
    message = ticket["message"]
    order = _order(ticket["order_id"])
    classification = classify_intent(message)
    intent = classification["intent"]

    retrieved = RETRIEVER.search(message, limit=3)
    retrieval_scores = {doc["id"]: score for doc, score in retrieved}
    mapped_ids = INTENT_POLICIES[intent]
    policy_ids = list(dict.fromkeys(mapped_ids + [doc["id"] for doc, _ in retrieved[:1]]))
    policies = _policy_cards(policy_ids, retrieval_scores)
    risk = risk_assessment(message, intent, order)
    fallback_draft = _draft(intent, order, risk)
    if use_llm:
        draft, generation_mode = _optional_llm_draft(message, order, policies, fallback_draft)
    else:
        draft, generation_mode = fallback_draft, "离线模板"

    steps = [
        {"name": "意图识别", "status": "done", "detail": classification["label"]},
        {"name": "订单核验", "status": "done", "detail": order["status"]},
        {"name": "政策检索", "status": "done", "detail": f"{len(policies)} 条依据"},
        {"name": "草稿生成", "status": "done", "detail": generation_mode},
        {
            "name": "风险审阅",
            "status": "warning" if risk["requires_review"] else "done",
            "detail": "转人工" if risk["requires_review"] else "可辅助发送",
        },
    ]
    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
    return {
        "ticket_id": ticket["id"],
        "intent": intent,
        "intent_label": classification["label"],
        "confidence": classification["confidence"],
        "matched_keywords": classification["matched_keywords"],
        "order": order,
        "policies": policies,
        "risk": risk,
        "draft": draft,
        "generation_mode": generation_mode,
        "steps": steps,
        "elapsed_ms": elapsed_ms,
        "decision": "转人工审核" if risk["requires_review"] else "客服确认后发送",
        "guardrail": (
            "自动化回复已停止；未经授权不得承诺赔偿或责任认定。"
            if risk["requires_review"]
            else "已通过事实约束与高风险规则检查。"
        ),
    }


def _baseline_policies(message: str) -> List[str]:
    scored = [(doc, RETRIEVER.score(message, i)) for i, doc in enumerate(POLICIES)]
    scored.sort(key=lambda item: item[1], reverse=True)
    return [scored[0][0]["id"]] if scored and scored[0][1] > 0 else []


def _rag_policies(message: str) -> List[str]:
    return [doc["id"] for doc, _ in RETRIEVER.search(message, limit=2)]


def evaluate() -> Dict[str, Any]:
    cases = evaluation_cases()
    methods = [
        {
            "id": "prompt",
            "name": "单轮 Prompt",
            "description": "无结构化订单核验与政策依据",
            "task_success": 0,
            "intent_correct": 0,
            "policy_correct": 0,
            "risk_correct": 0,
            "critical_errors": 0,
            "avg_policies": 0,
            "policy_count_total": 0,
        },
        {
            "id": "rag",
            "name": "RAG 检索增强",
            "description": "加入政策检索，但未设置风险接管",
            "task_success": 0,
            "intent_correct": 0,
            "policy_correct": 0,
            "risk_correct": 0,
            "critical_errors": 0,
            "avg_policies": 0,
            "policy_count_total": 0,
        },
        {
            "id": "workflow",
            "name": "RAG + Workflow",
            "description": "订单核验、政策依据、风险门禁与人工接管",
            "task_success": 0,
            "intent_correct": 0,
            "policy_correct": 0,
            "risk_correct": 0,
            "critical_errors": 0,
            "avg_policies": 0,
            "policy_count_total": 0,
        },
    ]

    per_intent: Dict[str, Dict[str, int]] = {
        intent: {"total": 0, "workflow_success": 0} for intent in INTENT_META
    }
    token_totals = {"prompt": 0, "rag": 0, "workflow": 0}

    for case in cases:
        message = case["message"]
        expected_intent = case["expected_intent"]
        expected_policies = set(case["expected_policies"])
        expected_risk = case["expected_risk"]
        order = _order(case["order_id"])

        predictions = {
            "prompt": {
                "intent": classify_naive(message),
                "policies": set(_baseline_policies(message)),
                "risk": False,
            },
            "rag": {
                "intent": classify_intent(message)["intent"],
                "policies": set(_rag_policies(message)),
                "risk": False,
            },
            "workflow": {
                "intent": classify_intent(message)["intent"],
                "policies": set(
                    INTENT_POLICIES[classify_intent(message)["intent"]]
                ),
                "risk": risk_assessment(
                    message, classify_intent(message)["intent"], order
                )["requires_review"],
            },
        }

        for method, prediction in predictions.items():
            metrics = next(item for item in methods if item["id"] == method)
            intent_ok = prediction["intent"] == expected_intent
            policy_ok = expected_policies.issubset(prediction["policies"])
            risk_ok = prediction["risk"] == expected_risk
            success = intent_ok and policy_ok and risk_ok
            metrics["intent_correct"] += int(intent_ok)
            metrics["policy_correct"] += int(policy_ok)
            metrics["risk_correct"] += int(risk_ok)
            metrics["task_success"] += int(success)
            metrics["critical_errors"] += int(expected_risk and not prediction["risk"])
            metrics["policy_count_total"] += len(prediction["policies"])

            policy_chars = sum(
                len(policy_by_id(policy_id)["content"]) for policy_id in prediction["policies"]
            )
            token_totals[method] += 180 + policy_chars // 2 + len(message) // 2

        per_intent[expected_intent]["total"] += 1
        workflow_prediction = predictions["workflow"]
        workflow_success = (
            workflow_prediction["intent"] == expected_intent
            and expected_policies.issubset(workflow_prediction["policies"])
            and workflow_prediction["risk"] == expected_risk
        )
        per_intent[expected_intent]["workflow_success"] += int(workflow_success)

    total = len(cases)
    for metrics in methods:
        metrics["task_success_rate"] = round(metrics["task_success"] / total * 100, 1)
        metrics["intent_accuracy"] = round(metrics["intent_correct"] / total * 100, 1)
        metrics["policy_coverage"] = round(metrics["policy_correct"] / total * 100, 1)
        metrics["risk_accuracy"] = round(metrics["risk_correct"] / total * 100, 1)
        metrics["critical_error_rate"] = round(metrics["critical_errors"] / total * 100, 1)
        metrics["avg_tokens"] = round(token_totals[metrics["id"]] / total)
        metrics["avg_policies"] = round(metrics["policy_count_total"] / total, 1)
        del metrics["intent_correct"]
        del metrics["policy_correct"]
        del metrics["risk_correct"]
        del metrics["critical_errors"]
        del metrics["task_success"]
        del metrics["policy_count_total"]

    risk_cases = sum(1 for case in cases if case["expected_risk"])
    return {
        "dataset": {
            "total": total,
            "risk_cases": risk_cases,
            "template_count": len(EVALUATION_BASES),
            "variants_per_template": 5,
            "source": "120 条离线回归样本，来自 24 个语义模板的 5 种表达变体；客户与订单均为虚构",
            "note": "模板与规则由同一项目设计，不是独立留出集；结果来自离线规则与 BM25 检索，不代表生产准确率。",
        },
        "methods": methods,
        "per_intent": [
            {
                "intent": intent,
                "label": INTENT_META[intent]["label"],
                "total": value["total"],
                "workflow_success_rate": round(
                    value["workflow_success"] / max(value["total"], 1) * 100, 1
                ),
            }
            for intent, value in per_intent.items()
        ],
    }


def dashboard_payload() -> Dict[str, Any]:
    evaluation = evaluate()
    pending = sum(1 for ticket in DEMO_TICKETS if ticket["status"] == "待处理")
    high_risk = sum(
        1
        for ticket in DEMO_TICKETS
        if ticket["priority"] in {"较高", "紧急"} and ticket["status"] == "待处理"
    )
    best = max(evaluation["methods"], key=lambda item: item["task_success_rate"])
    return {
        "pending": pending,
        "high_risk": high_risk,
        "total_demo": len(DEMO_TICKETS),
        "workflow_success": best["task_success_rate"],
        "critical_errors": best["critical_error_rate"],
        "policy_count": len(POLICIES),
        "evaluation_total": evaluation["dataset"]["total"],
    }
