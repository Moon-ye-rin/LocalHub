import type { ComposerTranslation } from 'vue-i18n'

const CATEGORY_KEYS: Record<string, string> = {
  '12': 'categories.c12', '관광지': 'categories.c12',
  '14': 'categories.c14', '문화시설': 'categories.c14',
  '15': 'categories.c15', '축제공연행사': 'categories.c15', '축제': 'categories.c15',
  '25': 'categories.c25', '여행코스': 'categories.c25',
  '28': 'categories.c28', '레포츠': 'categories.c28',
  '32': 'categories.c32', '숙박': 'categories.c32',
  '38': 'categories.c38', '쇼핑': 'categories.c38',
  '39': 'categories.c39', '음식점': 'categories.c39', '맛집': 'categories.c39',
  '자유': 'categories.free',
}

const DISTRICT_EN: Record<string, string> = {
  '강남구':'Gangnam-gu','강동구':'Gangdong-gu','강북구':'Gangbuk-gu','강서구':'Gangseo-gu','관악구':'Gwanak-gu','광진구':'Gwangjin-gu','구로구':'Guro-gu','금천구':'Geumcheon-gu',
  '노원구':'Nowon-gu','도봉구':'Dobong-gu','동대문구':'Dongdaemun-gu','동작구':'Dongjak-gu','마포구':'Mapo-gu','서대문구':'Seodaemun-gu','서초구':'Seocho-gu','성동구':'Seongdong-gu',
  '성북구':'Seongbuk-gu','송파구':'Songpa-gu','양천구':'Yangcheon-gu','영등포구':'Yeongdeungpo-gu','용산구':'Yongsan-gu','은평구':'Eunpyeong-gu','종로구':'Jongno-gu','중구':'Jung-gu','중랑구':'Jungnang-gu',
  '가평군':'Gapyeong-gun','고양시':'Goyang-si','과천시':'Gwacheon-si','광명시':'Gwangmyeong-si','광주시':'Gwangju-si','구리시':'Guri-si','군포시':'Gunpo-si','김포시':'Gimpo-si',
  '남양주시':'Namyangju-si','동두천시':'Dongducheon-si','부천시':'Bucheon-si','성남시':'Seongnam-si','수원시':'Suwon-si','시흥시':'Siheung-si','안산시':'Ansan-si','안성시':'Anseong-si',
  '안양시':'Anyang-si','양주시':'Yangju-si','양평군':'Yangpyeong-gun','여주시':'Yeoju-si','연천군':'Yeoncheon-gun','오산시':'Osan-si','용인시':'Yongin-si','의왕시':'Uiwang-si',
  '의정부시':'Uijeongbu-si','이천시':'Icheon-si','파주시':'Paju-si','평택시':'Pyeongtaek-si','포천시':'Pocheon-si','하남시':'Hanam-si','화성시':'Hwaseong-si',
}

export function translateCategory(t: ComposerTranslation, value: string): string {
  const key = CATEGORY_KEYS[value]
  return key ? t(key) : value
}

export function translateRegion(t: ComposerTranslation, value?: string | null): string {
  if (value === '서울') return t('common.seoul')
  if (value === '경기') return t('common.gyeonggi')
  if (value === '전체') return t('common.all')
  return value || ''
}

export function translateDistrict(value: string, locale: string): string {
  return locale.startsWith('en') ? (DISTRICT_EN[value] || value) : value
}

export function formatRegionLabel(
  t: ComposerTranslation,
  locale: string,
  region?: string | null,
  district?: string | null,
): string {
  if (!region || !district) return locale.startsWith('en') ? 'Region not specified' : '지역 미지정'
  const districtLabel = translateDistrict(district, locale)
  if (locale.startsWith('en')) return region === '경기' ? `${districtLabel}, ${t('common.gyeonggi')}` : `${districtLabel}, ${t('common.seoul')}`
  return region === '경기' ? `경기도 ${district}` : `서울 ${district}`
}

export function localeCode(locale: string): string {
  return locale.startsWith('en') ? 'en-US' : 'ko-KR'
}
