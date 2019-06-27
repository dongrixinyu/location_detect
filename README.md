# 简介
给定一篇文章，可包含标题和正文，从文章中确定地名

# 安装
```
$ git clone http://git.bbdops.com/dongrixinyu/Location-Detect.git
$ pip install Location-Detect/
``` 
# 使用方法
```python
import loc_reg
title = '湖南2018年度企业环境信用评价公示 39家企业拟被评“不良”'
passage = '【湖南2018年度企业环境信用评价公示 39家企业拟被评“不良”】今天，记者从湖南省生态环境厅获悉，我省2018年度企业环境信用评价拟定结果正在进行公示，拟评定环境诚信企业31家、环境合格企业1247家、环境风险企业121家、环境不良企业39家。'
print(loc_reg.predict(title, passage))
```