# Codex 協調開発スキル

**実際に並行して**協力して開発を進めるtmuxベースのスキルです。

## 🎯 基本コンセプト

**デフォルト：tmuxモード**（真の並行コラボレーション）
- 左ペイン：実装担当
- 右ペイン：Codex（レビュー・ガイダンス担当）
- 独立したプロセス間でメッセージ通信

**フォールバック：簡易モード**（60秒タイムアウト時のみ）
- Codexが60秒以内に応答しない場合
- 両方の役割をシミュレート
- 開発が止まらないように自動切り替え

---

## 🚀 クイックスタート

### 1. tmuxインストール

```bash
# macOS
brew install tmux

# Linux  
sudo apt-get install tmux
```

### 2. コラボレーション開始

Claudeに言うだけ：
```
「CodexでJWT認証システムを作って」
```

Claudeが自動的に：
1. ✅ tmuxセッション初期化
2. ✅ 通信インフラ構築
3. ✅ 次のステップをガイド

### 3. tmuxセッションに接続

```bash
# セッションにアタッチ
tmux attach-session -t [プロジェクト名]

# 左ペイン：このClaudeとの会話が続く（Code）
# 右ペイン：新しいClaude会話を開始（Codex役）
```

---

## 💬 通信方法

### 左ペイン（Code）

```bash
# ガイダンスを要求
python scripts/collab_communicate.py --agent claude --type IMPLEMENT \
  --message "JWT認証の実装を計画中。アーキテクチャのアドバイスを"

# 60秒待機...

# Codexの応答を読む
python scripts/collab_communicate.py --agent claude --action read
```

### 右ペイン（Codex）

```bash
# メッセージを読む
python scripts/collab_communicate.py --agent codex --action read

# 応答する
python scripts/collab_communicate.py --agent codex --type SUGGEST \
  --message "PyJWTを推奨。RS256署名、15分有効期限、リフレッシュローテーション"
```

---

## ⏱️ タイムアウト動作

**Codexが60秒以内に応答しない場合：**

```
⚠️ Codexから60秒以内に応答がありません
簡易モードに切り替えます - 両方の役割をシミュレートします

[Codexモード 🔍]
JWT認証のアーキテクチャガイダンス：
- PyJWT with RS256
- アクセストークン15分
...

[Codeモード 🔧]
ガイダンスに基づいて実装中...
```

これにより：
- ✅ 開発が止まらない
- ✅ ユーザーがCodexペインを開くのを待たなくて良い
- ✅ 後からtmuxモードに戻れる

**Codexが後で利用可能になった場合：**

```
💡 ヒント: Codexがtmuxセッションで利用可能になりました
   フルコラボレーションに戻るには：
   
   tmux attach-session -t [プロジェクト名]
```

---

## 📋 メッセージタイプ

| タイプ | 用途 | 送信者 |
|--------|------|--------|
| `IMPLEMENT` | 実装前のガイダンス要求 | Code |
| `REVIEW` | コードレビュー要求 | Code |
| `SUGGEST` | 提案・フィードバック | Codex |
| `APPROVE` | 実装承認 | Codex |
| `QUESTION` | 質問・確認 | 両方 |
| `COMPLETE` | タスク完了報告 | Code |

---

## インストール

1. このスキルをClaude.aiにインポート
2. （tmuxモード使用時のみ）tmuxをインストール

## ファイル構成

```
codex-collab/
├── SKILL.md                          # メインスキル定義
├── scripts/
│   ├── collab_communicate.py         # 通信スクリプト
│   └── session_manager.py            # セッション管理
└── references/
    ├── communication_protocol.md     # 詳細なプロトコル
    └── best_practices.md             # ベストプラクティス
```

## 詳細なワークフロー例

### 例: OAuth2実装（tmuxモード）

**左ペイン（Code）**:
```bash
# 1. ガイダンス要求
python scripts/collab_communicate.py --agent claude --type IMPLEMENT \
  --message "OAuth2認証サーバーを構築。アーキテクチャのアドバイスを"

# 2. Codexの返答待ち...

# 3. 返答を読む
python scripts/collab_communicate.py --agent claude --action read
# → authlibを使用、PKCEサポート、などの推奨事項

# 4. 実装
vim src/auth/oauth_server.py
# ... コーディング ...

# 5. レビュー依頼
python scripts/collab_communicate.py --agent claude --type REVIEW \
  --message "OAuth2サーバー実装完了：認可エンドポイント、トークンエンドポイント、PKCE対応"
```

**右ペイン（Codex）**:
```bash
# 1. リクエスト読み取り
python scripts/collab_communicate.py --agent codex --action read

# 2. アーキテクチャガイダンス提供
python scripts/collab_communicate.py --agent codex --type SUGGEST \
  --message "OAuth2サーバー推奨事項：
1. authlib使用（実績あり）
2. すべてのクライアントでPKCE実装
3. トークンをユーザーと関連付けて保存
4. レート制限追加（10req/分）
5. リダイレクトURIを厳格に検証"

# 3. 実装待ち...

# 4. レビューリクエスト読み取り
python scripts/collab_communicate.py --agent codex --action read

# 5. コードレビュー
cat src/auth/oauth_server.py

# 6. フィードバック
python scripts/collab_communicate.py --agent codex --type SUGGEST \
  --message "良好。追加：
1. トークン無効化エンドポイント
2. リフレッシュトークンローテーション"

# 7. 最終承認
python scripts/collab_communicate.py --agent codex --type APPROVE \
  --message "すべて対応済み。本番環境準備完了"
```

## トラブルシューティング

**Q: tmuxがインストールされていない**
```bash
brew install tmux  # macOS
```

**Q: メッセージが表示されない**
```bash
# 通信ディレクトリ確認
ls -la /tmp/code_codex_collab/

# 再初期化
python scripts/session_manager.py --init --session-name test
```

**Q: セッションが見つからない**
```bash
# セッション一覧
tmux ls

# 新規作成
python scripts/session_manager.py --init --session-name new-session
```

## ライセンス

MIT License
