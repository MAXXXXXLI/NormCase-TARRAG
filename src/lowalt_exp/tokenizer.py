import re
from typing import List


def char_ngrams(text: str, n_min: int = 2, n_max: int = 4) -> List[str]:
    text = re.sub(r"\s+", "", text.lower())
    tokens: List[str] = []
    for n in range(n_min, n_max + 1):
        if len(text) < n:
            continue
        tokens.extend(text[i : i + n] for i in range(len(text) - n + 1))
    # Add simple keyword tokens for short regulatory words.
    for kw in ["无人机", "低空", "空域", "登记", "运行", "审批", "飞行", "数据", "测绘", "北京", "深圳", "标准", "适航", "物流"]:
        if kw in text:
            tokens.append(kw)
    return tokens
