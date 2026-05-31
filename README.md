# Liveklass Event Pipeline Assignment

Liveklass와 같은 온라인 강의 플랫폼에서 발생할 수 있는 synthetic event를 생성하고,
PostgreSQL에 저장한 뒤 SQL 집계와 시각화를 통해 학습/결제 전환 인사이트를 확인하는 과제입니다.

## 현재 구현 단계

1. 프로젝트 기본 구조 생성 완료
2. 이벤트 로그 저장을 위한 `events` 테이블 스키마 작성 완료
3. 학습/결제 전환 분석을 위한 `duration_seconds` 필드 추가
4. session 기반 synthetic event generator 구현 완료
5. PostgreSQL batch insert 로직 구현 완료
6. 다음 단계: SQL 집계 쿼리 작성

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

`events` 테이블은 분석을 위한 raw event log 저장소입니다.
현업에서도 원본 이벤트는 단일 `events` 테이블 또는 날짜별 event table에 append하고,
이후 분석 목적에 따라 funnel, revenue, retention mart 테이블로 가공하는 방식이 일반적입니다.

`events` 테이블은 서비스 운영 DB가 아니라 이벤트 로그 분석용 저장소입니다.
따라서 `users`, `courses`, `lessons`를 별도 테이블로 정규화하지 않고,
분석에 필요한 식별자인 `user_id`, `session_id`, `course_id`, `lesson_id`를 이벤트 row에 함께 저장했습니다.

`event_type`이 각 row의 의미를 결정하며, 이벤트별로 필요하지 않은 필드는 `NULL`을 허용합니다.
예를 들어 `purchase_completed`는 `amount`와 `payment_method`를 사용하고,
`error_occurred`는 `error_area`와 `error_code`를 사용합니다.

`amount`는 원화 기준 결제 금액이므로 소수점 없이 정수로 저장합니다.
강의명과 lesson명은 이벤트 row에 직접 저장하지 않고, generator 설정값의 mapping을 통해 차트나 README 표시 단계에서 한국어 이름으로 변환할 수 있도록 했습니다.

`duration_seconds`는 페이지 체류 시간 또는 강의 콘텐츠 시청 시간을 초 단위로 저장합니다.
이를 통해 무료 체험 콘텐츠를 오래 시청한 session이 결제까지 이어지는지,
강의 상세 페이지 체류 시간이 `checkout_started` 또는 `purchase_completed`와 어떤 관계가 있는지 분석할 수 있도록 설계했습니다.

## 이벤트 생성 방식

이벤트는 완전 무작위가 아니라 온라인 강의 플랫폼에서 발생할 수 있는 대표 session scenario를 기반으로 생성합니다.
각 session은 하나의 `session_id`를 공유하며, 내부 이벤트 시간은 사용자의 행동 흐름에 맞춰 순차적으로 증가합니다.

현재 generator가 사용하는 대표 scenario는 다음과 같습니다.

- `browse_only`: 강의 탐색 후 이탈
- `preview_dropoff`: 무료 체험 콘텐츠 시청 중 이탈
- `preview_completed_no_purchase`: 무료 체험 콘텐츠 완료 후 미구매
- `checkout_abandoned`: 결제 시작 후 이탈
- `preview_to_purchase`: 무료 체험 콘텐츠 시청 후 결제 완료
- `payment_error`: 결제 중 오류 발생
- `paid_learning`: 결제 후 유료 콘텐츠 수강

이 구조를 통해 `session_id` 기준으로 무료 체험 시청 시간, 결제 시작, 결제 완료, 오류 발생 흐름을 함께 분석할 수 있습니다.

## 다음 구현 순서

1. SQL 집계 쿼리 작성
2. matplotlib 기반 PNG 시각화 생성
3. AWS 아키텍처 문서 작성

## 실행 예시

Docker Compose로 PostgreSQL과 Python app을 함께 실행합니다.

```bash
docker compose up --build
```

기본 실행에서는 2,500개 session에서 약 10,000건의 synthetic event를 생성하고,
1,000건 단위 batch로 PostgreSQL에 적재합니다.

실행 흐름은 다음과 같습니다.

```text
PostgreSQL readiness 확인
→ sql/init.sql 실행
→ events table TRUNCATE
→ synthetic events 생성
→ 1,000건 단위 batch insert
→ SELECT COUNT(*) FROM events
```

과제 재현성을 위해 실행 시 `events` 테이블을 초기화한 뒤 synthetic event를 적재합니다.
실제 운영 환경에서는 append-only 방식으로 이벤트를 누적하고, partitioning 또는 retention policy를 적용하는 것이 일반적입니다.

DB에 직접 접속해서 확인하려면 다음 명령어를 사용할 수 있습니다.

```bash
docker exec -it liveklass-postgres psql -U liveklass -d liveklass
```

```sql
SELECT COUNT(*) FROM events;

SELECT event_type, COUNT(*)
FROM events
GROUP BY event_type
ORDER BY COUNT(*) DESC;
```

## Queue / Streaming 확장 방향

이번 구현은 과제 범위를 고려해 Python generator가 batch-style로 이벤트를 생성하는 방식입니다.
실제 운영 환경에서는 이벤트 생성 API와 DB 사이에 Amazon Kinesis, SQS, Kafka 같은 queue/streaming layer를 둘 수 있습니다.
이를 통해 트래픽 급증 시 DB 부하를 완화하고, consumer retry 및 dead letter queue로 적재 안정성을 높일 수 있습니다.

> 현재 데이터는 실제 사용자 데이터가 아니라 과제 검증을 위한 synthetic event입니다.
> 따라서 분석 결과는 실제 비즈니스 결론이 아니라, 이벤트 로그를 통해 어떤 분석이 가능한지 보여주는 예시입니다.
