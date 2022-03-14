# Wanted 사이트를 크롤링하여 개발관련 인사이트를 제공하는 Project

import os
import requests
import json
import datetime
import lang_analyze as la
from openpyxl import Workbook
from openpyxl.utils.exceptions import IllegalCharacterError

# global #

URL_BASIC = 'https://www.wanted.co.kr/wd/'
MAX_STREAK = 50  # 최대 미등록 공고 횟수. 높을수록 최신 공고 신뢰도가 높아짐
CRAWL_GOAL = 200  # 크롤링으로 얻을 데이터 수

# crawl_start = 102160  # 크롤링 시작지점
crawl_count = 0       # GRAWL_GOAL 을 위한 Count
find_latest_start = 102219  # 가장 최신공고 찾는 시작지점

company_info_array = []  # 크롤링 회사 정보가 담길 배열
none_streak = 0  # 미등록 / 삭제 공고 연속
latest_url = 0
url = None
is_latest = False  # 크롤링 시작지점 ~ 가장 최근 공고까지 조회했는지 여부


# init #
def init():
    latest_wd = find_latest()
    init_crawl(latest_wd)
    make_excel()


# function #

# 최신 공고 url 번호 찾기
# find_latest_start 를 이 함수의 return 값 + 1로 계속 갱신요망
def find_latest():
    global URL_BASIC
    global none_streak
    global find_latest_start
    global url

    i = 0
    while none_streak < MAX_STREAK and is_latest is False:
        url = URL_BASIC + str(find_latest_start + i)
        response = requests.get(url)

        if len(response.text) < 342000:  # 미등록 or 삭제공고
            none_streak += 1
        else:
            none_streak = 0
        i += 1

    return find_latest_start + i - MAX_STREAK - 1


# 크롤링 범위
def init_crawl(wd):
    global company_info_array
    global crawl_count
    global is_latest

    crawl_count = 0  # crawling 된 IT 공고 카운트
    i = 0

    while crawl_count < CRAWL_GOAL:
        insert_company_info(wd - i)
        i += 1


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

    url = URL_BASIC + str(wd)
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
    now_date = now.strftime('%Y%m%d_%H%M%S')
    path = os.path.abspath(__file__)[:-10] + '/excel/'  # 저장경로는 프로젝트 폴더내의 excel 폴더
    excel_title = path + 'wanted' + now_date + '.xlsx'

    write_wb.save(excel_title)
