# Codex 協調開発スキル

**実際に並行して**協力して開発を進めるtmuxベースのスキルです。

> **Note**: このスキルはUNIX系OS（macOS, Linux）専用です。Windowsでは動作しません（fcntlを使用）。

## 基本コンセプト

**デフォルト：tmuxモード**（真の並行コラボレーション）
- 左ペイン：Claude（実装担当）
- 右ペイン：Codex（レビュー・ガイダンス担当）
- 独立したプロセス間でメッセージ通信

**フォールバック：簡易モード**（60秒タイムアウト時のみ）
- Codexが60秒以内に応答しない場合
- 両方の役割をシミュレート
- 開発が止まらないように自動切り替え

---

## クイックスタート

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
1. tmuxセッション初期化（tmux内なら現在のセッションにペイン追加、tmux外なら新規セッション作成）
2. 通信インフラ構築
3. 次のステップをガイド

### 3. tmuxセッションに接続

```bash
# tmux外から実行した場合、セッションにアタッチ
tmux attach-session -t [プロジェクト名]

# 左ペイン：このClaudeとの会話が続く（Code）
# 右ペイン：Codexが自動起動（レビュー役）
```

---

## 通信方法

### 左ペイン（Claude）

```bash
# ガイダンスを要求（--notify で相手に自動通知）
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py \
  --agent claude --type IMPLEMENT \
  --message "JWT認証の実装を計画中。アーキテクチャのアドバイスを" \
  --notify

# 応答を待機（最大60秒）
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py \
  --agent claude --action wait --timeout 60

# Codexの応答を読む
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py \
  --agent claude --action read
```

### 右ペイン（Codex）

```bash
# メッセージを読む
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py \
  --agent codex --action read

# 応答する（--notify で相手に自動通知）
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py \
  --agent codex --type SUGGEST \
  --message "PyJWTを推奨。RS256署名、15分有効期限、リフレッシュローテーション" \
  --notify
```

---

## 新機能（v2）

### 自動通知（--notify）

メッセージ送信時に `--notify` を付けると、相手のペインに自動で通知が送られます。

```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py \
  --agent claude --type REVIEW --message "レビューお願いします" --notify
```

### 応答待機（--wait）

メッセージ送信後に相手の応答を待機します。

```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py \
  --agent claude --type IMPLEMENT --message "設計アドバイスを" --wait --timeout 90
```

### tmux外からのセッション作成

tmux外から実行すると、新規セッションを自動作成します。

```bash
# tmux外から実行
python3 ~/.claude/skills/codex-collab/scripts/session_manager.py \
  --init --session-name my-project

# 作成後にアタッチ
tmux attach-session -t my-project
```

### データ保護機能

- **排他ロック**: 複数プロセスからの同時書き込みを防止
- **原子的書き込み**: 書き込み途中でのデータ破損を防止
- **自動復旧**: JSON破損時に `.bak` へ退避して警告表示

---

## タイムアウト動作

**Codexが60秒以内に応答しない場合：**

```
⚠️ Codexから60秒以内に応答がありません
簡易モードに切り替えます - 両方の役割をシミュレートします

[Codexモード]
JWT認証のアーキテクチャガイダンス：
- PyJWT with RS256
- アクセストークン15分
...

[Codeモード]
ガイダンスに基づいて実装中...
```

---

## メッセージタイプ

| タイプ | 用途 | 送信者 |
|--------|------|--------|
| `IMPLEMENT` | 実装前のガイダンス要求 | Claude |
| `REVIEW` | コードレビュー要求 | Claude |
| `SUGGEST` | 提案・フィードバック | Codex |
| `APPROVE` | 実装承認 | Codex |
| `QUESTION` | 質問・確認 | 両方 |
| `COMPLETE` | タスク完了報告 | Claude |

---

## 通信ディレクトリ構成

```
/tmp/codex_collab/
├── messages.json       # アクティブなメッセージキュー
├── history.json        # 全メッセージ履歴
├── sessions.json       # セッションメタデータ
├── pane_info.json      # 動的ペインID管理
└── current_session.txt # 現在のセッション名
```

---

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

---

## トラブルシューティング

**Q: tmuxがインストールされていない**
```bash
brew install tmux  # macOS
sudo apt-get install tmux  # Linux
```

**Q: メッセージが表示されない**
```bash
# 通信ディレクトリ確認
ls -la /tmp/codex_collab/

# メッセージ確認
cat /tmp/codex_collab/messages.json

# 再初期化
python3 ~/.claude/skills/codex-collab/scripts/session_manager.py \
  --init --session-name test
```

**Q: セッションが見つからない**
```bash
# セッション一覧
tmux ls

# 新規作成
python3 ~/.claude/skills/codex-collab/scripts/session_manager.py \
  --init --session-name new-session
```

**Q: JSONファイルが破損した**
```bash
# 破損したファイルは自動的に .bak へ退避されます
ls -la /tmp/codex_collab/*.bak

# 手動復旧
cp /tmp/codex_collab/messages.bak /tmp/codex_collab/messages.json
```

---

## ライセンス

MIT License
