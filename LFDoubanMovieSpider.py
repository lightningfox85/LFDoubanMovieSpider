# 标准库
import os
import re
import csv
import time
import urllib
import json
# 第三方库及本地应用库
import requests
from bs4 import BeautifulSoup
import lxml
from wordcloud import WordCloud
import jieba
import jieba.analyse
from snownlp import SnowNLP
import matplotlib
import matplotlib.pyplot as plt

# 全局变量（手动填入）
g_webbrower_cookies = ''  # 手工写入登陆后的Cookies，非必填，页面数量较大时需要
g_response_moive_id = '26322774'  # 豆瓣电影ID
# 伪装的请求头:360极速浏览器，无需更改
g_response_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 \
   (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
}
g_font_path_chs = './font/SourceHanSerifCN-Regular.otf'  # 中文字体，无需更改
# 百度自然语言处理App ID
g_BaiduNLP_APP_ID = '14685896'
# 百度自然语言处理Api Key
g_BaiduNLP_API_KEY = 'xaYYnwKDkc8QCboTWKzqgs6r'
# 百度自然语言处理Secret Key
g_BaiduNLP_SECRET_KEY = 'V227Tx84BGHF12VZMmhkdd3Oiq7foWwc'


# 保存到CSV文件
def save_to_csv(filename, fieldnames, rows):
    with open(filename, 'a', encoding='utf_8_sig', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(rows)
# 获取电影完整短评
def get_movie_fullshortcontent(movie_shortcontent_id, cookies):
    # 短评地址  https://movie.douban.com/j/review/9690139/full
    lf_movie_shortcontent_url = \
        'https://movie.douban.com/j/review/%s/full' % (
            movie_shortcontent_id)
    lf_movie_shortcontent_response = requests.get(
        lf_movie_shortcontent_url,
        headers=g_response_headers, cookies=cookies).json()['html']
    return lf_movie_shortcontent_response
# 获取一页影评信息
def get_onepage_moive_info(index_20):
    # 请求
    # 影评地址  https://movie.douban.com/subject/3168101/reviews
    lf_response_url = \
        'https://movie.douban.com/subject/%s/reviews?start=%s' % \
        (g_response_moive_id, index_20)
    cookies = {}
    if (len(g_webbrower_cookies) > 0):
        for line in g_webbrower_cookies.split(';'):
            name, value = line.split('=', 1)
            cookies[name] = value
    lf_response = requests.get(lf_response_url, headers=g_response_headers,
                               cookies=cookies)
    # 解析
    lf_bs = BeautifulSoup(lf_response.text, 'lxml')
    # 用户
    movie_info_names = lf_bs.find_all('a', {'property': 'v:reviewer'})
    fieldnames = ['用户名', '评分', '有用数', '没用数', '短评']
    movie_infos = []
    for i in movie_info_names:
        movie_infos.append(i.string)
    # 评分
    movie_info_ratings = lf_bs.find_all(
        'span',
        {'class': re.compile('allstar\d0 main-title-rating')})
    for i in movie_info_ratings:
        movie_infos.append(i['title'])
    # 有用数和没用数
    movie_info_ups = lf_bs.find_all('span', {
        'id': re.compile('r-useful_count-\d*')})
    movie_info_downs = lf_bs.find_all('span', {
        'id': re.compile('r-useless_count-\d*')})
    for i in movie_info_ups:
        movie_infos.append(i.string.strip())
    for i in movie_info_downs:
        movie_infos.append(i.string.strip())
    # 短论
    movie_info_shortcontent_ids_text = lf_bs.find_all('div', {
        'id': re.compile('review_\d*_short')})
    for i in movie_info_shortcontent_ids_text:
        time.sleep(1)
        movie_infos.append(get_movie_fullshortcontent(i['data-rid'], cookies))
    for i in range(int(len(movie_infos) / 5)):
        movie_info_one = [
            movie_infos[i],
            movie_infos[i + int(len(movie_infos) / 5)],
            movie_infos[i + int(len(movie_infos) / 5) * 2],
            movie_infos[i + int(len(movie_infos) / 5) * 3],
            movie_infos[i + int(len(movie_infos) / 5) * 4]
        ]
        # print(movie_info_one) #显示影评信息
        # 保存到CSV文件
        save_to_csv('movie_info.csv', fieldnames, movie_info_one)
    time.sleep(3)
# 获取全部页面信息
def get_all_movie_info(lf_response_moive_id):
    # 请求
    lf_response_url = 'https://movie.douban.com/subject/%s/reviews?start=0' % \
                      (lf_response_moive_id)
    # 解码Cookies
    cookies = {}
    if (len(g_webbrower_cookies) > 0):
        for line in g_webbrower_cookies.split(';'):
            name, value = line.split('=', 1)
            cookies[name] = value
    lf_response = requests.get(lf_response_url, headers=g_response_headers,
                               cookies=cookies)
    # 解析
    lf_bs = BeautifulSoup(lf_response.text, 'lxml')
    # 页面数
    movie_info_pagenumbers = \
        lf_bs.find('span', {'class': 'thispage'})['data-total-page']
    for index in range(int(movie_info_pagenumbers)):
        print('共%s页影评信息，正在抓取第%s页，%s%%完成...' %
              (int(movie_info_pagenumbers), (index + 1),
               int(index / int(movie_info_pagenumbers) * 100)))
        get_onepage_moive_info(20 * index)
        print('共%s页影评信息，抓取第%s页影评信息完成，%s%%完成...' %
              (int(movie_info_pagenumbers), (index + 1),
               int((index + 1) / int(movie_info_pagenumbers) * 100)))
        time.sleep(1)
    print('全部抓取任务完成！')
# 读取CSV文件到文本
def read_from_csv_to_string(filename, fieldindex):
    with open(filename, 'r', encoding='utf_8_sig') as csvfile:
        csvreader = csv.reader(csvfile)
        text = ''
        for row in csvreader:
            text += row[fieldindex]
        return text
# 读取CSV文件到列表（由字段索引）
def read_from_csv_to_list(filename, fieldindex):
    with open(filename, 'r', encoding='utf_8_sig') as csvfile:
        # csvreader = csv.reader(csvfile)
        csvreader = csv.reader((line.replace('\0', '') for line in csvfile))
        text_list = []
        for row in csvreader:
            text_list.append(row[fieldindex])
        return text_list
# 读取CSV文件到列表
def read_from_csv_to_list(filename):
    with open(filename, 'r', encoding='utf_8_sig') as csvfile:
        # csvreader = csv.reader(csvfile)
        csvreader = csv.reader((line.replace('\0', '') for line in csvfile))
        text_list = []
        for row in csvreader:
            text_list.append(row)
        return text_list
# 数据清洗
def cleaning_data(data):
    '''
    数据清洗：
    1.不完整缺失数据处理：
        1.1直接删除。适合缺失值数量较小，并且是随机出现的，删除它们对整体数据影响不大的情况。
        1.2插补法。
        1.2.1使用均值或中位数填充。
        1.2.2随机插补法
        1.2.3多重插补法----通过变量之间的关系对缺失数据进行预测，生成多个完整的数据集，对这
        些数据集进行分析，最后对分析结果进行汇总处理
        1.2.4热平台插补----在非缺失数据集中找到一个与缺失值所在样本相似的样本（匹配样本），
        利用其中的观测值对缺失值进行插补。
        1.3建模法。
    2.异常值处理（去除不合理值、修正矛盾内容）
        2.1删除异常值 ---明显看出是异常且数量较少可以直接删除
        2.2不处理 ---如果算法对异常值不敏感则可以不处理
        2.3平均值替代 ---损失信息小，简单高效
        2.4视为缺失值 ---可以按照处理缺失值的方法来处理
    3.重复数据处理
    4.噪音数据处理
    5.关联性验证：数据有多个来源，有必要进行关联性验证。
    '''
    cleaned_data = list()
    for i in range(len(data)):
        # 1.不完整缺失数据处理：填充空的有用数和无用数为0
        if (data[i][2].strip() == '' or not (data[i][2].strip().isdigit())):
            data[i][2] = '0'
        if (data[i][3].strip() == '' or not (data[i][3].strip().isdigit())):
            data[i][3] = '0'
        # 2.异常值处理：未评分的，设为'无'
        if data[i][1].strip() not in ['力荐', '推荐', '还行', '较差', '很差']:
            data[i][1] = '无'
        # 4.噪音数据处理:Html标签清洗
        data[i][4] = get_html_text(data[i][4])
        # 3.重复数据处理
        if not data[i] in cleaned_data:
            cleaned_data.append(data[i])
    return cleaned_data
# 获取HTML文本内容
def get_html_text(html_text):
    bs = BeautifulSoup(html_text, 'lxml')
    return bs.text
# 生成词云
def get_WordCloud(WordCloud_text):
    print('开始生成词云...')
    WordCloud_text = ' '.join(jieba.cut(WordCloud_text))
    jieba.set_dictionary('./jieba_extra_dict/dict.txt.big')
    jieba.analyse.set_stop_words("./jieba_extra_dict/stop_words.txt")
    lf_wordcloud_text = WordCloud \
        (font_path=g_font_path_chs,
         width=800,
         height=600,
         max_words=200,
         min_font_size=4,
         max_font_size=100,
         stopwords=['因为', '这个', '还是', '一个', '不是', '就是', '可以',
                    '没有', '但是']
         ).generate_from_text(WordCloud_text)
    # 写入图片
    lf_wordcloud_text.to_file('WordCloud.jpg')
    print('生成词云完成！')
    # 1.图片方式显示：
    # image = lf_wordcloud_text.to_image()
    # image.show()
    # 2.matplotlib.pyplot方式显示：
    # plt.figure(figsize=(10, 8))
    # plt.subplot(121)
    font = matplotlib.font_manager.FontProperties(fname=g_font_path_chs)
    plt.title('词云图', fontproperties=font)
    plt.imshow(lf_wordcloud_text)
    plt.axis("off")
    plt.show()
# 获取百度AccessToken
def get_Baidu_AccessToken():
    auth_url = 'https://aip.baidubce.com/oauth/2.0/token?' \
               'grant_type=client_credentials&client_id={0}&client_secret={1}' \
        .format(g_BaiduNLP_API_KEY, g_BaiduNLP_SECRET_KEY)
    auth_request = urllib.request.Request(auth_url, method='POST')
    auth_request.add_header('Content-Type', 'application/json;charset=UTF-8')
    auth_response = urllib.request.urlopen(auth_request)
    auth_content = auth_response.read().decode('utf-8')
    auth_content_access_token = json.loads(auth_content)['access_token']
    return auth_content_access_token
# 获取百度自然语言处理情感倾向分析结果
def get_BaiduNLP_Sentiment_Classify(text, AccessToken):
    api_url = 'https://aip.baidubce.com/rpc/2.0/nlp/v1/sentiment_classify' \
              '?access_token={0}'.format(AccessToken)
    api_body_data = dict()
    # API限制：文本内容（GBK编码）最大2048字节
    if (len(text) >= 512):
        api_body_data['text'] = text[:512].encode(encoding='gbk',
                                                  errors='ignore').decode(
            'gbk')
        # print('情感倾向分析文本共有{0}字节（超过2048字节），截取后的新文本有'
        #       '{1}字节，超出部分被舍弃！文本内容为：{2}'.
        #       format(len(text) * 4, len(api_body_data['text']) * 4, text))
    else:
        api_body_data['text'] = text.encode(encoding='gbk', errors='ignore') \
            .decode('gbk')
    api_body_data_json = json.dumps(api_body_data).encode('gbk')
    api_request = urllib.request.Request(api_url, data=api_body_data_json,
                                         method='POST')
    api_request.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(api_request) as api_response:
            api_content = api_response.read().decode('gbk')
            api_content_items = json.loads(api_content)['items']
    except urllib.error.URLError as e:
        print('发生错误，正在重试...错误信息：%s' % e)
        return get_BaiduNLP_Sentiment_Classify(text, AccessToken)
    # QPS限制:5
    time.sleep(5 / 1000)
    return api_content_items[0]['positive_prob']
# 生成影评情感倾向分析图
def get_SentimentAnalysis_Image(shortcontent_list, sentiment_analysis_method):
    print('开始生成影评情感倾向分析图...')
    start_time = time.time()
    sentiments_list = list()
    if (sentiment_analysis_method == 'SnowNLP'):
        for i in shortcontent_list:
            if (len(i) > 0):
                s = SnowNLP(i)
                sentiments_list.append(s.sentiments)
                # print('积极概率：%f，短评：%s.' % (s.sentiments, i))
    elif (sentiment_analysis_method == 'BaiduNLP'):
        access_token = get_Baidu_AccessToken()
        j = 0
        for i in shortcontent_list:
            if (len(i) > 0):
                baidu_sentiments = \
                    get_BaiduNLP_Sentiment_Classify(i, access_token)
                if (baidu_sentiments != '0'):
                    sentiments_list.append(baidu_sentiments)
                    j += 1
                    print('共%s条影评，已获取第%s条百度自然语言处理情感倾向'
                          '分析结果，%0.2f%%完成...' % (len(shortcontent_list)
                                                 , j, j / len(
                        shortcontent_list) * 100))
    elif (sentiment_analysis_method == 'TencentNLP'):
        access_token = get_Baidu_AccessToken()
        j = 0
        for i in shortcontent_list:
            if (len(i) > 0):
                baidu_sentiments = \
                    get_BaiduNLP_Sentiment_Classify(i, access_token)
                if (baidu_sentiments != '0'):
                    sentiments_list.append(baidu_sentiments)
                    j += 1
                    print('共%s条影评，已获取第%s条百度自然语言处理情感倾向'
                          '分析结果，%0.2f%%完成...' % (len(shortcontent_list)
                                                 , j, j / len(
                        shortcontent_list) * 100))
    else:
        return
    sentiments_list_only = list(set(sentiments_list))  # 情感概率列表
    sentiments_list_only.sort()
    list_number = list()  # 情感概率数量列表
    s_list_number = list()  # 散点图面积
    for i in sentiments_list_only:
        list_number.append(sentiments_list.count(i))
        s_list_number.append(sentiments_list.count(i) * 2)

    font = matplotlib.font_manager.FontProperties(fname=g_font_path_chs)

    # 散点图
    # plt.subplot(121)
    # plt.scatter(
    #     sentiments_list_only,
    #     list_number,
    #     s=s_list_number,
    #     marker="*",
    #     alpha=0.5)
    # font = matplotlib.font_manager.FontProperties(fname=g_font_path_chs)
    # plt.title('影评情感倾向分析散点图', fontproperties=font)
    # plt.xlabel('积极概率(越接近1表示正面积极情绪，越接近0表示负面消极情绪)',
    #            fontproperties=font)
    # plt.ylabel('样本数量(标记面积越大样本数量越多)', fontproperties=font)
    # plt.grid(True)

    # 直方图
    plt.subplot(121)
    sentiments_positive_coutlist = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for i in sentiments_list_only:
        if (0.0 < round(float(i), 1) <= 0.1):
            sentiments_positive_coutlist[0] = sentiments_positive_coutlist[
                                                  0] + 1
        elif (0.1 < round(float(i), 1) <= 0.2):
            sentiments_positive_coutlist[1] = sentiments_positive_coutlist[
                                                  1] + 1
        elif (0.2 < round(float(i), 1) <= 0.3):
            sentiments_positive_coutlist[2] = sentiments_positive_coutlist[
                                                  2] + 1
        elif (0.3 < round(float(i), 1) <= 0.4):
            sentiments_positive_coutlist[3] = sentiments_positive_coutlist[
                                                  3] + 1
        elif (0.4 < round(float(i), 1) <= 0.5):
            sentiments_positive_coutlist[4] = sentiments_positive_coutlist[
                                                  4] + 1
        elif (0.5 < round(float(i), 1) <= 0.6):
            sentiments_positive_coutlist[5] = sentiments_positive_coutlist[
                                                  5] + 1
        elif (0.6 < round(float(i), 1) <= 0.7):
            sentiments_positive_coutlist[6] = sentiments_positive_coutlist[
                                                  6] + 1
        elif (0.7 < round(float(i), 1) <= 0.8):
            sentiments_positive_coutlist[7] = sentiments_positive_coutlist[
                                                  7] + 1
        elif (0.8 < round(float(i), 1) <= 0.9):
            sentiments_positive_coutlist[8] = sentiments_positive_coutlist[
                                                  8] + 1
        elif (0.9 < round(float(i), 1) <= 1.0):
            sentiments_positive_coutlist[9] = sentiments_positive_coutlist[
                                                  9] + 1
    plt.hist(sentiments_list, bins=10, range=(0, 1.0), facecolor='r',
             alpha=0.75)
    plt.title('影评情感倾向直方图', fontproperties=font)
    plt.xlabel('积极概率\n(越接近1表示正面积极情绪越强烈，'
               '越接近0表示负面消极情绪强烈)', fontproperties=font)
    plt.ylabel('样本数量', fontproperties=font)
    plt.axis(xmin=0.0, ymin=0, xmax=1.0)
    plt.grid(True)
    plt.tight_layout()

    # 饼形图
    plt.subplot(122)
    plt.rcParams['font.sans-serif'] = 'SimHei'  # 饼形图中文字体,微软雅黑
    sentiments_positive_cout = 0
    for i in sentiments_list_only:
        if (round(float(i), 1) > 0.5):
            sentiments_positive_cout = sentiments_positive_cout + 1
    pie_x = [sentiments_positive_cout,
             (len(sentiments_list_only) - sentiments_positive_cout)]
    pie_labels = ['正面积极情感', '负面消极情感']
    pie_colors = ['#6ad845', '#f8c42e']
    plt.pie(pie_x, labels=pie_labels, colors=pie_colors, autopct='%3.1f%%',
            labeldistance=1, startangle=90, counterclock=False)
    plt.title('影评情感倾向饼形图', fontproperties=font)
    plt.legend()
    end_time = time.time()
    print('生成影评情感倾向分析图完成,处理影评情感倾向分析数据耗时%s秒!' %
          (end_time - start_time))
    plt.show()
# 获取用户评分算术平均分
def get_user_arithmetic_average_rating_info(cleaned_data):
    # 按五种评分（1~5分）乘以2换算至十分制，未评分用户不计入总人数
    ratings_dict = {'力荐': 5 * 2, '推荐': 4 * 2, '还行': 3 * 2,
                    '较差': 2 * 1, '很差': 1 * 1, '无': 0}
    ratings_dict.setdefault('无')
    total_user_ratings = 0
    total_user_number = 0
    for i in range(len(cleaned_data)):
        if (ratings_dict.get(cleaned_data[i][1]) != 0):
            total_user_ratings += ratings_dict.get(cleaned_data[i][1])
            total_user_number += 1
    arithmetic_average_ratings = total_user_ratings / total_user_number
    print('用户评分（算术平均分）为：%0.1f,其中总分:%0.1f，用户数:%d人。' % (
        arithmetic_average_ratings, total_user_ratings, total_user_number))
# 主函数
def main():
    # 1.数据抓取(抓取完毕注释关闭)
    if(os.path.exists('movie_info.csv') == True):
        os.remove('movie_info.csv')
    if(os.path.exists('WordCloud.jpg') == True):
        os.remove('WordCloud.jpg')
    get_all_movie_info(g_response_moive_id)
    # 2.数据清洗
    data = read_from_csv_to_list('movie_info.csv')
    cleaned_data = cleaning_data(data)
    # 3.数据分析(3项数据分析可单独禁用)
    #   3.1生成词云
    WordCloud_text = str()
    for i in range(len(cleaned_data)):
        WordCloud_text += cleaned_data[i][4].strip() + ' '
    get_WordCloud(WordCloud_text)
    #   3.2影评文本情感倾向分析
    shortcontent_list = list()
    for i in range(len(cleaned_data)):
        if (len(cleaned_data[i][4]) != 0):
            shortcontent_list.append(cleaned_data[i][4])
    get_SentimentAnalysis_Image(shortcontent_list, 'BaiduNLP')
    #   3.3用户评分（算术平均分）计算:
    get_user_arithmetic_average_rating_info(cleaned_data)


main()
