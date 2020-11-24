from jinja2 import Environment, FileSystemLoader
from pyecharts.globals import CurrentConfig
from django.http import HttpResponse
from django.shortcuts import render

CurrentConfig.GLOBAL_ENV = Environment(loader=FileSystemLoader("./app/templates"))

import requests
import re
from pyecharts.charts import Map
import pyecharts.options as opts
import json

# import sys
# import urllib2 as HttpUtils
# import urllib as UrlUtils
# from bs4 import BeautifulSoup


# 获取页面源码
def gethtmlcode():
    s = requests.session()
    url = 'https://ncov.dxy.cn/ncovh5/view/pneumonia'
    # 获取响应
    response = s.get(url)
    # 设置响应的字符编码
    response.encoding = 'utf-8'
    # 拿到响应结果
    return response.text

# 从页面源码中获取我们想要的数据：全国及省份数据
def getprovincedata():
    # 使用正由匹配来获取想要的数据
    province_origin_data = re.compile('window.getAreaStat = ([\s\S]*?)</script>')
    data_list = province_origin_data.findall(gethtmlcode())
    # 由于获取到的数据是一个字符串，我们需要将其转换为列表
    return json.loads(data_list[0].replace('}catch(e){}', ''))

# 画全国地图与各省份地图
def drawmap(maptype, map_province_list, map_province_data):
    # 拿到想要的数据之后，接下来我们开始画地图
    title = ''
    if maptype == 'china':
        title = '全国疫情可视化数据展示'
    else:
        title = maptype

    ditu = (
        Map(
            init_opts=opts.InitOpts(
                width='900px',
                height='600px',
                page_title=title
            )
        )
        .add(
            series_name='确诊人数',
            data_pair=[list(z) for z in zip(map_province_list, map_province_data)],
            maptype=maptype,
            is_map_symbol_show=False  # 是否显示地图上的小红点
        )
        .set_global_opts(
            legend_opts=opts.LegendOpts(
                is_show=False
            ),
            visualmap_opts=opts.VisualMapOpts(
                is_piecewise=True,
                pieces=[
                    {'min': 0, 'max': 0, 'label': '0', 'color': '#ffffff'},
                    {'min': 1, 'max': 9, 'label': '1-9', 'color': '#FFE5DB'},
                    {'min': 10, 'max': 99, 'label': '10-99', 'color': '#FF9985'},
                    {'min': 100, 'max': 999, 'label': '100-999', 'color': '#F57567'},
                    {'min': 1000, 'max': 9999, 'label': '1000-9999', 'color': '#E64546'},
                    {'min': 10000, 'label': '>= 10000', 'color': '#B80909'}
                ],
                # pos_top='center',
                textstyle_opts=opts.TextStyleOpts(
                    color='#ffffff'
                )
            )
        )
    )
    return ditu


def index(request):
    # 获取省份数据
    province_data = getprovincedata()

    # 直接就可以生成图表
    # 接下来，我们要做什么样的事情呢？
    # 将我们获取到的数据  ==》 我们想要的数据 ==》 画图
    # 我们想要的数据：
    #   1） 各省份的名称  map_province_list = []
    #   2） 各省累计确认人数  map_province_data = []
    map_province_list = []
    map_province_data = []
    # 我们获取到的是什么样的数据？
    #  list0 = [
    #       {'provinceShortName': '北京', 'confirmedCount': 837},
    #       {'provinceShortName': '天津', 'confirmedCount': 655}
    #  ]
    # 如果将我们获取到的数据转为我们想要的数据
    # 遍历获取到的数据，拿到对应的省份和确诊人数，放到列表当中
    for item in province_data:
        map_province_list.append(item['provinceShortName'])
        map_province_data.append(item['currentConfirmedCount'])

    ditu = drawmap('china', map_province_list, map_province_data)

    return HttpResponse(ditu.render_embed(template_name='index.html', province_data=province_data))


# 从页面源码中获取我们想要的数据：全国及省份数据
def getglobaldata():
    # 使用正由匹配来获取想要的数据
    province_origin_data = re.compile('window.getStatisticsService = ([\s\S]*?)</script>')
    data_list = province_origin_data.findall(gethtmlcode())
    # 由于获取到的数据是一个字符串，我们需要将其转换为列表
    return json.loads(data_list[0].replace('}catch(e){}', ''))


