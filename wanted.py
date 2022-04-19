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
from collections import deque

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
crawling_text_array = []  # 최근 공고 탐색중 얻는 response.text array
wanted_json_array = []    # response.text 에서 얻은 json array
company_info_array = []  # 크롤링 회사 정보가 담길 배열
none_streak = 0  # 미등록 / 삭제 공고 연속
latest_point = 0  # 가장 최근 공고 글번호
url = None  # 크롤링 진행중인 url (basic_url + wd)


# init #
def init(c_type):
    global crawling_text_array
    global crawl_goal
    global wanted_json_array

    setting_by_json()  # properties.json 의 설정 가져오기
    crawl_to_latest()  # 이전 크롤링 지점 ~ 가장 최근 공고까지 크롤링
    res_text_array_to_json() # json 형태로 변환후 IT 카테고리만 배열에 추가

    if c_type == 'begin':  # begin : 최근공고 ~ 목표 크롤링 개수까지 크롤링
        if len(wanted_json_array) >= crawl_goal:  # 최근공고를 찾는동안 채워진 array가 목표를 넘는다면 자름
            crawling_text_array = crawling_text_array[-crawl_goal:]
        else:  # 목표개수를 채울때까지 크롤링
            crawl_to_goal()

    make_company_info_array()   # json -> company_info dict 형태로 저장
    make_excel()                # 엑셀 파일 생성
    renew_json_file()           # 가장 최근 공고 + 1 을 다음 크롤링 시작지점으로 저장


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
    excel_save_path = settings_json['excel_save_path']
    min_text_length = get_min_text_len()


# 내용이 없는 공고 필터 기준
def get_min_text_len():
    min_url = url_basic + str(1000000000000)  # min_url 원리 : 내용이 없는 공고 response.text 길이를 구함. 공고의 기본 구성 길이보다 길면 내용이 있는 공고
    response = requests.get(min_url)
    return len(response.text) + 200


# properties.json 의 start_point renew
def renew_json_file():
    global json_file
    global latest_point

    with open(json_file, 'r') as f:
        json_data = json.load(f)

    # 데이터 수정
    json_data['CrawlSettings']['start_point'] = latest_point + 1

    # 기존 json 파일 덮어쓰기
    with open(json_file, 'w') as f:
        json.dump(json_data, f)


# 최신 공고 url 번호 찾기
# 최신 공고를 찾는동안 받은 response.text는 array에 넣음
# 최신 공고번호 찾은 후 properties.json 의 start_point도 같이 갱신
def crawl_to_latest():
    global none_streak
    global start_point
    global latest_point

    i = 0
    while none_streak < max_streak:  # max_streak은 내용없는 공고의 연속개수이며 크롤링 끝내는 조건으로 활용중
        wd = start_point + i

        is_streak = crawl_by_wd(wd)

        if not is_streak:  # 미등록 or 삭제공고
            none_streak += 1
        else:
            none_streak = 0
        i += 1

    latest_point = start_point + i - max_streak - 1


# 목표 개수 채울때까지 크롤링
def crawl_to_goal():
    global start_point
    global crawl_goal
    global wanted_json_array
    global url_basic

    wanted_json_array = deque(wanted_json_array)    # appendleft(prepend)를 위해 dequq 형태로 변환

    remain_goal = crawl_goal - len(wanted_json_array) # 남은 IT공고 크롤링 수

    i = 0
    while remain_goal > 0:
        wd = start_point - i
        res_text = crawl_by_wd_backward(wd)

        if res_text == '': # 내려간 공고
            i += 1
            continue

        res_text_json = '{' + res_text[res_text.find(',"jobDetail"') + 1:res_text.find(',"theme')] + '}'  # 해당 페이지의 json

        if res_text_json[:12] == '{"jobDetail"' and len(res_text_json) > 100:
            res_text_json = json.loads(res_text_json)   # json 변환
            res_text_json = res_text_json['jobDetail']['head'][str(wd)]

        if res_text_json['category'] == 'IT':  # IT 카테고리면 json_array에 넣어줌
            res_text_json['url'] = url_basic + str(wd)
            wanted_json_array.appendleft(res_text_json)
            remain_goal -= 1
        i += 1
    wanted_json_array = list(wanted_json_array) # deque -> list 변환


# wd (글번호) 를 통한 크롤링 정보 담기
def crawl_by_wd(wd):
    global crawling_text_array

    url = url_basic + str(wd)
    response = requests.get(url)

    if len(response.text) < min_text_length:  # 미등록 or 삭제공고
        return False
    else:
        res_info = {wd: response.text}
        crawling_text_array.append(res_info)  # 내용있는 공고면 크롤링 text 리스트에 추가
        return True


# 크롤링 기준점 이전으로 크롤링
def crawl_by_wd_backward(wd):
    url = url_basic + str(wd)
    response = requests.get(url)

    if len(response.text) < min_text_length:  # 미등록 or 삭제공고
        return ''
    else:
        return response.text


# url 크롤링하여 얻은 회사정보를 json 변환
def res_text_array_to_json():
    global crawling_text_array

    for res_info in crawling_text_array:
        for wd in res_info.keys():
            text = res_info[wd][-10000:]
            info_json = '{' + text[text.find(',"jobDetail"') + 1:text.find(',"theme')] + '}'  # 해당 페이지의 json

            if info_json[:12] == '{"jobDetail"' and len(info_json) > 100:
                wanted_json = json.loads(info_json)
                wanted_json = wanted_json['jobDetail']['head'][str(wd)]
                if wanted_json['category'] == 'IT':
                    wanted_json['url'] = url_basic + str(wd)
                    wanted_json_array.append(wanted_json)


# wanted_json_array 의 json을 분석하여 원하는 정보를 company_info 라는 dict 형태로 저장
def make_company_info_array():
    global wanted_json_array

    for wanted_json in wanted_json_array:
        if wanted_json is None:
            return None

        status = wanted_json['status']
        if status == 'active':
            status = '지원가능'
        elif status == 'draft':
            status = '지원마감'
        else:
            print('status 예외발생 json'.format(wanted_json))

        job_detail = str(wanted_json['jd'])
        prefer_start = job_detail.find('우대사항')  # 우대사항 필터
        prefer = ''
        prefer_lang = ''
        if prefer_start > 0:  # 우대사항이 있다면
            prefer = job_detail[prefer_start + 5:job_detail.find('혜택') - 2].strip()
            prefer = prefer.replace('-', '•')
            prefer_lang = la.find_lang_from_jd(prefer)

        main_tasks = str(wanted_json['main_tasks']).replace('-', '•')  # 주요 업무
        main_tasks_lang = la.find_lang_from_jd(main_tasks)  # 주요 업무 프로그래밍 언어 필터
        requirements = str(wanted_json['requirements']).replace('-', '•')  # 자격요건
        requirements_lang = la.find_lang_from_jd(requirements)  # 자격 요건 프로그래밍 언어 필터

        if wanted_json['confirm_time'] is None:  # 아주 가끔 confirm_time이 None 인 공고가 있음
            now = datetime.datetime.now()
            today = now.strftime('%Y-%m-%d')
            wanted_json['confirm_time'] = today

        company_info = {
            'url': wanted_json['url'],
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
        company_info_array.append(company_info)


# company_info_array를 통한 엑셀 파일 생성
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

    if not os.path.exists(excel_save_path):  # 폴더 없으면 만들기
        os.makedirs(excel_save_path)

    excel_title = excel_save_path + now_date + '.xlsx'

    write_wb.save(excel_title)
