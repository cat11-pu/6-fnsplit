# -*- coding: utf-8 -*-
"""验收：结构与行为双轨。
结构：两个新模块存在、functions.py 引用它们、functions.py 里 _func_ 归零、行数下降、
      注册表函数名集合仍是原来那 24 个。
行为：30 条内置函数表达式逐个比对（期望值固化自拆分前的实现）。
全过退出码 0。"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(HERE, "jmespath")
WANT_FUNCS = ["abs", "avg", "ceil", "contains", "ends_with", "floor", "join", "keys", "length", "map", "max", "max_by", "merge", "min", "min_by", "not_null", "reverse", "sort", "sort_by", "starts_with", "sum", "to_array", "to_number", "to_string", "type", "values"]
BATTERY = json.loads("""{
 "length(s)": 5,
 "length(strs)": 3,
 "sort(nums)": [
  1,
  2,
  3
 ],
 "sort_by(objs, &n)[*].t": [
  "y",
  "x"
 ],
 "max(nums)": 3,
 "min(nums)": 1,
 "max_by(objs, &n).t": "x",
 "min_by(objs, &n).t": "y",
 "join('-', strs)": "a-b-a",
 "contains(strs, 'a')": true,
 "starts_with(s, 'he')": true,
 "ends_with(s, 'lo')": true,
 "reverse(nums)": [
  2,
  1,
  3
 ],
 "reverse(s)": "olleh",
 "to_string(nums)": "[3,1,2]",
 "to_number('42')": 42,
 "to_array(s)": [
  "hello"
 ],
 "type(s)": "string",
 "type(nums)": "array",
 "type(obj)": "object",
 "keys(obj)": [
  "k1",
  "k2"
 ],
 "values(obj)": [
  1,
  2
 ],
 "merge(obj, obj2)": {
  "k1": 1,
  "k2": 9,
  "k3": 3
 },
 "map(&n, objs)": [
  3,
  1
 ],
 "not_null(missing, s)": "hello",
 "sum(nums)": 6,
 "avg(nums)": 2.0,
 "ceil(floats[0])": 2,
 "floor(floats[0])": 1,
 "abs(floats[1])": 1.8
}""")
DOC = json.loads("""{"s": "hello", "strs": ["a", "b", "a"], "nums": [3, 1, 2], "objs": [{"n": 3, "t": "x"}, {"n": 1, "t": "y"}], "obj": {"k1": 1, "k2": 2}, "obj2": {"k2": 9, "k3": 3}, "floats": [1.2, -1.8]}""")


def main():
    bad = 0
    problems = []

    # ---- 结构 ----
    str_path = os.path.join(PKG, "fn_strings.py")
    col_path = os.path.join(PKG, "fn_collections.py")
    if not os.path.exists(str_path):
        problems.append("缺少 jmespath/fn_strings.py")
    if not os.path.exists(col_path):
        problems.append("缺少 jmespath/fn_collections.py")
    func_path = os.path.join(PKG, "functions.py")
    func_text = io.open(func_path, encoding="utf-8").read()
    for needed in ("fn_strings", "fn_collections"):
        if needed not in func_text:
            problems.append("functions.py 没有引用 " + needed)
    left = len(re.findall(r"def _func_", func_text))
    if left != 0:
        problems.append("functions.py 里还留着 %d 个 _func_ 定义" % left)
    lines = len(func_text.splitlines())
    if lines > 200:
        problems.append("functions.py 还有 %d 行（要求不超过 200）" % lines)

    sys.path.insert(0, HERE)
    import jmespath
    from jmespath.functions import Functions
    got = sorted(Functions.FUNCTION_TABLE.keys())
    if got != WANT_FUNCS:
        problems.append("注册表函数名对不上：期望 %d 个，实际 %d 个，差异 %s"
                        % (len(WANT_FUNCS), len(got),
                           sorted(set(WANT_FUNCS) ^ set(got))[:6]))

    # ---- 行为 ----
    for expr in sorted(BATTERY):
        try:
            result = jmespath.search(expr, DOC)
        except Exception as error:  # noqa: BLE001
            result = "抛错:" + str(error)[:40]
        if result == BATTERY[expr]:
            print("通过", expr, "=", json.dumps(result, ensure_ascii=False))
        else:
            bad += 1
            print("不过", expr, "期望", json.dumps(BATTERY[expr], ensure_ascii=False),
                  "实际", json.dumps(result, ensure_ascii=False, default=str))

    # ---- 汇总 ----
    for item in problems:
        print("结构不过", item)
    total = len(BATTERY) + 5
    passed = total - bad - len(problems)
    print("通过率 %d/%d" % (passed, total))
    return 0 if (bad == 0 and not problems) else 1


if __name__ == "__main__":
    sys.exit(main())
