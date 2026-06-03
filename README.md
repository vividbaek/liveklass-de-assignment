# Liveklass Event Pipeline

온라인 강의 서비스에서 발생할 수 있는 가상 이벤트를 생성하고, PostgreSQL에 필드별로 저장한 뒤 SQL 집계 결과를 PNG 차트로 시각화하는 데이터 파이프라인 과제입니다.

전체 흐름은 다음과 같습니다.

```text
이벤트 생성기 -> PostgreSQL -> SQL 집계 -> PNG 차트
```

## 실행 방법

필요한 도구:

- Docker
- Docker Compose

전체 파이프라인은 아래 명령 한 번으로 실행됩니다.

```bash
docker compose up
```

실행하면 PostgreSQL과 Python 앱 컨테이너가 함께 시작됩니다. 앱은 DB가 준비될 때까지 기다린 뒤 스키마를 초기화하고, 가상 이벤트를 생성해 `events` 테이블에 적재합니다. 적재가 끝나면 SQL 집계 결과를 바탕으로 PNG 차트를 생성합니다.

`docker-compose.yml`에 앱 빌드 설정이 포함되어 있어, 로컬에 이미지가 없으면 Compose가 자동으로 앱 이미지를 빌드합니다. 코드를 수정한 뒤 이미지를 강제로 다시 만들고 싶을 때만 `docker compose up --build`를 사용하면 됩니다.

실행 흐름:

```text
PostgreSQL 준비 상태 확인
-> sql/init.sql 실행
-> events 테이블 초기화
-> 가상 이벤트 생성
-> 배치 적재
-> 적재 건수 검증
-> SQL 집계 기반 PNG 차트 생성
```

결과 파일은 `charts/` 디렉터리에 생성됩니다.

- `charts/session_funnel.png`
- `charts/preview_watch_conversion.png`
- `charts/course_revenue.png`
- `charts/error_area_counts.png`

컨테이너 정리가 필요하면 아래 명령을 실행합니다.

```bash
docker compose down
```

## 프로젝트 구조

```text
.
├── docker-compose.yml
├── Dockerfile
├── src/
│   ├── main.py              # 전체 파이프라인 실행
│   ├── event_generator.py   # 가상 이벤트 생성
│   ├── db.py                # DB 연결, 스키마 초기화, 적재
│   ├── analysis.py          # SQL 쿼리 실행
│   └── visualize.py         # PNG 차트 생성
├── sql/
│   ├── init.sql             # events 테이블 스키마
│   └── queries/             # 분석 쿼리
├── charts/                  # 시각화 결과
├── k8s/                     # Kubernetes 선택 과제 매니페스트
└── docs/                    # AWS/Kubernetes 설계 문서
```

## 이벤트 설계

이벤트는 온라인 강의 서비스의 방문, 학습, 결제, 오류 흐름을 표현하도록 설계했습니다.

| 이벤트 타입 | 의미 |
|---|---|
| `page_view` | 메인, 강의 목록, 커뮤니티 등 일반 페이지 조회 |
| `course_view` | 특정 강의 상세 페이지 조회 |
| `lesson_started` | 무료 체험 또는 유료 강의 시청 시작 |
| `lesson_completed` | 강의 콘텐츠 시청 완료 |
| `checkout_started` | 결제 페이지 진입 |
| `purchase_completed` | 결제 완료 |
| `error_occurred` | 결제, 영상, 라이브 수업, 강의 로딩 오류 |

단순히 이벤트 타입별 발생 수만 보기보다 실제 서비스 의사결정에 가까운 분석이 가능하도록 `session_id`, `course_id`, `lesson_id`, `duration_seconds`, `amount`, `error_area`를 함께 생성했습니다. 특히 `course_view -> lesson_started -> checkout_started -> purchase_completed` 흐름을 세션 기준 퍼널로 볼 수 있게 구성했습니다.

기본 실행에서는 2,500개 세션에서 약 10,000건의 이벤트를 생성합니다. 이벤트 생성기는 고정 seed를 사용하므로 같은 코드와 설정에서는 같은 데이터를 재현할 수 있습니다.

## 저장소 선택 이유

저장소는 PostgreSQL을 선택했습니다.

