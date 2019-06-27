# -*- coding=utf-8 -*-
# ------------------------------------
# Create On 2019/04/24 10:20 
# File Name: location_recognization.py
# Edit Author: Cui Chengyu
# ------------------------------------

import os
import re
import json

from collections import Counter


DIR_PATH = os.path.abspath(os.path.dirname(__file__))
# PARENT_PATH = os.path.dirname(DIR_PATH)
DICT_PATH = os.path.join(DIR_PATH, 'utils/dicts')


class LocationRecognization(object):
    ''' 给定一篇文章，可包含标题和正文，从文章中确定地名 '''
    def __init__(self, location_file='bbd_china_province_city_county.json', 
                 world_file='bbd_world_country.json'):
        ''' 
        location_file: 全国地名文件
        world_file: 全世界主要地名文件
        '''
        self.location_file = os.path.join(DICT_PATH, location_file)
        self.world_file = os.path.join(DICT_PATH, world_file)
        print(self.location_file)
        with open(self.location_file, 'r', encoding='utf-8') as f:
            self.location_dict = json.load(f)
        
        # 冗余信息，不能作为地名的指标判断    
        self.redundent_locations = ['北京时间']
        
        # 不带国家名的国外地名，用于国外、国内判断
        self.world_words = ['联合国', '全球', '世界', '东盟', '白宫', '亚洲', 
                            '欧洲', '欧盟', '南极洲', '非洲', '南美', '北美']
        self.world_words_pattern = re.compile('(' + '|'.join(self.world_words) + ')')
        
        # 无具体省市的国内词汇
        self.domestic_words = ['中国', '我国']  # , '全国'
        self.domestic_words_pattern = re.compile('(' + '|'.join(self.domestic_words) + ')')
        
        self.redundent_locations_pattern = re.compile('(' + '|'.join(self.redundent_locations) + ')')
        self.suffix_names = ['自治区', '自治州', '自治县', '盟', '省', '市', '区', '县', '旗']
        self._get_location_names()
        
        with open(self.world_file, 'r', encoding='utf-8 ') as f:
            self.world_dict = json.load(f)
        self._get_world_location_names()
        
    def _get_clean_names(self, name_list):
        ''' 给定一个 name_list，清除其中的后缀 '''
        for suffix in self.suffix_names:
            name_list = [name.replace(suffix, '') if '地区' not in name else name for name in name_list]
        return name_list
    
    def _get_clean_name(self, name):
        ''' 给定一个 name，清除其中的后缀 '''
        for suffix in self.suffix_names:
            if '地区' not in name:
                name = name.replace(suffix, '')
        return name
        
    def _get_world_location_names(self):
        ''' 获取世界主要地名 '''
        self.world_locations_list = list()  # 所有地名集合，含国家和城市
        self.world_locations_dict = dict()  # 所有地名的映射词典
        for country, cities in self.world_dict.items():
            self.world_locations_dict.update({country: country})
            if type(cities) is list:
                for city in cities:
                    self.world_locations_dict.update({city: country})
            else:
                if cities is not None:
                    self.world_locations_dict.update({cities: country})
        self.world_locations_list = list(self.world_locations_dict.keys())
        self.world_locations_pattern = re.compile('(' + '|'.join(self.world_locations_list) + ')')
        
    def _get_location_names(self):
        ''' 获取所有的地名，分级展开 '''
        # 获取所有的名字
        not_in_city = '省直辖行政单位'  # 被排除在 city 之外
        province_names = list(self.location_dict.keys())
        cleaned_province_names = self._get_clean_names(province_names)
        
        city_names = list(set([c_k for p_k in self.location_dict.keys() 
                               for c_k in self.location_dict[p_k].keys() if not_in_city not in c_k]))
        cleaned_city_names = self._get_clean_names(city_names)
        
        county_names = [co_k for p_k in self.location_dict.keys() for ci_k in self.location_dict[p_k].keys() 
                        for co_k in self.location_dict[p_k][ci_k]]
        cleaned_county_names = self._get_clean_names(county_names)
        
        # 建立正则表达式
        self.province_pattern = re.compile('(' + '|'.join(province_names + cleaned_province_names) + ')')
        self.city_pattern = re.compile('(' + '|'.join(city_names) + ')')  # 去掉后缀会引起歧义
        self.county_pattern = re.compile('(' + '|'.join(county_names) + ')')  # 去掉后缀会引起歧义
        
        # 建立倒排索引
        self.city_to_province = dict()
        for p_k in self.location_dict.keys():
            for c_k in self.location_dict[p_k].keys():
                self.city_to_province[self._get_clean_name(c_k)] = self._get_clean_name(p_k)
        
        self.county_to_city = dict()
        for p_k in self.location_dict.keys():
            for ci_k in self.location_dict[p_k].keys():
                for co_k in self.location_dict[p_k][ci_k]:
                    self.county_to_city[co_k] = self._get_clean_name(ci_k)
        
    def _search_world_location(self, passage, top_k=2):
        '''
        搜索世界地名，返回所有的国家名，及其频次
        '''
        world_res = self.world_locations_pattern.finditer(passage)
        country_list = list()
        world_counts = 0
        for item in world_res:
            country_list.append(self.world_locations_dict[item.group()])
            world_counts += 1
        counter = Counter(country_list).most_common()
        country_list = [tup[0] for tup in counter][:top_k]
        return country_list, world_counts
        
    def _search_domestic_location(self, passage, top_k=2):
        '''
        搜索国内的地名，及其频次
        '''
        final_res = list()
        domestic_counts = 0  # 用于判断国内国外地名的重要性
        # 首先找市，找到对应的省，直接返回
        city_res = self.city_pattern.finditer(passage)
        city_list = list()
        for item in city_res:
            city_list.append(self._get_clean_name(item.group()))
        
        if city_list != []:
            counter = Counter(city_list).most_common()
            domestic_counts += sum([tup[1] for tup in counter])
            city_list = [tup[0] for tup in counter][:top_k]
            for city in city_list:
                final_res.append({'省': self.city_to_province[city], 
                                  '市': city})
            # print('选择了市！！！')
            return final_res, domestic_counts
        
        # 此时没找到 city 从 县入手
        county_res = self.county_pattern.finditer(passage)
        county_list = list()
        for item in county_res:
            county_list.append(item.group())

        if county_list != []:
            counter = Counter(county_list).most_common()
            domestic_counts += sum([tup[1] for tup in counter])
            county_list = [tup[0] for tup in counter][:top_k]
            for county in county_list:
                cur_loc = None  # 当前的地址
                if '直辖行政单位' in self.county_to_city[county]:  # 将县级市直接拉到市中
                    cur_loc = {'省': self.city_to_province[self.county_to_city[county]], 
                               '市': county}
                else:
                    cur_loc = {'省': self.city_to_province[self.county_to_city[county]], 
                               '市': self.county_to_city[county]}

                if cur_loc not in final_res:
                    final_res.append(cur_loc)
            #print('选择了县！！！')
            return final_res, domestic_counts  # 去重
        
        # 市和县都没找到，找省，并返回省
        province_res = self.province_pattern.finditer(passage)
        province_list = list()
        for item in province_res:
            province_list.append(self._get_clean_name(item.group()))
            
        if province_list != []:  # 找到了省
            counter = Counter(province_list).most_common()
            domestic_counts += sum([tup[1] for tup in counter])
            province_list = [tup[0] for tup in counter][:top_k]
            for province in province_list:
                if province in ['北京', '上海', '天津', '重庆', '香港', '澳门']:
                    final_res.append({'省': province, '市': province})
                else:
                    final_res.append({'省': province})
            #print('选择了省！！！', province)
            return final_res, domestic_counts
        
        return final_res, domestic_counts  # 没有找到任何地址
                
    def search_location(self, title=None, passage=None, top_k=2):
        ''' 输入一篇文章，找到地名 
        top_k: 只取最重要的5个
        
        首先找市，找到对应的省，直接返回；
        如果皆空，找县，再找对应的市和省，返回；
        如果没有对应的县，则只找省，返回省；
        如果省也没有，市也没有，县也没有，返回空字典
        '''
        if title is not None:
            assert type(title) is str, 'the `title` is not str'
            
            # 首先处理标题，若标题有地名，则结果就返回该地名
            country_list, world_counts = self._search_world_location(title, top_k=top_k)
            city_list, domestic_counts = self._search_domestic_location(title, top_k=top_k)

            # 考虑 中国 二字在标题中，其国内的权重要加大
            if '中国' in title or '我国' in title:
                domestic_counts += 1

            if country_list != [] and domestic_counts == 0:
                # 国外有国家名，而无国内地名，则返回国外，国家名
                return {'国外': country_list}
            if domestic_counts != 0: # and country_list == []:
                # 有国内名，而不管有无国外名，则返回国内名
                # TODO:
                # 此时地名中可能不包含省，市，也就是不全，还需要在原文中确定
                # 由于大数据不需要这些，故不返回了。
                return {'国内': city_list}
            # if domestic_counts != 0 and country_list != []:
                #if world_counts > domestic_counts:  # 标题中出现了更多的国外地名
                #    return '国外', country_list
                #else:  # 国外地名与国内地名同样多时，返回国内地名
                #    pdb.set_trace()
                #    return '国内', city_list
        
        if passage is not None:
            assert type(passage) is str, 'the `passage` is not str'
            
            if title is not None:
                title_passage = ''.join([title, passage])
            else:
                title_passage = passage
            # 若标题中未显示任何地名信息，或无标题，则进一步在文章中处理寻找
            # 将冗余的一些地名删除，北京时间等等。
            passage = self.redundent_locations_pattern.sub('', passage)

            # 计数其中`中国、我国`字样
            zhongguo_count = 0
            domestic_res = self.domestic_words_pattern.finditer(title_passage)
            for item in domestic_res:
                zhongguo_count += 1

            country_list, world_counts = self._search_world_location(passage, top_k=top_k)
            city_list, domestic_counts = self._search_domestic_location(passage, top_k=top_k)

            domestic_counts += zhongguo_count

            if country_list != [] and domestic_counts == 0:
                # 国外有国家名，而无国内地名，则返回国外，国家名
                return {'国外': country_list}
            if domestic_counts != 0 and country_list == []:
                # 有国内名，而无国外名，则返回国内名
                return {'国内': city_list}
            if domestic_counts != 0 and country_list != []:
                if world_counts > 3 * domestic_counts:  # 标题中出现了更多的国外地名
                    return {'国外': country_list}
                else:  # 国外地名与国内地名同样多时，返回国内地名
                    return {'国内': city_list}

            # 若两者皆空，检查国外的可能性
            # 检查一些不含国家名的国外地，若有直接返回国外
            world_list = list()
            world_res = self.world_words_pattern.finditer(title_passage)
            for item in world_res:
                world_list.append(item.group())
            if len(world_list) > len(passage) * 0.005:  # 出现多次才能判定为国外
                return {'国外': list()}
            return {'国内': list()}
        
        if title is not None:
            return {'国内': list()}
        raise ValueError('`title` and `passage` should not be None')


