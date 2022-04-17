#-*- coding: utf-8 -*-

# Wanted 사이트를 크롤링하여 개발관련 인사이트를 제공하는 Project
# requests 로 받아온 해당 url 정보에서 txt로 이루어진 json 부분을 잘라내어서 활용

import os
import pathlib
import requests
import json
import datetime
import lang_analyze as la
from openpyxl import Workbook
from openpyxl.utils.exceptions import IllegalCharacterError

# settings by properties.json #
url_basic = None  # url 주소
max_streak = None  # 최대 미등록 공고 횟수. 높을수록 최신 공고 신뢰도가 높아짐
crawl_goal = None  # 크롤링으로 얻을 데이터 수
start_point = None  # 가장 최신공고 찾는 시작지점
min_text_length = None  # response.text 의 최소길이. 이 길이보다 길어야 모집중인 공고라고 판단
excel_save_path = None  # 엑셀저장경로

# global #
json_file = str(pathlib.Path(__file__).parent.absolute()) + '/properties.json'
crawl_count = 0  # GRAWL_GOAL 을 위한 Count
company_info_array = []  # 크롤링 회사 정보가 담길 배열
none_streak = 0  # 미등록 / 삭제 공고 연속
url = None  # 크롤링 진행중인 url (basic_url + wd)


# init #
def init(c_type):
    setting_by_json()
    latest_wd = find_latest()
    renew_json_file(latest_wd)
    if c_type == 'begin':  # 크롤링이 처음이라면 가장 최신 ~ 목표 크롤링 갯수까지 크롤링함
        crawl_to_goal(latest_wd)
    elif c_type == 'daily':  # 스케줄러로 매일 실행하게될 크롤링은 최신 ~ 이전 크롤링 까지 크롤링함
        crawl_to_start_point(latest_wd)

    make_excel()


# function #

# properties.json 으로 setting
def setting_by_json():
    global url_basic
    global max_streak
    global crawl_goal
    global start_point
    global min_text_length
    global json_file
    global excel_save_path

    with open(json_file, 'r') as f:
        json_data = json.load(f)

    settings_json = json_data['CrawlSettings']
    url_basic = settings_json['url_basic']
    max_streak = settings_json['max_streak']
    crawl_goal = settings_json['crawl_goal']
    start_point = settings_json['start_point']
    min_text_length = settings_json['min_text_length']
    excel_save_path = settings_json['excel_save_path']


# properties.json 의 start_point renew
def renew_json_file(new_latest):
    global json_file

    with open(json_file, 'r') as f:
        json_data = json.load(f)

    # 데이터 수정
    json_data['CrawlSettings']['start_point'] = new_latest + 1

    # 기존 json 파일 덮어쓰기
    with open(json_file, 'w') as f:
        json.dump(json_data, f)


# 최신 공고 url 번호 찾기
# 최신 공고번호 찾은 후 properties.json 의 start_point도 같이 갱신
def find_latest():
    global url_basic
    global none_streak
    global start_point
    global url

    i = 0
    while none_streak < max_streak:
        url = url_basic + str(start_point + i)
        response = requests.get(url)

        if len(response.text) < min_text_length:  # 미등록 or 삭제공고
            none_streak += 1
        else:
            none_streak = 0
        i += 1

    latest_point = start_point + i - max_streak - 1

    return latest_point


# 목표 개수만큼 크롤링
def crawl_to_goal(latest_wd):
    global company_info_array
    global crawl_count

    crawl_count = 0  # crawling 된 IT 공고 카운트
    i = 0

    while crawl_count < crawl_goal:
        insert_company_info(latest_wd - i)
        i += 1


# 최신 ~ strat_point(이전 최신글) 까지 크롤링
def crawl_to_start_point(latest_wd):
    global company_info_array
    global start_point

    i = 0

    while latest_wd - i > start_point:
        insert_company_info(latest_wd - i)
        i += 1