- JSON 문자열을 통째로 저장하지 않고 각 필드를 컬럼으로 분리하기 좋습니다.
- 이벤트 타입, 세션, 강의, 시간 기준 SQL 집계가 쉽습니다.
- Docker Compose로 앱과 DB를 함께 띄우기 쉬워 과제 재현성이 좋습니다.

이번 과제는 작은 배치 파이프라인이므로 PostgreSQL 단일 테이블로 충분하다고 판단했습니다. 실제 운영 환경이라면 이벤트 수집 API와 DB 사이에 Kinesis, Kafka, SQS 같은 큐 또는 스트리밍 계층을 두고, 원본 이벤트는 S3 같은 객체 스토리지에 함께 보관하는 구조를 고려할 수 있습니다.

이벤트 로그는 시간이 지나며 필드가 늘어날 수 있습니다. 다만 이번 과제에서는 SQL 집계와 결제/전환 분석을 직접 보여주는 것이 더 중요하다고 봤습니다. 운영에서 스키마 변화가 잦아진다면 `schema_version` 컬럼이나 선택적 `metadata JSONB` 컬럼을 추가해 유연성을 보완할 수 있습니다.

## 스키마 설명

이벤트는 `events` 테이블에 저장합니다. 자세한 DDL은 `sql/init.sql`에 있습니다.

| 컬럼 | 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `event_id` | UUID | No | 이벤트 고유 ID, primary key |
| `event_type` | VARCHAR(50) | No | 이벤트 종류 |
| `event_time` | TIMESTAMP | No | 이벤트 발생 시각 |
| `session_id` | VARCHAR(50) | No | 방문 흐름을 묶기 위한 세션 ID |
| `user_type` | VARCHAR(20) | No | `guest` 또는 `member` |
| `user_id` | VARCHAR(50) | Yes | 로그인 사용자 ID, 비회원은 NULL |
| `course_id` | VARCHAR(50) | Yes | 강의 식별자 |
| `lesson_id` | VARCHAR(50) | Yes | 강의 내 콘텐츠 식별자 |
| `lesson_access_type` | VARCHAR(30) | Yes | `free_preview`, `paid_enrolled` 등 |
| `page_url` | TEXT | Yes | 이벤트 발생 페이지 경로 |
| `device_type` | VARCHAR(20) | Yes | `desktop`, `mobile`, `tablet` |
| `duration_seconds` | INTEGER | Yes | 페이지 체류 또는 강의 시청 시간 |
| `amount` | INTEGER | Yes | 결제 금액 |
| `payment_method` | VARCHAR(30) | Yes | 결제 수단 |
| `error_area` | VARCHAR(30) | Yes | 오류 발생 영역 |
| `error_code` | VARCHAR(50) | Yes | 오류 상세 코드 |

테이블은 이벤트 한 건을 한 행으로 저장하는 로그 테이블로 설계했습니다. 모든 이벤트에 공통으로 필요한 `event_id`, `event_type`, `event_time`, `session_id`, `user_type`은 필수 컬럼으로 두고, 결제/강의/오류처럼 특정 이벤트에서만 필요한 값은 NULL을 허용했습니다.

`event_type`, `user_type`, `duration_seconds`, `amount`에는 기본 CHECK 제약을 두어 잘못된 값이 적재되지 않도록 했습니다. 분석 쿼리에서 자주 사용하는 `event_type`, `event_time`, `session_id`, `course_id`, `user_id`에는 인덱스를 추가했습니다.

## 분석 쿼리

분석 쿼리는 `sql/queries/`에 분리했습니다.

| 파일 | 분석 내용 |
|---|---|
| `session_funnel.sql` | `course_view -> lesson_started -> checkout_started -> purchase_completed` 세션 퍼널 |
| `preview_watch_conversion.sql` | 무료 체험 시청 시간 구간별 구매 전환율 |
| `course_revenue.sql` | 강의별 구매 수와 매출 |
| `error_area_counts.sql` | 오류 영역별 발생 수 |

과제 요구사항은 최소 2개 이상의 집계 분석이지만, 서비스 관점에서 전환, 매출, 오류를 함께 볼 수 있도록 4개 쿼리를 작성했습니다.

## 테스트

