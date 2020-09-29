# 简介
给定一篇文章，可包含标题和正文（或仅标题，仅正文），确定其**归属地**（地名）。
- 结果标准：
    - 区分国内国外，
    - 国外到国家名一级
    - 国内到省市一级

# 该功能已经集成合并至工具集 [JioNLP](https://github.com/dongrixinyu/JioNLP)，性能更好，速度更快！！！

# 安装
- 使用 python3
```
$ git clone https://github.com/dongrixinyu/location_detect.git
$ cd location_detect
$ pip install .
``` 
# 使用方法
### 样例1
```python
import loc_reg
title = '湖南2018年度企业环境信用评价公示 39家企业拟被评“不良”'
passage = '今天，记者从湖南省生态环境厅获悉，我省2018年度企业环境信用评价拟定结果正在长沙市进行公示，拟评定环境诚信企业31家、环境合格企业1247家、环境风险企业121家、环境不良企业39家。'
print(loc_reg.predict(title, passage))
```

结果为：
```json
{'国内': [{'省': '湖南', '市': '长沙'}]}
```

### 样例2

```python
passage = '近日，布鲁塞尔爆发了大规模罢工游行，城市服务、商店、餐饮店均受到影响，原因和欧盟税收等政策有关。'
print(loc_reg.predict(passage))
```

结果为：
```json
{'国外': ['比利时']}
```

# 说明

- 从舆情新闻数据中随机抽取 100 篇自测，正确率 93%。其他类型文本未测试，效果待定。

如果觉得好用，请 follow 我一下 https://github.com/dongrixinyu


