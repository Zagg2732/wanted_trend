# 원티드 사이트 IT 카테고리 공고의 주요업무, 자격요건, 우대사항 저장
# 언어, 프레임워크 툴 등을 분류할 키워드를 얻기 위함
import os

import wanted

NEXT_LETTER = [',', '', ' ', '에', '/', '등', '관', '개', '\n', '.js', 'js', '과', '와']  # 언어 다음에 오는 단어의 모음. 프로그래밍 언어를 찾았을때 다음글자를 체크해서 언어인지 확인
BEFORE_LETTER = [',', ' ', '/', '\n', '•']


def init():
    print('init')


def get_lang_from_txt():
    path = os.path.abspath(__file__)[:-15] + 'languages.txt'
    f = open(path, 'r')
    line = f.readline()
    lang = line.split(', ')
    f.close()

    return lang


# 주요업무, 자격요건 / 우대사항에 있는 프로그래밍 언어 찾기
def find_lang_from_jd(jd):
    jd = jd.lower()
    lang = get_lang_from_txt()
    jd_lang = ''
    for l in lang:
        l = l.lower()
        lang_index = jd.find(l)
        if lang_index > 0:
            if jd[lang_index + len(l)] in NEXT_LETTER and jd[lang_index - 1] in BEFORE_LETTER:
                if jd_lang == '':
                    jd_lang += l
                else:
                    jd_lang += ', ' + l

    return jd_lang
