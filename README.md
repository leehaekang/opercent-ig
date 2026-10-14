# opercent-ig

오퍼센트 인스타그램 카드뉴스 발행 파이프라인.

## 구조

- `images/<날짜>/1.jpg …` — 카드 이미지. raw.githubusercontent.com URL로 인스타그램에 전달됩니다.
- `queue/<날짜>.json` — 그날 게시물 정의.
- `.github/workflows/publish.yml` — 수동 실행(workflow_dispatch) 워크플로.
- `scripts/publish.py` — Instagram Graph API 호출.

## 큐 파일 형식

```json
{
  "status": "approved",
  "caption": "본문...",
  "first_comment": "첫 댓글...",
  "images": ["images/2026-10-14/1.jpg", "images/2026-10-14/2.jpg"]
}
```

`status`가 `approved`일 때만 발행됩니다. 발행에 성공하면 `published`로 바뀌고 `media_id`가 기록됩니다.

## 필요한 Secrets

Settings → Secrets and variables → Actions

- `IG_USER_ID` — 인스타그램 비즈니스 계정 ID
- `IG_ACCESS_TOKEN` — 장기 액세스 토큰 (instagram_business_content_publish 권한)

## 발행

Actions → Publish to Instagram → Run workflow → 날짜 입력
