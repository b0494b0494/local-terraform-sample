# ローカルTerraform練習用サンプルアプリ

ローカルのエミュレータ環境で完結するTerraformとKubernetesの練習用アプリです。

## 必要な環境

- Docker & Docker Compose
- Terraform >= 1.0
- Kubernetes（Minikube/kind/k3d）+ kubectl

## クイックスタート

### 1. アプリを起動（最も簡単）

```bash
make docker-compose-up
# または
docker-compose up -d
```

アクセス: `http://localhost:8080`

### 2. LLMオブザーバビリティアプリを起動

```bash
docker-compose up llm-app -d
```

アクセス: `http://localhost:8081`

**オブザーバビリティ機能**:
- 構造化ログ（JSON形式）
- Prometheus形式のメトリクス（`/metrics`）
- トレーシング（`/traces`）
- ダッシュボード（`observability_dashboard.html`をブラウザで開く）

### 3. TerraformでKubernetesにデプロイ

```bash
# Kubernetes環境を準備（Minikubeの場合）
minikube start
eval $(minikube docker-env)
docker build -t sample-app:latest .

# Terraformでデプロイ
terraform init
terraform apply

# 確認
kubectl get all -n sample-app
kubectl port-forward -n sample-app svc/sample-app-service 8080:80
```

### 4. クリーンアップ

```bash
terraform destroy
docker-compose down
```

## 便利なコマンド

```bash
make help              # コマンド一覧
make docker-compose-up # アプリ起動
make terraform-init    # Terraform初期化
make terraform-apply   # Terraformでデプロイ
make test             # テスト実行
```

## 学習リソース

- **[docs/PRACTICE.md](./docs/PRACTICE.md)** - 練習課題集（初級〜上級）
- **[docs/QUICKREF.md](./docs/QUICKREF.md)** - クイックリファレンス（よく使うコマンド）
- **[docs/TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md)** - トラブルシューティング
- **[docs/CHANGELOG.md](./docs/CHANGELOG.md)** - 変更履歴

## LLMオブザーバビリティ練習

最近流行りのLLMアプリケーションのオブザーバビリティ（可観測性）をローカルで練習できます。

### 機能

1. **構造化ログ**: JSON形式のログ出力
2. **メトリクス**: Prometheus形式のメトリクス（リクエスト数、レスポンスタイム、トークン数など）
3. **トレーシング**: 簡易的な分散トレーシング（OpenTelemetry風）
4. **ダッシュボード**: HTMLベースの簡易ダッシュボード

### 使い方

```bash
# LLMアプリを起動
docker-compose up llm-app -d

# チャットAPIをテスト
curl -X POST http://localhost:8081/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'

# メトリクスを確認
curl http://localhost:8081/metrics

# トレーシングデータを確認
curl http://localhost:8081/traces

# ダッシュボードを開く（ブラウザで）
open observability_dashboard.html
```

## セキュリティ注意

⚠️ **ローカル練習環境用です。本番環境では使用しないでください。**

- `DEBUG=True`は開発環境のみ
- 機密情報はコードに含めない（`.gitignore`で除外済み）

## ファイル構成

```
app.py                      # Flaskアプリ
llm_app.py                  # LLM風アプリ（オブザーバビリティ実装）
observability_dashboard.html # オブザーバビリティダッシュボード
docker-compose.yml          # Docker Compose設定
main.tf                     # Terraform設定
k8s-manifests.yaml         # Kubernetesマニフェスト（参考用）
docs/                      # ドキュメント
  PRACTICE.md              # 練習課題集
  QUICKREF.md              # クイックリファレンス
  TROUBLESHOOTING.md       # トラブルシューティング
  CHANGELOG.md             # 変更履歴
.cursorrules               # Cursorルール（セキュリティ）
```

詳細は各ドキュメントを参照してください。