# 返回全国总体数据
def getdata(request):
    return HttpResponse(json.dumps(getglobaldata()))

def getdatalist(request):
    return HttpResponse(json.dumps(getprovincedata()))

# 各省份地图
def province(request, province_name):
    # 获取省份数据
    province_data = getprovincedata()
    global_data = getprovincedetaildata(province_name)

    map_province_list = []
    map_province_data = []

    for item in province_data:
        if item['provinceShortName'] == province_name:
            for item1 in item['cities']:
                map_province_list.append(item1['cityName'])
                map_province_data.append(item1['confirmedCount'])


    # 修改城市名称
    map_province_list = changecityname(province_name, map_province_list)
    ditu = drawmap(province_name, map_province_list, map_province_data)

    return HttpResponse(ditu.render_embed(template_name='map_province.html', global_data=global_data, province_name=province_name))


# 修改城市名称，由于丁香医生城市名称与pycharts中城市名称不一至，因此需要修改
def changecityname(cityname, hei_city_name_list):
    if cityname == '北京':
        hei_end_name_list = hei_city_name_list
    if cityname == '上海':
        hei_end_name_list = hei_city_name_list
    if cityname == '天津':
        hei_end_name_list = hei_city_name_list
    if cityname == '重庆':
        hei_end_name_list = [
            '梁平县' if i == '梁平区' else '武隆县' if i == '武隆区' else '彭水苗族土家族自治县' if i == '彭水县' else '秀山土家族苗族自治县' if i == '秀山县' else '酉阳土家族苗族自治县' if i == '酉阳县' else '石柱土家族自治县' if i == '石柱县' else str(
                i) for i in hei_city_name_list]
    if cityname == '海南':
        hei_end_name_list = [
            '昌江黎族自治县' if i == '昌江' else '定安县' if i == '定安' else '昌江黎族自治县' if i == '昌江' else '临高县' if i == '临高' else '澄迈县' if i == '澄迈' else '保亭黎族苗族自治县' if i == '保亭' else '陵水黎族自治县' if i == '陵水' else '琼中黎族苗族自治县' if i == '琼中' else '乐东黎族自治县' if i == '乐东' else str(
                i) + "市" for i in hei_city_name_list]
    if cityname == '黑龙江':
        hei_end_name_list = ['大兴安岭地区' if i == '大兴安岭' else str(i) + "市" for i in hei_city_name_list]
    if cityname == '辽宁':
        hei_end_name_list = [str(i) + "市" for i in hei_city_name_list]
    if cityname == '河北':
        hei_end_name_list = [str(i) + "市" for i in hei_city_name_list]
    if cityname == '河南':
        hei_end_name_list = [str(i) + "市" for i in hei_city_name_list]
    if cityname == '吉林':
        hei_end_name_list = ['延边朝鲜族自治州' if i == '延边' else '四平市' if i == '四平市' else '吉林市' if i == '吉林市' else str(i) + "市"
                             for i in hei_city_name_list]
    if cityname == '内蒙古':
        hei_end_name_list = ['兴安盟' if i == '兴安盟' else '锡林郭勒盟' if i == '锡林郭勒盟' else str(i) + "市" for i in
                             hei_city_name_list]
    if cityname == '新疆':
        hei_end_name_list = [
            '五家渠市' if i == '兵团第六师五家渠市' else '石河子市' if i == '兵团第八师石河子市' else '昌吉回族自治州' if i == '昌吉州' else '塔城地区' if i == '塔城地区' else '巴音郭楞蒙古自治州' if i == '巴州' else '伊犁哈萨克自治州' if i == '伊犁州' else '吐鲁番市' if i == '吐鲁番市' else '阿克苏地区' if i == '阿克苏地区' else str(
                i) + "市" for i in hei_city_name_list]
    if cityname == '西藏':
        hei_end_name_list = [str(i) + "市" for i in hei_city_name_list]
    if cityname == '青海':
        hei_end_name_list = ['海北藏族自治州' if i == '海北州' else str(i) + "市" for i in hei_city_name_list]
    if cityname == '山东':
        hei_end_name_list = [str(i) + "市" for i in hei_city_name_list]
    if cityname == '山西':
        hei_end_name_list = [str(i) + "市" for i in hei_city_name_list]
    if cityname == '陕西':
        hei_end_name_list = [str(i) + "市" for i in hei_city_name_list]
    if cityname == '甘肃':
        hei_end_name_list = [str(i) + "市" for i in hei_city_name_list]
    if cityname == '湖北':
        hei_end_name_list = ['恩施土家族苗族自治州' if i == '恩施州' else '神农架林区' if i == '神农架林区' else str(i) + "市" for i in
                             hei_city_name_list]
    if cityname == '湖南':
        hei_end_name_list = ['湘西土家族苗族自治州' if i == '湘西自治州' else str(i) + "市" for i in hei_city_name_list]
    if cityname == '云南':
        hei_end_name_list = [
            '红河哈尼族彝族自治州' if i == '红河州' else '西双版纳傣族自治州' if i == '西双版纳' else '德宏傣族景颇族自治州' if i == '德宏州' else '大理白族自治州' if i == '大理州' else '楚雄彝族自治州' if i == '楚雄州' else '文山壮族苗族自治州' if i == '文山州' else str(
                i) + "市" for i in hei_city_name_list]
    if cityname == '贵州':
        hei_end_name_list = [
            '黔东南苗族侗族自治州' if i == '黔东南州' else '黔南布依族苗族自治州' if i == '黔南州' else '黔西南布依族苗族自治州' if i == '黔西南州' else str(
                i) + "市" for i in hei_city_name_list]
    if cityname == '四川':
        hei_end_name_list = [
            '甘孜藏族自治州' if i == '甘孜州' else '凉山彝族自治州' if i == '凉山州' else '阿坝藏族羌族自治州' if i == '阿坝州' else str(i) + "市" for i
            in hei_city_name_list]
    if cityname == '福建':
        hei_end_name_list = [str(i) + "市" for i in hei_city_name_list]
    if cityname == '江苏':
        hei_end_name_list = [str(i) + "市" for i in hei_city_name_list]
    if cityname == '江西':
        hei_end_name_list = [str(i) + "市" for i in hei_city_name_list]
    if cityname == '安徽':
        hei_end_name_list = [str(i) + "市" for i in hei_city_name_list]
    if cityname == '广东':
        hei_end_name_list = [str(i) + "市" for i in hei_city_name_list]
    if cityname == '广西':
        hei_end_name_list = [str(i) + "市" for i in hei_city_name_list]
    if cityname == '浙江':
        hei_end_name_list = [str(i) + "市" for i in hei_city_name_list]
    if cityname == '宁夏':
        hei_end_name_list = [str(i) + "市" for i in hei_city_name_list]
    return hei_end_name_list


