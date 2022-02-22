# Wanted 사이트를 크롤링하여 개발관련 인사이트를 제공하는 Project

import requests
import json


company_info_array = [] # 크롤링 회사 정보가 담길 배열


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

    print(company_info_array)


# function #
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
        wanted_json = json.loads(info_json)
        wanted_json = wanted_json['jobDetail']['head'][str(i)]
        location = wanted_json['location']            # 지역
        company_name = wanted_json['company_name']    # 회사이름
        # main_tasks = wanted_json['main_tasks']      # 주요업무
        # requirements = wanted_json['requirements']  # 자격요건

    return [location, company_name]


def get_lang_by_jd(jd):  # 사용언어들 추출하기
    print('job details = {}'.format(jd.replace("\\n", "\n")))


# init #
init()
