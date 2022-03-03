# Wanted 사이트를 크롤링하여 개발관련 인사이트를 제공하는 Project

import os
import requests
import json
import datetime
from openpyxl import Workbook

company_info_array = []  # 크롤링 회사 정보가 담길 배열
URL_BASIC = 'https://www.wanted.co.kr/wd/'
url = None

# init #
def init():
    for i in range(44900, 44910, 1):  # 사이트 크롤링 범위. 현재 테스트로 range 값 지정한 상태 (추후 크롤링 범위 수정 및 함수화)
        try:
            company_info = get_company_info(get_json(i))
        except Exception as e:
            # print('Error 발생 url : {}, log : {}'.format(url, e))
            company_info = None

        if company_info is not None:
            company_info_array.append(company_info)
    if len(company_info_array) > 0:  # 배열에 IT 공고를 하나도 추가하지 못했다면
        make_excel(company_info_array)
    else:
        print('크롤링 범위에 해당하는 IT 공고가 없어 엑셀이 만들어지지 않았습니다')


# function #
# url 크롤링하여 얻은 회사정보 json
def get_json(i):
    global url
    url = URL_BASIC + str(i)
    response = requests.get(url)
    html = response.text[-10000:]
    info_json = '{' + html[html.find(',"jobDetail"') + 1:html.find(',"theme')] + '}'  # 해당 페이지의 json

    if len(info_json) > 100:
        wanted_json = json.loads(info_json)
        wanted_json = wanted_json['jobDetail']['head'][str(i)]
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
        prefer_start = job_detail.find('우대')
        prefer = ''
        if prefer_start > 0:
            prefer = job_detail[prefer_start + 5:job_detail.find('혜택')-2].strip()

        company_info = {
            '지원상태': status,
            '회사이름': wanted_json['company_name'],
            '지역': wanted_json['location'],
            '주요업무': wanted_json['main_tasks'],
            '자격요건': wanted_json['requirements'],
            '우대사항': prefer
        }

    return company_info


# 회사정보를 통한 엑셀 파일 생성
def make_excel(company_info):
    write_wb = Workbook()  # openpyxl
    write_ws = write_wb.active

    # 컬럼 생성
    write_ws.append(list(company_info[0].keys()))

    # 크롤링 내용 삽입
    for company in company_info:
        excel_insert = []
        for value in company.values():
            excel_insert.append(value)
        write_ws.append(excel_insert)

    # 엑셀 저장
    now = datetime.datetime.now()
    now_date = now.strftime('%Y%m%d_%H%M%S')
    path = os.path.abspath(__file__)[:-10] + '/excel/'  # 저장경로는 프로젝트 폴더내의 excel 폴더
    excel_title = path + 'wanted' + now_date + '.xlsx'

    write_wb.save(excel_title)


# init #
init()
