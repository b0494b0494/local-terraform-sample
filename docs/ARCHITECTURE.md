# Architecture and System Diagram

## System Overview

```mermaid
graph TB
    subgraph Local["Local Development"]
        subgraph Docker["Docker Compose"]
            SampleApp["sample-app<br/>:8080"]
            LLMApp["llm-app<br/>:8081"]
        end
    end
    
    subgraph K8s["Kubernetes (Minikube/kind/k3d)"]
        subgraph AppNS["sample-app Namespace"]
            Deployment["Deployment<br/>(2 pods)"]
            Service["Service"]
            ConfigMap["ConfigMap"]
            Secret["Secret"]
        end
        
        subgraph MonitorNS["monitoring Namespace"]
            Prometheus["Prometheus"]
            Grafana["Grafana"]
            Loki["Loki"]
            Promtail["Promtail<br/>(DaemonSet)"]
        end
    end
    
    Docker --> K8s
    Deployment --> Service
    Deployment --> ConfigMap
    Deployment --> Secret
```

## Component Diagram

```mermaid
graph TB
    subgraph AppLayer["Application Layer"]
        SampleApp["sample-app<br/>Flask<br/>/, /health, /ready, /info"]
        LLMApp["llm-app<br/>Flask + Observability<br/>/chat, /metrics, /traces"]
    end
    
    subgraph K8sInfra["Kubernetes Infrastructure"]
        Deployment["Deployment<br/>Replicas, Probes"]
        Service["Service<br/>ClusterIP, LoadBal"]
        HPA["HPA<br/>Auto-scale, CPU based"]
        ConfigMap["ConfigMap<br/>App config"]
        Secret["Secret<br/>API keys"]
        Ingress["Ingress<br/>Routing"]
        PVC["PVC/PV<br/>Storage"]
        SA["ServiceAccount<br/>Identity"]
        RBAC["RBAC<br/>Permissions"]
    end
    
    subgraph Observability["Observability Stack"]
        Prometheus["Prometheus<br/>Metrics, Storage, Scraping"]
        Grafana["Grafana<br/>Dashboards, Queries, Alerts"]
        Loki["Loki<br/>Log store, Index"]
        Promtail["Promtail<br/>Collect, Forward"]
    end
    
    AppLayer --> K8sInfra
    K8sInfra --> Observability
    Prometheus --> Grafana
    Promtail --> Loki
    Loki --> Grafana
```

## Data Flow

### Request Flow

```mermaid
flowchart LR
    User["User/Client"] -->|External access| Ingress["Ingress<br/>(optional)"]
    Ingress -->|Load balancing| Service["Service"]
    Service -->|Routes to| Pods["Pods<br/>sample-app<br/>Application instances"]
```

### Observability Flow

```mermaid
flowchart TB
    subgraph Metrics["Metrics Flow"]
        AppPods1["Application Pods<br/>(exposes /metrics)"]
        Prometheus["Prometheus<br/>Scrapes metrics"]
        Grafana1["Grafana<br/>Visualizes"]
        
        AppPods1 --> Prometheus
        Prometheus --> Grafana1
    end
    
    subgraph Logs["Logs Flow"]
        AppPods2["Application Pods<br/>(logs to stdout)"]
        Promtail["Promtail<br/>Collects logs (DaemonSet)"]
        Loki["Loki<br/>Stores logs"]
        Grafana2["Grafana<br/>Queries logs"]
        
        AppPods2 --> Promtail
        Promtail --> Loki
        Loki --> Grafana2
    end
```

## Terraform Resource Hierarchy

```mermaid
graph TD
    Root["terraform/"] --> Main["main.tf<br/>Core Resources"]
    Main --> NS["Namespace"]
    Main --> CM["ConfigMap"]
    Main --> Dep["Deployment"]
    Main --> Svc["Service"]
    
    Root --> Secrets["secrets.tf<br/>Secret"]
    Root --> Ingress["ingress.tf<br/>(optional)<br/>Ingress"]
    Root --> HPA["hpa.tf<br/>(optional)<br/>HorizontalPodAutoscaler"]
    
    Root --> Storage["storage.tf<br/>(optional)"]
    Storage --> SC["StorageClass"]
    Storage --> PV["PersistentVolume"]
    Storage --> PVC["PersistentVolumeClaim"]
    
    Root --> RBAC["rbac.tf"]
    RBAC --> SA["ServiceAccount"]
    RBAC --> Role["Role"]
    RBAC --> RB["RoleBinding"]
    
    Root --> Monitoring["monitoring.tf<br/>(optional)"]
    Monitoring --> Prom["Prometheus"]
    Monitoring --> Graf["Grafana"]
    Monitoring --> Lok["Loki"]
    Monitoring --> PT["Promtail"]
    
    Root --> Vars["variables.tf<br/>All variables"]
    Root --> Out["outputs.tf<br/>Resource outputs"]
```

## Network Architecture

