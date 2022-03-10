# 원티드 사이트 IT 카테고리 공고의 주요업무, 자격요건, 우대사항 저장
# 언어, 프레임워크 툴 등을 분류할 키워드를 얻기 위함
import os

# 프로그래밍 언어 앞뒤에 올 수 있는 단어 필터
BEFORE_LETTER = [',', ' ', '/', '\n', '•', '(']
NEXT_LETTER = [',', '', ' ', '에', '/', '등', '관', '개', '\n', '.js', 'js', '과', '와', ')']


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
        jd_temp = jd
        while lang_index > 0:
            if jd_temp[lang_index + len(l)] in NEXT_LETTER and jd_temp[lang_index - 1] in BEFORE_LETTER:
                if jd_lang == '':
                    jd_lang += l
                else:
                    jd_lang += ', ' + l
            jd_temp = jd_temp[lang_index + 1:]
            lang_index = jd_temp.find(l)


    return jd_lang
