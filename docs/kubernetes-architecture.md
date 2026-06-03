# Kubernetes 배포 검토

이 문서는 Step 1에서 만든 이벤트 생성기 앱을 Kubernetes에 배포한다고 가정했을 때의 구성 검토입니다.
실제 클러스터에 배포하지는 않지만, 이벤트 생성기 앱을 Kubernetes에서 실행한다면 어떤 리소스가 적절한지 정리했습니다.

## 적용 범위

현재 프로젝트는 Docker Compose에서 Python 앱을 실행해 가상 이벤트를 만들고 PostgreSQL에 적재하는 방식입니다.
이 작업은 계속 떠 있는 웹 서버가 아니라 한 번 실행하고 종료되는 배치 작업에 가깝습니다.

그래서 Kubernetes 매니페스트는 전체 운영 시스템을 옮기는 방식이 아니라, 이벤트 생성기 앱 실행에 필요한 최소 구성으로 작성했습니다.

```text
ConfigMap
→ DB 연결 설정 제공

Job
→ python -m src.main 실행
→ 가상 이벤트 생성
→ PostgreSQL 적재
```

## 작성한 매니페스트

이번 과제에서는 다음 두 파일을 작성했습니다.

- `k8s/event-generator-configmap.yaml`
- `k8s/event-generator-job.yaml`

### ConfigMap

`ConfigMap`은 컨테이너에 주입할 일반 설정값을 관리합니다.
이번 프로젝트에서는 DB 연결에 필요한 값 중 민감하지 않은 항목만 분리했습니다.

```yaml
POSTGRES_DB: liveklass
POSTGRES_USER: liveklass
POSTGRES_HOST: liveklass-postgres
POSTGRES_PORT: "5432"
```

이 값을 매니페스트에 분리해두면 이미지나 Python 코드를 수정하지 않고도 환경별 DB host, database name, port를 바꿀 수 있습니다.

DB password는 `ConfigMap`에 넣지 않았습니다.
실제 운영 환경에서는 password, token, API key 같은 민감 정보는 `Secret`으로 관리해야 하므로,
`Job` 매니페스트에서는 `liveklass-db-secret`을 참조하도록만 작성했습니다.

### Job

`Job`은 한 번 실행하고 종료되는 작업에 적합한 리소스입니다.
Step 1의 이벤트 생성기 앱은 API 서버처럼 계속 요청을 기다리는 서비스가 아니라,
`python -m src.main`을 실행해 이벤트를 생성하고 PostgreSQL에 적재한 뒤 종료됩니다.

그래서 `Deployment`보다 `Job`이 더 적합하다고 판단했습니다.

```text
Job
→ event-generator 컨테이너 실행
→ python -m src.main
→ PostgreSQL 적재 완료 후 종료
```

`backoffLimit: 2`를 둔 이유는 일시적인 DB 연결 실패 같은 문제가 있을 때 제한적으로 재시도하기 위해서입니다.
`ttlSecondsAfterFinished: 3600`은 완료된 Job 리소스를 일정 시간 뒤 정리하기 위한 설정입니다.

## 왜 Deployment가 아닌 Job인가

`Deployment`는 API 서버나 처리기처럼 계속 실행되어야 하는 작업에 적합합니다.
예를 들어 실제 운영 환경에서 클라이언트 이벤트를 받는 ingestion API가 있다면 다음처럼 Deployment로 운영할 수 있습니다.

```text
API Gateway
→ Ingress
→ Service
→ Ingestion API Pods
→ Kinesis Data Streams
```

하지만 현재 Step 1 앱은 실시간 요청을 받는 ingestion API가 아니라 가상 이벤트 생성기입니다.
따라서 Pod를 계속 유지하는 Deployment보다, 실행 후 종료되는 Job이 과제 목적에 더 잘 맞습니다.

## 향후 확장한다면

서비스가 커져 실제 이벤트 수집 API와 처리기가 분리되면 Kubernetes 리소스도 다음처럼 확장할 수 있습니다.

| 대상 | 적합한 리소스 | 이유 |
| --- | --- | --- |
| Ingestion API | `Deployment`, `Service`, `Ingress` | 외부 요청을 계속 받아야 하고 여러 Pod로 scale-out할 수 있습니다. |
| Kinesis Consumer | `Deployment` | Kinesis에서 지속적으로 이벤트를 읽어 PostgreSQL에 적재합니다. |
| Event Generator | `Job` | 한 번 실행하고 종료되는 배치 작업입니다. |
| Chart/Report 생성 | `CronJob` | 정해진 시간마다 분석 결과나 리포트를 갱신할 수 있습니다. |
| 일반 설정 | `ConfigMap` | 환경별 설정값을 코드와 분리할 수 있습니다. |
| 민감 정보 | `Secret` | DB password, API key 같은 값을 별도로 관리합니다. |

이 과제에서는 실제 ingestion API와 처리기를 구현하지 않았기 때문에,
해당 Deployment 매니페스트까지 작성하면 오히려 현재 코드와 맞지 않는 예시가 될 수 있습니다.
그래서 Step 1 이벤트 생성기 앱에 직접 대응되는 `ConfigMap`과 `Job`만 작성했습니다.

## ECS Fargate와의 관계

AWS 운영 아키텍처에서는 ECS Fargate를 기본 컨테이너 실행 방식으로 제안했습니다.
현재 규모에서는 ECS Fargate가 더 단순하고 운영 부담도 낮습니다.

Kubernetes/EKS는 여러 작업을 독립적으로 배포하고 확장해야 할 때 더 의미가 있습니다.
따라서 이번 과제에서는 Kubernetes를 메인 운영안으로 바꾸기보다,
이벤트 생성기 앱을 Kubernetes에서 실행한다면 어떤 리소스를 선택할지 보여주는 선택 과제로 정리했습니다.