```mermaid
graph TB
    subgraph Cluster["Kubernetes Cluster"]
        subgraph AppNS["sample-app Namespace"]
            Pod["Pod"]
            Svc["Service"]
            Ing["Ingress"]
            User["User"]
            CM["ConfigMap"]
            Sec["Secret"]
            PVC2["PVC (storage)"]
            
            Pod --> Svc
            Svc --> Ing
            Ing --> User
            Pod -.-> CM
            Pod -.-> Sec
            Pod -.-> PVC2
        end
        
        subgraph MonitorNS["monitoring Namespace"]
            Prom["Prometheus"]
            Graf["Grafana"]
            User2["User"]
            AppMetrics["App Pods<br/>(metrics)"]
            
            Prom --> Graf
            Graf --> User2
            AppMetrics --> Prom
            
            Lok["Loki"]
            Promt["Promtail"]
            AppLogs["App Pods<br/>(logs)"]
            Graf2["Grafana<br/>(log queries)"]
            
            Promt --> Lok
            AppLogs --> Promt
            Lok --> Graf2
        end
    end
```

## Security Layers

```mermaid
graph TB
    subgraph Security["Security Layers"]
        RBAC["1. RBAC<br/>Role-Based Access Control<br/>ServiceAccount ? Role ? Permissions"]
        NetPolicy["2. Network Policies<br/>(optional)<br/>Control pod-to-pod communication"]
        Secrets["3. Secrets Management<br/>Encrypted storage for credentials"]
        Limits["4. Resource Limits<br/>CPU/Memory constraints per pod"]
        NonRoot["5. Non-root containers<br/>Security context in Dockerfile"]
    end
```

## Deployment Flow

```mermaid
flowchart TD
    Dev["Developer"] -->|git push| CI["GitHub Actions<br/>CI<br/>Test & Build"]
    CI -->|if main branch| CD["GitHub Actions<br/>CD<br/>Deploy"]
    CD -->|terraform apply| K8s["Kubernetes<br/>Cluster<br/>Resources created"]
```

## File Structure Overview

```mermaid
graph TD
    Root["project-root/"] --> App["Application"]
    App --> AppPy["app.py<br/>Main Flask app"]
    App --> LLMPy["llm_app.py<br/>LLM app with observability"]
    App --> Req["requirements.txt<br/>Dependencies"]
    
    Root --> IaC["Infrastructure as Code"]
    IaC --> MainTf["main.tf<br/>Core K8s resources"]
    IaC --> VarsTf["variables.tf<br/>Configuration variables"]
    IaC --> SecTf["secrets.tf<br/>Secret management"]
    IaC --> IngTf["ingress.tf<br/>External access"]
    IaC --> HpaTf["hpa.tf<br/>Auto-scaling"]
    IaC --> StorTf["storage.tf<br/>Persistent storage"]
    IaC --> RbacTf["rbac.tf<br/>Security"]
    IaC --> MonTf["monitoring.tf<br/>Observability stack"]
    IaC --> OutTf["outputs.tf<br/>Output values"]
    
    Root --> Config["Configuration"]
    Config --> Compose["docker-compose.yml<br/>Local development"]
    Config --> Dockerfile["Dockerfile<br/>Container image"]
    Config --> Manifests["k8s-manifests.yaml<br/>Reference manifests"]
    Config --> TfVars["terraform.tfvars.example<br/>Variable examples"]
    
    Root --> Cicd["CI/CD"]
    Cicd --> Workflows[".github/workflows/"]
    Workflows --> CiYml["ci.yml<br/>Continuous Integration"]
    Workflows --> CdYml["cd.yml<br/>Continuous Deployment"]
    
    Root --> Docs["Documentation"]
    Docs --> DocsDir["docs/"]
    DocsDir --> Arch["ARCHITECTURE.md<br/>This file"]
    DocsDir --> Practice["PRACTICE.md<br/>Exercises"]
    DocsDir --> Quick["QUICKREF.md<br/>Commands"]
    DocsDir --> Troubleshoot["TROUBLESHOOTING.md<br/>Debugging"]
    DocsDir --> Other["...<br/>Other guides"]
```

## Resource Dependencies

```mermaid
graph TD
    NS["Namespace<br/>(sample-app)"] --> CM["ConfigMap<br/>(app-config)"]
    CM --> Dep1["Deployment<br/>(references ConfigMap)"]
    
    NS --> Sec["Secret<br/>(app-secret)"]
    Sec --> Dep2["Deployment<br/>(references Secret)"]
    
    NS --> SA["ServiceAccount"]
    SA --> RB["RoleBinding"]
    RB --> Role["Role"]
    SA --> Dep3["Deployment<br/>(uses ServiceAccount)"]
    
    NS --> Dep4["Deployment"]
    Dep4 --> PVC["PVC<br/>(optional)"]
    PVC --> PV["PV"]
    Dep4 --> HPA["HPA<br/>(references Deployment)"]
    
    NS --> Svc["Service<br/>(references Deployment pods)"]
    Svc --> Ing["Ingress<br/>(optional, references Service)"]
```
