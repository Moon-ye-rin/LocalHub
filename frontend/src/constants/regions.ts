export type PostRegion = '서울' | '경기'

export const SEOUL_DISTRICTS = [
  '강남구', '강동구', '강북구', '강서구', '관악구', '광진구', '구로구', '금천구',
  '노원구', '도봉구', '동대문구', '동작구', '마포구', '서대문구', '서초구', '성동구',
  '성북구', '송파구', '양천구', '영등포구', '용산구', '은평구', '종로구', '중구', '중랑구',
] as const

export const GYEONGGI_MUNICIPALITIES = [
  '가평군', '고양시', '과천시', '광명시', '광주시', '구리시', '군포시', '김포시',
  '남양주시', '동두천시', '부천시', '성남시', '수원시', '시흥시', '안산시', '안성시',
  '안양시', '양주시', '양평군', '여주시', '연천군', '오산시', '용인시', '의왕시',
  '의정부시', '이천시', '파주시', '평택시', '포천시', '하남시', '화성시',
] as const

export const REGION_OPTIONS: Array<{ value: PostRegion; label: string }> = [
  { value: '서울', label: '서울' },
  { value: '경기', label: '경기' },
]

export function getDistrictOptions(region: PostRegion): readonly string[] {
  return region === '서울' ? SEOUL_DISTRICTS : GYEONGGI_MUNICIPALITIES
}

export function formatPostRegion(region?: string | null, district?: string | null): string {
  if (!region || !district) return '지역 미지정'
  return region === '경기' ? `경기도 ${district}` : `서울 ${district}`
}
