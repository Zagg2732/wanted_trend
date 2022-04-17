#-*- coding: utf-8 -*-

import sys
import wanted

# init의 parameter 는 begin / daily 로 나뉨
# begin은 가장 최신 등록 공고 ~ IT공고를 원하는 개수만큼 크롤링 하는것
# daily 는 Sechedular로 매일 크롤링 하는것 (가장 최신 등록 공고 ~ 이전 마지막 크롤링 + 1)
try:
    c_type = sys.argv[1]  # 프로젝트 실행시 argv로 받아서 사용
except IndexError as e:
    c_type = 'daily'

wanted.init(sys.argv[1])
