# Liveklass Event Pipeline Assignment

Liveklass와 같은 온라인 강의 플랫폼에서 발생할 수 있는 synthetic event를 생성하고,
PostgreSQL에 저장한 뒤 SQL 집계와 시각화를 통해 학습/결제 전환 인사이트를 확인하는 과제입니다.

## 현재 구현 단계

1. 프로젝트 기본 구조 생성 완료
2. 이벤트 로그 저장을 위한 `events` 테이블 스키마 작성 완료
3. 학습/결제 전환 분석을 위한 `duration_seconds` 필드 추가
4. session 기반 synthetic event generator 구현 완료
5. 다음 단계: PostgreSQL insert 로직 구현

## 이벤트 설계

현재 설계한 이벤트 타입은 다음과 같습니다.

- `page_view`: 랜딩, 강의 목록, 결제 페이지 등 일반 페이지 방문
- `course_view`: 특정 강의 상세 페이지 조회
- `lesson_started`: 무료 체험 콘텐츠 또는 유료 수강 콘텐츠 시청 시작
- `lesson_completed`: 무료 체험 콘텐츠 또는 유료 수강 콘텐츠 시청 완료
- `checkout_started`: 결제 시작
- `purchase_completed`: 결제 완료
- `error_occurred`: 결제, 영상, 라이브 수업, 강의 시청 중 오류 발생

## 스키마 설계 이유

`events` 테이블은 서비스 운영 DB가 아니라 이벤트 로그 분석용 저장소입니다.
따라서 `users`, `courses`, `lessons`를 별도 테이블로 정규화하지 않고,
분석에 필요한 식별자인 `user_id`, `session_id`, `course_id`, `lesson_id`를 이벤트 row에 함께 저장했습니다.

`event_type`이 각 row의 의미를 결정하며, 이벤트별로 필요하지 않은 필드는 `NULL`을 허용합니다.
예를 들어 `purchase_completed`는 `amount`와 `payment_method`를 사용하고,
`error_occurred`는 `error_area`와 `error_code`를 사용합니다.

`duration_seconds`는 페이지 체류 시간 또는 강의 콘텐츠 시청 시간을 초 단위로 저장합니다.
이를 통해 무료 체험 콘텐츠를 오래 시청한 session이 결제까지 이어지는지,
강의 상세 페이지 체류 시간이 `checkout_started` 또는 `purchase_completed`와 어떤 관계가 있는지 분석할 수 있도록 설계했습니다.

## 다음 구현 순서

1. PostgreSQL insert 로직 구현
2. SQL 집계 쿼리 작성
3. matplotlib 기반 PNG 시각화 생성
4. Docker Compose로 app + DB 실행 구성

## 실행 예시

현재 단계에서는 DB 저장 전, synthetic event 생성 결과를 console에서 확인할 수 있습니다.

```bash
python3 -m src.main
```

## Queue / Streaming 확장 방향

이번 구현은 과제 범위를 고려해 Python generator가 batch-style로 이벤트를 생성하는 방식입니다.
실제 운영 환경에서는 이벤트 생성 API와 DB 사이에 Amazon Kinesis, SQS, Kafka 같은 queue/streaming layer를 둘 수 있습니다.
이를 통해 트래픽 급증 시 DB 부하를 완화하고, consumer retry 및 dead letter queue로 적재 안정성을 높일 수 있습니다.

> 현재 데이터는 실제 사용자 데이터가 아니라 과제 검증을 위한 synthetic event입니다.
> 따라서 분석 결과는 실제 비즈니스 결론이 아니라, 이벤트 로그를 통해 어떤 분석이 가능한지 보여주는 예시입니다.
