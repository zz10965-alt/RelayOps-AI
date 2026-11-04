"""Dify Code node: strict, fail-closed JSON validation before any resolve call."""
import json
import math


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate key')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('non-finite JSON number')


def main(text: str, order_id: str, case_id: str, execution_token: str) -> dict:
    output = {'route': 'handoff', 'body': '', 'analysis': '', 'reason': '模型JSON无效，需要人工核查'}
    try:
        if not isinstance(text, str) or not 1 <= len(text) <= 6000:
            return output
        text = text.strip()
        if text.startswith('```json\n') and text.endswith('\n```'):
            text = text[8:-4]
        data = json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)
        fields = {'order_id', 'damaged', 'product_match', 'image_quality', 'confidence', 'summary'}
        if not isinstance(data, dict) or set(data) != fields:
            return output
        if type(data['damaged']) is not bool or type(data['product_match']) is not bool:
            return output
        if not isinstance(data['order_id'], str) or not 1 <= len(data['order_id']) <= 80:
            return output
        if not isinstance(data['summary'], str) or not 1 <= len(data['summary']) <= 1000:
            return output
        if data['image_quality'] not in ('clear', 'blurry', 'unrelated'):
            return output
        score = data['confidence']
        if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1:
            return output
        if not case_id or len(case_id) > 80 or not execution_token or len(execution_token) > 128:
            return output
        output['analysis'] = json.dumps(data, ensure_ascii=False, allow_nan=False)
        if data['order_id'] != order_id:
            output['reason'] = '订单号冲突，转人工'
        elif data['image_quality'] == 'blurry':
            output.update(route='supplement', reason='照片模糊，请补充清晰商品照片；不执行退货')
        elif data['image_quality'] != 'clear' or not data['product_match']:
            output['reason'] = '照片无关或商品不匹配，转人工；不执行退货'
        elif not data['damaged'] or score < 0.8:
            output['reason'] = '损坏证据或置信度不足，转人工；不执行退货'
        else:
            output.update(route='eligible', reason='视觉初筛通过，仍需后端业务规则与数据库回读')
            output['body'] = json.dumps({'case_id': case_id, 'execution_token': execution_token,
                                        'analysis': json.dumps(data, ensure_ascii=False, allow_nan=False)},
                                       ensure_ascii=False, allow_nan=False)
        return output
    except (ValueError, TypeError, OverflowError):
        return output