# company_info_array 에 IT 회사 정보 append
def insert_company_info(wd):
    global crawl_count

    try:
        company_info = get_company_info(get_json(wd))
    except Exception as e:
        # print('Error 발생 url : {}, log : {}'.format(url, e))
        company_info = None

    if company_info is not None:
        company_info_array.append(company_info)
        crawl_count += 1


# url 크롤링하여 얻은 회사정보를 json 변환
def get_json(wd):
    global url

    url = url_basic + str(wd)
    response = requests.get(url)
    html = response.text[-10000:]
    info_json = '{' + html[html.find(',"jobDetail"') + 1:html.find(',"theme')] + '}'  # 해당 페이지의 json

    if len(info_json) > 100:
        wanted_json = json.loads(info_json)
        wanted_json = wanted_json['jobDetail']['head'][str(wd)]
        return wanted_json
    else:  # request failed (모집종료된 공고)
        return None


# get_json에서 얻은 json 분석
def get_company_info(wanted_json):
    if wanted_json is None:
        return None

    global url

    category = wanted_json['category']
    if category != 'IT':  # 카테고리가 IT인 공고
        return None
    else:
        status = wanted_json['status']
        if status == 'active':
            status = '지원가능'
        elif status == 'draft':
            status = '지원마감'
        else:
            print('status 예외발생 url : {}, status : {}'.format(url, status))

        job_detail = str(wanted_json['jd'])
        prefer_start = job_detail.find('우대사항')  # 우대사항 필터
        prefer = ''
        if prefer_start > 0:  # 우대사항이 있다면
            prefer = job_detail[prefer_start + 5:job_detail.find('혜택') - 2].strip()
            prefer = prefer.replace('-', '•')
            prefer_lang = la.find_lang_from_jd(prefer)
        main_tasks = str(wanted_json['main_tasks']).replace('-', '•')  # 주요 업무
        main_tasks_lang = la.find_lang_from_jd(main_tasks)  # 주요 업무 프로그래밍 언어 필터
        requirements = str(wanted_json['requirements']).replace('-', '•')  # 자격요건
        requirements_lang = la.find_lang_from_jd(requirements)  # 자격 요건 프로그래밍 언어 필터

        company_info = {
            'url': url,
            '공고 작성일': wanted_json['confirm_time'][:10],
            '지원상태': status,
            '회사이름': wanted_json['company_name'],
            '지역': wanted_json['location'],
            '주요업무': main_tasks,
            '주요업무(언어)': main_tasks_lang,
            '자격요건': requirements,
            '자격요건(언어)': requirements_lang,
            '우대사항': prefer,
            '우대사항(언어)': prefer_lang
        }

    return company_info


# 회사정보를 통한 엑셀 파일 생성
def make_excel():
    global company_info_array

    if len(company_info_array) == 0:  # 배열에 IT 공고를 하나도 추가하지 못했다면
        print('크롤링 범위에 해당하는 IT 공고가 없어 엑셀이 만들어지지 않았습니다')
        return None

    # IT 공고 excel 파일 만들기
    write_wb = Workbook()  # openpyxl
    write_ws = write_wb.active

    # 컬럼 생성
    write_ws.append(list(company_info_array[0].keys()))

    # 크롤링 내용 삽입
    for company in company_info_array:
        excel_insert = []
        for value in company.values():
            excel_insert.append(value)
        try:
            write_ws.append(excel_insert)
        except IllegalCharacterError as e:  # 가끔 excel 형식의 Unicode에 맞지않는 문자가 포함된 공고가 있어서 예외처리
            print('IllegalCharacterError from {}'.format(excel_insert))

    # 엑셀 저장
    now = datetime.datetime.now()
    now_date = now.strftime('%Y%m%d')
    # path = os.path.abspath(__file__)[:-10] + 'excel/'  # 저장경로는 프로젝트 폴더내의 excel 폴더

    if not os.path.exists(excel_save_path):  # 폴더 없으면 만들기
        os.makedirs(excel_save_path)

    excel_title = excel_save_path + now_date + '.xlsx'

    write_wb.save(excel_title)
