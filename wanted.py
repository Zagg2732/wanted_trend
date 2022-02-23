# Wanted 사이트를 크롤링하여 개발관련 인사이트를 제공하는 Project

import os
import requests
import json
import datetime
from openpyxl import Workbook

company_info_array = []  # 크롤링 회사 정보가 담길 배열


def init():
    for i in range(94690, 94700, 1):  # 사이트 크롤링 범위. 현재 테스트로 range 값 지정한 상태 (추후 크롤링 범위 수정)
        url = 'https://www.wanted.co.kr/wd/' + str(i)
        try:
            company_info = get_info(url, i)
        except Exception as e:
            print('Error 발생 url : {}, log : {}'.format(url, e))
            company_info = None

        if company_info is not None:
            company_info_array.append(company_info)
    make_excel(company_info_array)


# function #

# url 크롤링하여 얻은 회사정보
def get_info(url, i):
    response = requests.get(url)
    html = response.text
    info_json = '{' + html[html.find(',"jobDetail"') + 1:html.find(',"theme')] + '}'  # 해당 페이지의 json

    if len(info_json) > 100:  # request failed (모집종료된 공고)
        wanted_json = json.loads(info_json)
        wanted_json = wanted_json['jobDetail']['head'][str(i)]
        category = wanted_json['category']
    else:
        return None

    if category != 'IT':  # 카테고리가 IT인 회
        return None
    else:
        company_info = {}
        wanted_json = json.loads(info_json)
        wanted_json = wanted_json['jobDetail']['head'][str(i)]

        company_info['회사이름'] = wanted_json['company_name']
        company_info['지역'] = wanted_json['location']
        company_info['주요업무'] = wanted_json['main_tasks']
        company_info['자격요건'] = wanted_json['requirements']

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
    path = os.path.abspath(__file__)[:-10] + '/excel/' # 저장경로는 프로젝트 폴더내의 excel 폴더
    excel_title = path + 'wanted' + now_date + '.xlsx'

    write_wb.save(excel_title)


# init #
init()
