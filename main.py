# -*- coding:utf-8 -*-
import multiprocessing
import random
from datetime import datetime, time
from time import sleep
from time import time as times
import os
from urllib import parse
import json
import requests


# ！！！请填写下面的参数
# 填写用户名和密码，以便登录
username = ''
password = ''
# uid为用户id
uid = ''
# 此三项为签到参数，经纬度和真实姓名
latitude = '-1'
longitude = '-1'
name = ''
# 下面三项一般不需要修改
clientip = ''
signuseragent = ''
# 图片签到所需要的objectId，具体ID可抓包获得
objectId = 'a58cb2acedf5fa10d2ad2fc421fb7d30'

# 每次课的上课时间
start_time = {
    time(8, 0),
    time(10, 0),
    time(13, 30),
    time(15, 30),
}
# 监听时长，例如设为20，就从每次上课开始监听20分钟
listen_time = 20
# 星期几上课，特殊：星期天是0
start_day = [1, 2, 3, 4, 5]

# 从这里开始不需要修改
useragent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_4_1 like Mac OS X) ' \
            'AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 ' \
            'ChaoXingStudy/ChaoXingStudy_3_4.4.1_ios_phone_202004111750_39 (@Kalimdor)_4375872153618237766 ' \
            'ChaoXingStudy/ChaoXingStudy_3_4.4.1_ios_phone_202004111750_39 (@Kalimdor)_4375872153618237766'
encode_name = parse.quote(name)
cookie_filename = 'chaoxing_cookies'
header = {
    'Cookie': '',
    'User-Agent': useragent
}


def myprint(string):
    print(datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S') + '  ' + string)


def getCookies():
    myprint('正在登录，获取新Cookie')
    if username and password:
        url = 'https://passport2-api.chaoxing.com/v11/loginregister'
        payload = {
            'uname': username,
            'code': password
        }
        cookie_jar = requests.session().post(url=url, data=payload, headers={'User-Agent': useragent}).cookies
        cookie_dict = requests.utils.dict_from_cookiejar(cookie_jar)
        cookie_str = ''
        for key in cookie_dict:
            cookie_str += key + '=' + cookie_dict[key] + '; '
        header['cookie'] = cookie_str
        with open(cookie_filename, 'w', encoding='utf-8')as file:
            file.write(cookie_str)
        myprint('获取Cookie成功')
    else:
        myprint('plz edit username and password in this python file')


def loadCookie():
    if os.path.exists(cookie_filename):
        with open(cookie_filename, 'r', encoding='utf-8') as f:
            data = f.read().strip()
            if data:
                header['cookie'] = data
            else:
                getCookies()
    else:
        getCookies()


should_run = False
coursedata = []
activates = []
timestamp: float = 0


def listenThread():
    global should_run
    while should_run:
        def backClassData():
            cdata = {}
            url = 'http://mooc1-api.chaoxing.com/mycourse/backclazzdata?view=json&rss=1'
            while not cdata:
                res = requests.get(url, headers=header)
                res_data = res.text
                if '请重新登录' in res_data:
                    getCookies()
                    continue
                try:
                    cdata = json.loads(res_data)
                except json.JSONDecodeError:
                    myprint('Cookie已失效，将重新获取')
                    getCookies()
                    continue
                if not cdata:
                    getCookies()
                    continue
                if cdata['result'] != 1:
                    myprint('课程列表获取失败')
                    sleep(10)
                    continue
                for item in cdata['channelList']:
                    if 'course' not in item['content']:
                        continue
                    pushdata = {'courseid': item['content']['course']['data'][0]['id'],
                                'name': item['content']['course']['data'][0]['name'],
                                'imageurl': item['content']['course']['data'][0]['imageurl'],
                                'classid': item['content']['id']}
                    coursedata.append(pushdata)
                myprint('课程获取成功\n')
                printCourseData()

        def printCourseData():
            global coursedata
            for index, item in enumerate(coursedata):
                print(str(index + 1) + "." + item['name'])
            startSign()

        def taskActiveList(courseId, classId):
            url = 'https://mobilelearn.chaoxing.com/ppt/activeAPI/taskactivelist?' \
                  'courseId=' + str(courseId) + \
                  '&classId=' + str(classId) + \
                  '&uid=' + uid
            res = requests.get(url, headers=header)
            data_json = json.loads(res.text)
            activeList = data_json['activeList']
            for item in activeList:
                if 'nameTwo' not in item:
                    continue
                if item['activeType'] == 2 and item['status'] == 1:
                    signurl = item['url']
                    aid = getVar(signurl)
                    if aid not in activates:
                        myprint('待签到活动 名称:%s 状态:%s 时间:%s ' % (item['nameOne'], item['nameTwo'], item['nameFour']))
                        sign(aid, uid, courseId)

        def getVar(url):
            var1 = url.split('&')
            for var in var1:
                var2 = var.split('=')
                if var2[0] == 'activePrimaryId':
                    return var2[1]
            return 'notfound'

        def sign(aid, uid, courseid):
            global should_run, activates
            url = 'https://mobilelearn.chaoxing.com/pptSign/stuSignajax?' \
                  'activeId=' + aid + \
                  '&uid=' + uid + \
                  '&clientip=' + clientip + \
                  '&useragent=' + signuseragent +\
                  '&latitude=' + latitude + \
                  '&longitude=' + longitude + \
                  '&appType=15' + \
                  '&fid=2378' + \
                  '&objectId=' + objectId + \
                  '&name=' + encode_name
            res = requests.get(url, headers=header)
            course_name = ''
            for item in coursedata:
                if item['courseid'] == courseid:
                    course_name = item['name']
            if res.text == 'success':
                myprint(course_name + ': 签到成功！')
                activates.append(aid)
                sleep(60)
                should_run = False
            elif res.text == '您已签到过了':
                myprint(course_name + ': 您已签到过了')
                activates.append(aid)
                sleep(60)
                should_run = False
            else:
                myprint(course_name + ': 签到失败')
                activates.append(aid)

        def startSign():
            global should_run
            while should_run:
                print('\n')
                for item in coursedata:
                    myprint('正在监听: ' + str(item['name']))
                    taskActiveList(item['courseid'], item['classid'])
                    sleep(3.7)
                    if not should_run:
                        break
                if should_run:
                    sleep(random.randint(37, 88))
            myprint('任务结束')

        backClassData()


def listen():
    myprint('主程序启动')
    child_process = None
    global should_run, timestamp
    loadCookie()

    while True:
        current_time = datetime.now().strftime('%H:%M')
        weekday = datetime.now().strftime('%w')

        if int(weekday) in start_day:
            for item in start_time:
                if str(item)[:-3] == current_time:
                    timestamp = times()
                    should_run = True
                if should_run and times() - timestamp > 60 * listen_time:
                    should_run = False

        if should_run and child_process is None:
            myprint('监听开始\n')
            child_process = multiprocessing.Process(target=listenThread)
            child_process.start()

        if not should_run and child_process is not None:
            myprint('监听结束\n')
            child_process.terminate()
            child_process.join()
            child_process = None

        sleep(10)


if __name__ == '__main__':
    try:
        listen()
    except KeyboardInterrupt:
        myprint('主动停止运行')