이벤트 생성기와 검증 로직의 기본 동작은 `pytest`로 확인할 수 있습니다.

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest tests -q
```

## 시각화 결과

SQL 집계 결과는 `src/visualize.py`에서 `matplotlib` 기반 PNG로 생성합니다. Docker 환경에서도 한글이 깨지지 않도록 `assets/fonts/`에 포함된 Pretendard 폰트를 사용합니다.

### 세션 퍼널 전환율

![Session funnel](charts/session_funnel.png)

강의 상세 조회 이후 무료 체험 시청, 결제 시작, 결제 완료로 이어지는 세션 수와 전환율을 보여줍니다.

### 무료 체험 시청 시간별 전환율

![Preview watch conversion](charts/preview_watch_conversion.png)

무료 체험 콘텐츠 시청 시간을 구간으로 나누고, 각 구간에서 구매 완료로 이어진 세션 비율을 계산했습니다.

### 강의별 매출

![Course revenue](charts/course_revenue.png)

강의별 구매 수와 매출을 함께 비교합니다. 가격 차이가 있으므로 구매 수만 보지 않고 매출 기준도 함께 확인하도록 구성했습니다.

### 오류 영역별 발생 수

![Error area counts](charts/error_area_counts.png)

오류가 어느 영역에서 많이 발생했는지 보여줍니다. 결제 오류는 구매 전환에 직접 영향을 줄 수 있어 퍼널 분석과 함께 확인할 운영 지표로 사용했습니다.

현재 데이터는 실제 사용자 데이터가 아니라 과제 검증을 위한 가상 이벤트입니다. 따라서 차트의 수치는 실제 비즈니스 결론이 아니라, 이벤트 로그로 어떤 분석이 가능한지 보여주는 예시입니다.

## 구현하면서 고민한 점

첫째, 이벤트를 JSON 하나로 저장하지 않고 분석에 필요한 필드를 컬럼으로 분리했습니다. 과제 요구사항을 만족하는 동시에 SQL 집계가 자연스럽게 동작하도록 하기 위해서입니다.

둘째, 단순 이벤트 수보다 세션 기준 분석을 우선했습니다. 같은 사용자가 여러 이벤트를 남길 수 있기 때문에 구매 전환이나 이탈을 볼 때는 이벤트 행 수보다 `session_id` 기준 집계가 더 해석하기 쉽다고 판단했습니다.

셋째, 시각화까지 `docker compose up` 한 번으로 끝나도록 구성했습니다. 평가자가 별도 명령을 기억하지 않아도 이벤트 생성, 저장, 집계, 차트 생성을 한 번에 재현할 수 있게 하는 것이 중요하다고 봤습니다.

넷째, 현재 구현은 배치 방식입니다. 운영 환경이라면 누적 적재, 파티셔닝, 보관 정책, 원본 이벤트 보관, DLQ 등을 추가해 장애 대응과 장기 보관을 분리하는 방향으로 확장할 수 있습니다.

## 선택 과제

### AWS 아키텍처

AWS에서 운영한다면 Kinesis, Firehose, S3, RDS PostgreSQL, Glue, Athena, QuickSight, CloudWatch, SQS DLQ를 조합하는 구조를 고려했습니다.

- 문서: [docs/aws-architecture.md](docs/aws-architecture.md)
- 구성도: [docs/aws-architecture.png](docs/aws-architecture.png)

![AWS architecture](docs/aws-architecture.png)

### Kubernetes 매니페스트

이벤트 생성기 앱을 Kubernetes에서 실행한다고 가정하고 `ConfigMap`과 `Job` 매니페스트를 작성했습니다.

Kubernetes는 아직 실무 경험이 많지 않아, 이번 과제에서는 기본 리소스의 역할을 먼저 정리한 뒤 현재 앱에 직접 대응되는 구성을 중심으로 작성했습니다. 이벤트 생성기는 계속 떠 있는 서버가 아니라 실행 후 종료되는 작업이므로, `Deployment`보다 `Job`이 더 적절하다고 판단했습니다.

- [k8s/event-generator-configmap.yaml](k8s/event-generator-configmap.yaml)
- [k8s/event-generator-job.yaml](k8s/event-generator-job.yaml)

`ConfigMap`은 민감하지 않은 DB 연결 설정을 분리하기 위해 사용했습니다. DB password는 실제 운영에서 `Secret`으로 관리해야 하므로 매니페스트에서는 `liveklass-db-secret`을 참조하도록 작성했습니다.