if __name__ == '__main__':
    import pdb
    
    title = '古特雷斯呼吁动员各方力量加快可持续发展目标实施进度。'
    passage = '''新华社联合国7月18日电（记者王建刚）联合国秘书长古特雷斯18日在2018年可持续发展高级别政治论坛闭幕式上，肯定了落实2030年可持续发展目标所取得的积极进展，同时敦促国际社会动员各方力量，加快目标实施进度。古特雷斯指出，虽然全球在降低母婴死亡率、提高基础教育覆盖率以及改善电力供应等方面取得了显著进展，但在实现“不让任何一个人掉队”这一核心承诺时，国际社会在某些领域已经落后于既定目标，甚至出现了倒退。他表示，全球罹患营养不良的人数十年来首次出现了上升。性别不平等问题仍在阻碍女性发展，剥夺她们的基本权利和发展机遇。此外，对可持续基础设施的关键投资也严重不足。古特雷斯说，全球正面临气候变化、战争冲突、不平等、侵犯人权、人道主义危机、长期贫穷与饥饿等重大挑战。为应对这些挑战，实现可持续发展目标，国际社会需要从5个方面加大努力。首先，要充分动员青年的力量，让青年接受良好的教育。其次，全球必须控制温室气体排放。第三，可持续发展目标所需资金仍面临重大缺口，国际社会应调动内部资源，并为脆弱国家提供经济支持。第四，要充分运用先进技术优势，让所有人受益。第五，国际社会要加强体系建设，共创和平与包容的社会。联合国可持续发展高级别政治论坛18日以压倒性多数通过一份部长宣言，重申国际社会致力于有效落实2030年可持续发展议程的承诺。联合国可持续发展高级别政治论坛每年举行一次，包括为期3天的部长级会议。今年论坛的主题为“向可持续和富有抗御力的社会转型”，有80多位部长和副部长以及2500名非政府组织成员出席论坛。在为期8天的讨论中，47个国家分享了各自的成功经验、面临的挑战以及汲取的教训。'''
    
    location = LocationRecognization()
    res = location.search_location(title=title, passage=passage)
    print(json.dumps(res, ensure_ascii=False))

                        
                        