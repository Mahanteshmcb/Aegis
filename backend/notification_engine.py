"""Notification evaluation engine for Day 68.
Provides a simple evaluator that can trigger SystemAlert records for rules.
"""
import ast
import logging
from datetime import datetime
from typing import Optional, Any

from sqlalchemy.orm import Session

from backend import crud
from backend.models_db import NotificationRule
from backend.schemas import SystemAlertCreate

logger = logging.getLogger(__name__)


def _safe_eval(node: ast.AST, context: dict) -> Any:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body, context)
    if isinstance(node, ast.BoolOp):
        values = [_safe_eval(v, context) for v in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)
        raise ValueError(f"Unsupported boolean operator: {node.op}")
    if isinstance(node, ast.BinOp):
        left = _safe_eval(node.left, context)
        right = _safe_eval(node.right, context)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Mod):
            return left % right
        raise ValueError(f"Unsupported binary operator: {node.op}")
    if isinstance(node, ast.UnaryOp):
        operand = _safe_eval(node.operand, context)
        if isinstance(node.op, ast.Not):
            return not operand
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return +operand
        raise ValueError(f"Unsupported unary operator: {node.op}")
    if isinstance(node, ast.Compare):
        left = _safe_eval(node.left, context)
        for op, comparator in zip(node.ops, node.comparators):
            right = _safe_eval(comparator, context)
            if isinstance(op, ast.Eq) and not (left == right):
                return False
            if isinstance(op, ast.NotEq) and not (left != right):
                return False
            if isinstance(op, ast.Lt) and not (left < right):
                return False
            if isinstance(op, ast.LtE) and not (left <= right):
                return False
            if isinstance(op, ast.Gt) and not (left > right):
                return False
            if isinstance(op, ast.GtE) and not (left >= right):
                return False
            left = right
        return True
    if isinstance(node, ast.Name):
        return context.get(node.id)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Attribute):
        value = _safe_eval(node.value, context)
        if isinstance(value, dict):
            return value.get(node.attr)
        return getattr(value, node.attr, None)
    if isinstance(node, ast.Subscript):
        container = _safe_eval(node.value, context)
        key = _safe_eval(node.slice, context) if hasattr(node, 'slice') else None
        if isinstance(container, dict):
            return container.get(key)
        return None
    raise ValueError(f"Unsupported expression: {type(node).__name__}")


def _evaluate_simple_condition(condition: str, context: dict) -> bool:
    """Support a simple expression language: numeric comparisons and AND/OR."""
    if not condition:
        return False
    normalized = condition.strip().lower()
    if normalized == 'always':
        return True

    try:
        tree = ast.parse(condition, mode='eval')
    except SyntaxError as exc:
        logger.warning('Condition parse failed: %s', exc)
        return False

    for node in ast.walk(tree):
        if isinstance(node, (ast.Call, ast.Lambda, ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal, ast.With, ast.Try, ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
            logger.warning('Unsupported expression element in condition: %s', type(node).__name__)
            return False

    try:
        result = _safe_eval(tree, context)
        return bool(result)
    except Exception as e:
        logger.warning('Condition evaluation failed for %s: %s', condition, e)
        return False


def evaluate_rule(db: Session, tenant_id: int, rule_id: int, trigger_by_user_id: Optional[int] = None, context: dict | None = None) -> Optional[int]:
    """Evaluate the rule, create an alert, and optionally emit delivery status."""
    rule = db.query(NotificationRule).filter(NotificationRule.tenant_id == tenant_id, NotificationRule.id == rule_id).first()
    if not rule or not rule.enabled:
        return None

    if context is None:
        context = {}

    triggered = _evaluate_simple_condition(rule.condition, context)
    if not triggered:
        logger.debug('Rule %s did not match (condition=%s)', rule.id, rule.condition)
        return None

    alert_payload = {
        'tenant_id': tenant_id,
        'alert_type': 'notification_rule',
        'severity': 'medium',
        'title': f'Notification triggered: {rule.name}',
        'message': f'Rule {rule.name} matched (condition={rule.condition})',
        'source': 'system',
        'data': {'rule_id': rule.id, 'condition': rule.condition, 'context': context},
    }
    alert = crud.create_system_alert(db, SystemAlertCreate(**alert_payload))
    logger.info('Rule %s triggered, created alert %s', rule.id, alert.id)

    delivery_configs = crud.list_alert_delivery_configs(db, tenant_id)
    for cfg in delivery_configs:
        if not cfg.enabled:
            continue
        crud.create_alert_delivery_status(db, tenant_id, alert.id, cfg.provider, status='pending', attempts=0)

    return alert.id
