import wanted

# init의 parameter 는 begin / daily 로 나뉨
# begin은 가장 최신 등록 공고 ~ IT공고를 원하는 개수만큼 크롤링 하는것
# daily 는 Sechedular로 매일 크롤링 하는것 (가장 최신 등록 공고 ~ 이전 마지막 크롤링 + 1)
wanted.init('daily')

