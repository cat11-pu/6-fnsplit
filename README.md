# fnsplit

仓库里是 JMESPath 的 Python 实现（取自 jmespath/jmespath.py，MIT）。`jmespath/functions.py`
把所有内置函数都塞在一个类里，太长也不好维护。请按类拆开，行为一点不能变。

## 要拆成什么样

- 新建 `jmespath/fn_strings.py`：装字符串类内置函数（join、contains、starts_with、
  ends_with、to_string、to_number）。
- 新建 `jmespath/fn_collections.py`：装其余内置函数（sort、sort_by、max、max_by、min、
  min_by、length、reverse、merge、map、not_null、type、keys、values、to_array、sum、
  avg、ceil、floor、abs）。
- `jmespath/functions.py` 只留类型表、注册机制与共享工具，改成从上面两个模块引入实现；
  它里面**不能再有** `_func_` 开头的定义，整文件不超过 200 行。
- 允许为了拆分再引入必要的内部模块（例如放共享装饰器的），但 `jmespath` 包的对外用法不许变。

## 跑验收

    python3 check_refactor.py

结构（5 条）与行为（30 条内置函数表达式，期望值固化自拆分前的实现）都过才退出码 0。

## 约束

- 只改 `jmespath/` 包里的源码，不要动 `check_refactor.py`。
- 注册表里函数名集合必须还是原来那 24 个；行为一条不许变。
- 只用 Python 标准库。
