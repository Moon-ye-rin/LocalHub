import { createI18n } from 'vue-i18n'

export type AppLocale = 'ko' | 'en'

const messages = {
  ko: {
    common: {
      home: '홈', board: '게시판', locations: '지역정보', dashboard: '대시보드', write: '글쓰기', newPost: '새 글 작성',
      all: '전체', seoul: '서울', gyeonggi: '경기', seoulGyeonggi: '서울·경기', search: '검색', category: '카테고리',
      sort: '정렬', latest: '최신순', viewsSort: '조회순', likesSort: '좋아요순', bookmark: '북마크', bookmarks: '북마크',
      comments: '댓글', likes: '좋아요', views: '조회', edit: '수정', delete: '삭제', cancel: '취소', confirm: '확인', save: '저장',
      loading: '불러오는 중...', processing: '처리 중...', reset: '초기화', anonymous: '익명', noAddress: '주소 미제공',
      source: '출처: 한국관광공사 · 공공누리 제3유형', postsUnit: '개의 게시글', locationsUnit: '개의 지역정보',
      count: '{count}개', score: '{score}점', commentsCount: '댓글 {count}개', addBookmark: '북마크 추가', removeBookmark: '북마크 해제', originalKorean: '원문 데이터',
    },
    header: {
      region: '서울·경기', notifications: '새 게시글 알림', connected: '실시간 연결됨', reconnecting: '재연결 중',
      emptyNotifications: '새로 등록된 게시글이 없습니다.', deleteNotification: '알림 삭제', online: '{count}명 접속',
      presence: '현재 {count}명 접속', mainMenu: '주요 메뉴', openMenu: '메뉴 열기', justNow: '방금 전',
      language: '언어', korean: '한국어', english: 'English',
    },
    footer: { description: '서울·경기 지역정보 공유 커뮤니티', license: '한국관광공사 TourAPI 4.0 · 공공누리 제3유형' },
    hero: {
      eyebrow: '서울·경기 지역정보를 한곳에', line1: '동네의 발견을', line2: '함께 나누는',
      description: '서울·경기 공공 관광정보를 찾고, 지역 생활 후기를 회원가입 없이 익명으로 공유하세요.',
      dataButton: '공공데이터 보기', communityButton: '커뮤니티 참여', linked: '실제 데이터 연동', count: 'TourAPI 12,512건',
    },
    home: {
      publicDataTitle: '서울·경기 실제 공공데이터', publicDataDesc: 'TourAPI 원본 12,512건', communityTitle: '익명 커뮤니티',
      communityDesc: '비밀번호 기반 게시글·댓글', chatbotTitle: '데이터 챗봇', chatbotDesc: '서울·경기 지역정보와 게시글을 함께 검색',
      recommend: '{region} 추천 관광정보', viewAll: '전체 보기', recentPosts: '최근 지역 후기', goBoard: '게시판 가기', selectRegion: '추천 지역 선택',
    },
    categories: {
      c12: '관광지', c14: '문화시설', c15: '축제공연행사', c25: '여행코스', c28: '레포츠', c32: '숙박', c38: '쇼핑', c39: '음식점', free: '자유',
    },
    board: {
      title: '서울·경기 익명 게시판', description: '회원가입 없이 지역의 발견과 후기를 자유롭게 공유해 보세요.',
      searchPlaceholder: '제목 또는 내용 검색', popularTags: '인기 태그', bookmarksOnly: '북마크', summary: '{count}개의 게시글',
      noResults: '검색 결과가 없습니다', noResultsDesc: '검색어나 필터를 바꾸거나 첫 게시글을 작성해 보세요.', resetFilters: '필터 초기화',
    },
    locations: {
      title: '{region} 공공 관광정보', description: '관광지, 문화시설, 축제, 숙박, 쇼핑과 음식점 정보를 한곳에서 찾아보세요.',
      cache: '서울·경기 SQLite 캐시 연동', searchPlaceholder: '{region} 장소명 또는 주소 검색', showAll: '전체 목록 보기', bookmarksOnly: '북마크만 보기',
      regionSelect: '지역 선택', contentType: '콘텐츠 유형', summary: '{count}개의 {label} 지역정보', bookmarkLabel: '{region} 북마크', totalLabel: '서울·경기 전체',
      noBookmarks: '북마크한 지역정보가 없습니다', noBookmarksDesc: '관심 있는 지역정보 카드의 북마크 버튼을 눌러 저장해 보세요.',
      notFound: '지역정보를 찾지 못했습니다', notFoundDesc: '지역, 검색어 또는 콘텐츠 유형을 변경해 보세요.', list: '지역정보 목록',
      rating: '평점 {count}개', map: '위치 지도', mapUnavailable: '위치 좌표가 제공되지 않아 지도를 표시할 수 없습니다.',
      mapAttribution: '지도 데이터 © OpenStreetMap contributors', nearby: '가까운 지역정보', nearbyDesc: '현재 장소를 기준으로 가까운 5곳입니다',
      reactionLabel: '지역정보 반응', reviewTitle: '별점과 댓글', reviewSummary: '평균 {rating} · {count}개 평가', nickname: '닉네임', nicknamePlaceholder: '미입력 시 익명',
      password: '수정·삭제용 비밀번호', passwordPlaceholder: '4자 이상', ratingLabel: '별점', zeroPoint: '0점', comment: '댓글', commentPlaceholder: '이 장소에 대한 경험이나 정보를 남겨 주세요.',
      submitReview: '댓글 등록', submitting: '등록 중...', loadingComments: '댓글을 불러오는 중입니다.', firstReview: '첫 번째 별점과 댓글을 남겨 보세요.', edited: '수정됨',
      editPassword: '작성 시 비밀번호', saving: '저장 중...', deleteCommentTitle: '지역정보 댓글 삭제', deleteCommentDesc: '댓글 작성 시 등록한 비밀번호를 입력해 주세요.',
      originalNotice: '관광정보 제목과 주소는 공공누리 변경금지 조건에 따라 한국어 원문으로 표시됩니다.',
    },
    post: {
      backBoard: '목록으로 돌아가기', reactionLabel: '게시글 반응', attachedImage: '게시글 첨부 이미지', ownerEdit: '수정', ownerDelete: '삭제',
      commentsTitle: '댓글', writeComment: '댓글 작성', commentPlaceholder: '게시글에 대한 의견이나 추가 정보를 남겨 주세요.',
      commentPassword: '댓글 비밀번호', commentPasswordPlaceholder: '수정·삭제용 비밀번호(4자 이상)', submitComment: '댓글 등록', submitting: '등록 중...',
      loadingComments: '댓글을 불러오는 중입니다.', firstComment: '첫 댓글을 남겨 보세요.', edited: '수정됨', editPasswordPlaceholder: '작성 시 비밀번호',
      deletePostTitle: '게시글 삭제', editPostTitle: '게시글 수정', deletePostDesc: '작성 시 등록한 비밀번호를 입력하면 게시글이 삭제됩니다.',
      editPostDesc: '작성 시 등록한 비밀번호를 입력하면 수정 화면으로 이동합니다.', deleteCommentTitle: '댓글 삭제', deleteCommentDesc: '댓글 작성 시 등록한 비밀번호를 입력해 주세요.',
    },
    form: {
      backPost: '게시글로 돌아가기', backBoard: '게시판으로 돌아가기', editTitle: '게시글 수정', newTitle: '새 게시글 작성',
      description: '익명으로 작성되며, 비밀번호는 수정·삭제에만 사용됩니다.', category: '카테고리', postRegion: '게시글 지역', metroRegion: '광역 지역',
      districtSeoul: '자치구', districtGyeonggi: '시·군', regionHelp: '대시보드의 인기 지역 순위 집계에 사용됩니다.', title: '제목', titlePlaceholder: '지역정보나 후기를 입력해 주세요',
      content: '내용', contentPlaceholder: '구체적인 장소와 경험을 공유해 주세요.', images: '이미지 첨부', chooseImages: '이미지를 선택하거나 추가하세요',
      imageHelp: 'JPG·PNG·GIF, 파일당 5MB 이하, 기존 이미지 포함 최대 {count}개', existingImage: '기존 첨부 이미지', deleteImage: '기존 첨부 이미지 삭제', deleting: '삭제 중...',
      existingDeleteHint: '기존 이미지 · X로 삭제', removeImage: '첨부 이미지 제거', tags: '태그', tagPlaceholder: '태그 입력', add: '추가', password: '수정용 비밀번호',
      passwordPlaceholder: '4자 이상 입력', saveLoading: '저장 중...', editComplete: '수정 완료', register: '게시글 등록', confirmImageDelete: '이 이미지를 게시글에서 삭제할까요? 삭제 후에는 복구할 수 없습니다.',
    },
    dashboard: {
      title: '서울·경기 커뮤니티 대시보드', description: '게시글, 댓글, 좋아요, 조회 기록을 실시간으로 집계합니다.', refresh: '새로고침',
      monthly: '월별 카테고리 게시글 현황', recentMonths: '최근 7개월 · 누적 막대', distribution: '카테고리별 분포', comparison: '전체·서울·경기 비교',
      posts: '게시글', noPosts: '집계할 게시글이 없습니다.', popularRegions: '인기 지역 순위', postCount: '게시글 {count}', commentCount: '댓글 {count}',
      likeCount: '좋아요 {count}', viewCount: '조회 {count}', noRegions: '지역을 선택해 게시글을 작성하면 순위가 집계됩니다.', popularLocations: '인기 지역정보',
      reactionBased: '사용자 반응 기반', noPopularLocations: '지역정보에 댓글·좋아요·조회 기록이 쌓이면 순위가 표시됩니다.', topRated: '평점 높은 지역정보',
      ratingAverage: '댓글 별점 평균순', noRatings: '별점 댓글이 등록되면 순위가 표시됩니다.', weeklyTrend: '주간 조회수 · 좋아요 트렌드', thisWeek: '이번 주 월요일~일요일',
      viewsDataset: '조회수', likesDataset: '좋아요', unitItems: '건', unitTimes: '회',
    },
    chat: {
      source: '출처: 한국관광공사 TourAPI 4.0 · 공공누리 제3유형', greeting: '안녕하세요! LocalHub 챗봇이에요 😊\n서울·경기 공공데이터와 커뮤니티 게시글을 검색해 드립니다.',
      quick1: '서울 관광지 추천', quick2: '종로구 문화시설', quick3: '서울 축제 정보', quick4: '한강 관련 게시글', assistant: 'AI 지역 도우미', title: 'LocalHub 챗봇',
      basedOnData: '실제 서울·경기 데이터 기반', clear: '대화 초기화', references: '참고한 정보', placeholder: '서울·경기 지역정보를 물어보세요', open: 'LocalHub 챗봇 열기',
    },
    share: {
      kakao: '카카오톡 공유', connecting: '연결 중', copy: '링크 복사', copied: '공유 링크를 복사했습니다.', copyFailed: '링크 복사에 실패했습니다.',
      keyMissing: '카카오 JavaScript 키를 frontend/.env에 설정해 주세요.', kakaoFailed: '카카오톡 공유에 실패했습니다.', viewAtLocalHub: 'LocalHub에서 보기', defaultDescription: 'LocalHub에서 지역정보를 확인해 보세요.', label: '소셜 공유',
    },
    pagination: { label: '페이지 이동', previous: '이전 {count}개 페이지', previousTitle: '이전 페이지 묶음', next: '다음 {count}개 페이지', nextTitle: '다음 페이지 묶음' },
    passwordModal: { close: '닫기', label: '수정용 비밀번호', placeholder: '비밀번호 입력' },
    notFound: { title: '페이지를 찾을 수 없습니다', description: '주소를 확인하거나 LocalHub 홈으로 돌아가 주세요.', home: '홈으로 이동' },
    errors: {
      postsLoad: '게시글 목록을 불러오지 못했습니다.', postLoad: '게시글을 불러오지 못했습니다.', locationsLoad: '지역정보를 불러오지 못했습니다.', dashboardLoad: '대시보드 데이터를 불러오지 못했습니다.',
      commentsLoad: '댓글을 불러오지 못했습니다.', like: '좋아요 처리에 실패했습니다.', bookmark: '북마크 처리에 실패했습니다.', chat: '챗봇 응답을 가져오지 못했습니다.',
      commentRequired: '댓글 내용을 입력해 주세요.', commentPassword: '댓글 비밀번호는 4자 이상 입력해 주세요.', locationCommentPassword: '수정·삭제용 비밀번호를 4자 이상 입력해 주세요.',
      commentCreate: '댓글 등록에 실패했습니다.', commentEditRequired: '수정할 댓글 내용을 입력해 주세요.', commentEditPassword: '댓글 작성 시 사용한 비밀번호를 입력해 주세요.', commentEdit: '댓글 수정에 실패했습니다.', commentDelete: '댓글 삭제에 실패했습니다.',
      regionRequired: '지역과 세부 지역을 선택해 주세요.', titleRequired: '제목을 입력해 주세요.', contentRequired: '내용을 입력해 주세요.', passwordMin: '수정용 비밀번호는 4자 이상 입력해 주세요.', savePost: '게시글 저장에 실패했습니다.',
    },
  },
  en: {
    common: {
      home: 'Home', board: 'Community', locations: 'Places', dashboard: 'Dashboard', write: 'Write', newPost: 'New post',
      all: 'All', seoul: 'Seoul', gyeonggi: 'Gyeonggi', seoulGyeonggi: 'Seoul & Gyeonggi', search: 'Search', category: 'Category',
      sort: 'Sort', latest: 'Latest', viewsSort: 'Most viewed', likesSort: 'Most liked', bookmark: 'Bookmark', bookmarks: 'Bookmarks',
      comments: 'Comments', likes: 'Likes', views: 'Views', edit: 'Edit', delete: 'Delete', cancel: 'Cancel', confirm: 'Confirm', save: 'Save',
      loading: 'Loading...', processing: 'Processing...', reset: 'Reset', anonymous: 'Anonymous', noAddress: 'Address unavailable',
      source: 'Source: Korea Tourism Organization · KOGL Type 3', postsUnit: 'posts', locationsUnit: 'places', count: '{count}', score: '{score} pts',
      commentsCount: '{count} comments', addBookmark: 'Add bookmark', removeBookmark: 'Remove bookmark', originalKorean: 'Original Korean data',
    },
    header: {
      region: 'Seoul · Gyeonggi', notifications: 'New post alerts', connected: 'Live', reconnecting: 'Reconnecting',
      emptyNotifications: 'No new posts yet.', deleteNotification: 'Delete alert', online: '{count} online', presence: '{count} users online',
      mainMenu: 'Main navigation', openMenu: 'Open menu', justNow: 'Just now', language: 'Language', korean: '한국어', english: 'English',
    },
    footer: { description: 'Seoul and Gyeonggi local information community', license: 'Korea Tourism Organization TourAPI 4.0 · KOGL Type 3' },
    hero: {
      eyebrow: 'Seoul and Gyeonggi in one place', line1: 'Discover your neighborhood', line2: 'and share it on',
      description: 'Explore public tourism data for Seoul and Gyeonggi, then share local experiences anonymously without signing up.',
      dataButton: 'Explore public data', communityButton: 'Join the community', linked: 'Live data connected', count: '12,512 TourAPI records',
    },
    home: {
      publicDataTitle: 'Real public data', publicDataDesc: '12,512 original TourAPI records', communityTitle: 'Anonymous community',
      communityDesc: 'Password-based posts and comments', chatbotTitle: 'Data chatbot', chatbotDesc: 'Search places and community posts together',
      recommend: 'Recommended places in {region}', viewAll: 'View all', recentPosts: 'Recent local stories', goBoard: 'Open community', selectRegion: 'Select region',
    },
    categories: {
      c12: 'Attractions', c14: 'Cultural facilities', c15: 'Festivals & events', c25: 'Travel courses', c28: 'Leisure sports', c32: 'Accommodation', c38: 'Shopping', c39: 'Restaurants', free: 'General',
    },
    board: {
      title: 'Seoul & Gyeonggi community', description: 'Share local discoveries and experiences anonymously without creating an account.',
      searchPlaceholder: 'Search titles or content', popularTags: 'Popular tags', bookmarksOnly: 'Bookmarks', summary: '{count} posts',
      noResults: 'No results found', noResultsDesc: 'Try another search or filter, or write the first post.', resetFilters: 'Reset filters',
    },
    locations: {
      title: 'Public places in {region}', description: 'Find attractions, cultural facilities, festivals, accommodation, shopping and restaurants in one place.',
      cache: 'Seoul & Gyeonggi SQLite cache', searchPlaceholder: 'Search {region} place names or addresses', showAll: 'Show all', bookmarksOnly: 'Bookmarks only',
      regionSelect: 'Region', contentType: 'Content type', summary: '{count} {label} places', bookmarkLabel: '{region} bookmarks', totalLabel: 'All Seoul & Gyeonggi',
      noBookmarks: 'No bookmarked places', noBookmarksDesc: 'Use the bookmark button on a place card to save it.', notFound: 'No places found',
      notFoundDesc: 'Try changing the region, keyword or content type.', list: 'Back to places', rating: '{count} ratings', map: 'Map', mapUnavailable: 'Map coordinates are unavailable for this place.',
      mapAttribution: 'Map data © OpenStreetMap contributors', nearby: 'Nearby places', nearbyDesc: 'Five places closest to the current location', reactionLabel: 'Place reactions',
      reviewTitle: 'Ratings and comments', reviewSummary: 'Average {rating} · {count} ratings', nickname: 'Nickname', nicknamePlaceholder: 'Anonymous if left blank', password: 'Edit/delete password',
      passwordPlaceholder: 'At least 4 characters', ratingLabel: 'Rating', zeroPoint: '0 stars', comment: 'Comment', commentPlaceholder: 'Share your experience or useful information about this place.',
      submitReview: 'Post comment', submitting: 'Posting...', loadingComments: 'Loading comments...', firstReview: 'Be the first to leave a rating and comment.', edited: 'Edited',
      editPassword: 'Comment password', saving: 'Saving...', deleteCommentTitle: 'Delete place comment', deleteCommentDesc: 'Enter the password used when writing this comment.',
      originalNotice: 'TourAPI place names and addresses remain in their original Korean under the no-derivatives license.',
    },
    post: {
      backBoard: 'Back to community', reactionLabel: 'Post reactions', attachedImage: 'Post attachment', ownerEdit: 'Edit', ownerDelete: 'Delete', commentsTitle: 'Comments',
      writeComment: 'Write a comment', commentPlaceholder: 'Share an opinion or additional information about this post.', commentPassword: 'Comment password',
      commentPasswordPlaceholder: 'Password for edit/delete (4+ characters)', submitComment: 'Post comment', submitting: 'Posting...', loadingComments: 'Loading comments...', firstComment: 'Be the first to comment.',
      edited: 'Edited', editPasswordPlaceholder: 'Original comment password', deletePostTitle: 'Delete post', editPostTitle: 'Edit post', deletePostDesc: 'Enter the original password to delete this post.',
      editPostDesc: 'Enter the original password to open the edit page.', deleteCommentTitle: 'Delete comment', deleteCommentDesc: 'Enter the password used when writing this comment.',
    },
    form: {
      backPost: 'Back to post', backBoard: 'Back to community', editTitle: 'Edit post', newTitle: 'Create a post', description: 'Posts are anonymous. The password is used only for editing and deletion.',
      category: 'Category', postRegion: 'Post region', metroRegion: 'Province / city', districtSeoul: 'District', districtGyeonggi: 'City / county', regionHelp: 'Used for the popular-region ranking on the dashboard.',
      title: 'Title', titlePlaceholder: 'Enter local information or your experience', content: 'Content', contentPlaceholder: 'Share a specific place and experience.', images: 'Images',
      chooseImages: 'Choose or add images', imageHelp: 'JPG, PNG or GIF · up to 5 MB each · maximum {count} including existing images', existingImage: 'Existing attachment',
      deleteImage: 'Delete existing attachment', deleting: 'Deleting...', existingDeleteHint: 'Existing image · use X to delete', removeImage: 'Remove attachment', tags: 'Tags', tagPlaceholder: 'Enter a tag',
      add: 'Add', password: 'Edit/delete password', passwordPlaceholder: 'At least 4 characters', saveLoading: 'Saving...', editComplete: 'Save changes', register: 'Publish post',
      confirmImageDelete: 'Remove this image from the post? This cannot be undone.',
    },
    dashboard: {
      title: 'Seoul & Gyeonggi community dashboard', description: 'Live aggregates of posts, comments, likes and views.', refresh: 'Refresh', monthly: 'Monthly posts by category',
      recentMonths: 'Last 7 months · stacked bars', distribution: 'Category distribution', comparison: 'All · Seoul · Gyeonggi', posts: 'Posts', noPosts: 'No posts to summarize.',
      popularRegions: 'Popular regions', postCount: '{count} posts', commentCount: '{count} comments', likeCount: '{count} likes', viewCount: '{count} views',
      noRegions: 'Select a region when writing posts to populate this ranking.', popularLocations: 'Popular places', reactionBased: 'Based on user engagement',
      noPopularLocations: 'The ranking will appear when places receive comments, likes and views.', topRated: 'Top-rated places', ratingAverage: 'By average comment rating',
      noRatings: 'The ranking will appear after rated comments are added.', weeklyTrend: 'Weekly views and likes', thisWeek: 'Monday through Sunday this week',
      viewsDataset: 'Views', likesDataset: 'Likes', unitItems: '', unitTimes: '',
    },
    chat: {
      source: 'Source: Korea Tourism Organization TourAPI 4.0 · KOGL Type 3', greeting: 'Hello! I’m the LocalHub assistant 😊\nI can search Seoul and Gyeonggi public data and community posts.',
      quick1: 'Recommend Seoul attractions', quick2: 'Cultural facilities in Jongno', quick3: 'Festivals in Seoul', quick4: 'Community posts about the Han River', assistant: 'AI local guide', title: 'LocalHub assistant',
      basedOnData: 'Based on real Seoul & Gyeonggi data', clear: 'Clear chat', references: 'References', placeholder: 'Ask about places in Seoul or Gyeonggi', open: 'Open LocalHub assistant',
    },
    share: {
      kakao: 'Share on KakaoTalk', connecting: 'Connecting', copy: 'Copy link', copied: 'Share link copied.', copyFailed: 'Could not copy the link.', keyMissing: 'Set VITE_KAKAO_JAVASCRIPT_KEY in frontend/.env.',
      kakaoFailed: 'KakaoTalk sharing failed.', viewAtLocalHub: 'View on LocalHub', defaultDescription: 'Explore this place on LocalHub.', label: 'Social sharing',
    },
    pagination: { label: 'Pagination', previous: 'Previous {count} pages', previousTitle: 'Previous page group', next: 'Next {count} pages', nextTitle: 'Next page group' },
    passwordModal: { close: 'Close', label: 'Edit/delete password', placeholder: 'Enter password' },
    notFound: { title: 'Page not found', description: 'Check the URL or return to the LocalHub home page.', home: 'Go home' },
    errors: {
      postsLoad: 'Could not load posts.', postLoad: 'Could not load the post.', locationsLoad: 'Could not load places.', dashboardLoad: 'Could not load dashboard data.',
      commentsLoad: 'Could not load comments.', like: 'Could not update the like.', bookmark: 'Could not update the bookmark.', chat: 'Could not get a chatbot response.',
      commentRequired: 'Enter a comment.', commentPassword: 'The comment password must be at least 4 characters.', locationCommentPassword: 'The edit/delete password must be at least 4 characters.',
      commentCreate: 'Could not post the comment.', commentEditRequired: 'Enter the updated comment.', commentEditPassword: 'Enter the password used for this comment.', commentEdit: 'Could not update the comment.', commentDelete: 'Could not delete the comment.',
      regionRequired: 'Select a region and district.', titleRequired: 'Enter a title.', contentRequired: 'Enter content.', passwordMin: 'The edit/delete password must be at least 4 characters.', savePost: 'Could not save the post.',
    },
  },
} as const

function resolveInitialLocale(): AppLocale {
  const stored = localStorage.getItem('localhub-locale')
  if (stored === 'ko' || stored === 'en') return stored
  return navigator.language.toLowerCase().startsWith('en') ? 'en' : 'ko'
}

export const i18n = createI18n({
  legacy: false,
  locale: resolveInitialLocale(),
  fallbackLocale: 'ko',
  messages,
})

export function setAppLocale(locale: AppLocale): void {
  i18n.global.locale.value = locale
  localStorage.setItem('localhub-locale', locale)
  document.documentElement.lang = locale === 'ko' ? 'ko' : 'en'
}

setAppLocale(i18n.global.locale.value as AppLocale)