# 准备省份的json数据
def getprovincedetaildata(province_name):
    # 获取省份数据
    province_name = province_name.replace('/getdata', '')
    # print('province_name:', province_name, len(province_name))
    province_data = getprovincedata()
    # print('province_data:', province_data)/
    data = {}

    for item in province_data:
        if item['provinceShortName'] == province_name:
            data = item['cities']
            break
    return data
    # return HttpResponse(json.dumps(data))

# def getdatalistprovince(data_list):
#     provinceShortNames = []
#     confirmedCounts = []
#     curedCounts = []
#     deadCounts = []
#     for i in data_list:
#         provinceShortNames.append(i['provinceShortName'])
#         confirmedCounts.append(i['currentConfirmedCount'])
#         curedCounts.append(i['curedCount'])
#         deadCounts.append(i['deadCount'])
#     # 数据这样返回没问题
#     # 但是我建议你在外面定义一个变量，在for循环中获取想要的数据并赋值给外面的变量，
#     # 然后返回外面的变量
#     provice = (zip(provinceShortNames, confirmedCounts, curedCounts, deadCounts))
# 
#     for L in provice:
#         # 判断并赋值
#         return L
#     # return HttpResponse(json.dumps(L))
#     return  provice
# 
# def getdatalistprovinces(request):
#     data_list = province
# 
#     return HttpResponse(json.dumps(getdatalistprovince(data_list)))






