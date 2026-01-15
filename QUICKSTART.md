# クイックスタートガイド

> **Note**: UNIX系OS（macOS, Linux）専用です。

## 5分で始める

### 1. tmuxインストール

```bash
# macOS
brew install tmux

# Linux
sudo apt-get install tmux

# 確認
tmux -V
```

### 2. コラボレーション開始

Claudeに言う：
```
「CodexでJWT認証を作って」
```

Claudeが自動的に：
1. tmuxセッション作成（tmux内ならペイン追加、tmux外なら新規セッション）
2. 通信インフラ構築
3. 次のステップをガイド

### 3. セッションに接続

```bash
# tmux外から実行した場合
tmux attach-session -t [セッション名]

# ペイン構成
# 左：Claude（実装）
# 右：Codex（レビュー）- 自動起動
```

### 4. メッセージ通信

**Claude（左ペイン）:**
```bash
# ガイダンス要求 + 自動通知
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py \
  --agent claude --type IMPLEMENT \
  --message "JWT実装の設計アドバイスを" \
  --notify

# 応答を待機（オプション）
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py \
  --agent claude --action wait --timeout 60

# 応答を読む
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py \
  --agent claude --action read
```

**Codex（右ペイン）:**
```bash
# メッセージ読む
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py \
  --agent codex --action read

# 応答 + 自動通知
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py \
  --agent codex --type SUGGEST \
  --message "PyJWT推奨。RS256、15分有効期限" \
  --notify
```

---

## 60秒タイムアウト（自動フォールバック）

Codexが60秒以内に応答しない場合、自動的に簡易モードに：

```
⚠️ Codexから応答なし（60秒）
簡易モードに切り替えます

[Codexモード]
アーキテクチャガイダンス...

[Codeモード]
実装中...
```

開発は止まりません。Codexが後で参加可能。

---

## チートシート

### メッセージタイプ

| タイプ | 用途 | 使用者 |
|--------|------|--------|
| IMPLEMENT | ガイダンス要求 | Claude |
| REVIEW | レビュー依頼 | Claude |
| SUGGEST | 提案・フィードバック | Codex |
| APPROVE | 承認 | Codex |
| QUESTION | 質問 | 両方 |
| COMPLETE | 完了報告 | Claude |

### 新オプション

| オプション | 説明 |
|------------|------|
| `--notify` | 相手ペインに自動通知 |
| `--wait` | 応答を待機 |
| `--timeout N` | 待機秒数（デフォルト60） |

### tmux基本操作

| 操作 | コマンド |
|------|----------|
| ペイン切り替え | `Ctrl+b` → `o` |
| デタッチ | `Ctrl+b` → `d` |
| コピーモード | `Ctrl+b` → `[` |
| ペーストモード | `Ctrl+b` → `]` |
| ヘルプ | `Ctrl+b` → `?` |

### よく使うコマンド

```bash
# スクリプトのベースパス
SCRIPTS=~/.claude/skills/codex-collab/scripts

# 読む
python3 $SCRIPTS/collab_communicate.py --agent [claude|codex] --action read

# 書く（通知付き）
python3 $SCRIPTS/collab_communicate.py --agent [claude|codex] \
  --type [TYPE] --message "..." --notify

# 履歴
python3 $SCRIPTS/collab_communicate.py --action history --limit 10

# クリア
python3 $SCRIPTS/collab_communicate.py --action clear

# セッション一覧
python3 $SCRIPTS/session_manager.py --list

# セッション終了
python3 $SCRIPTS/session_manager.py --end --session-name [name]
```

---

## 通信ディレクトリ

```
/tmp/codex_collab/
├── messages.json       # メッセージキュー
├── history.json        # 履歴
├── sessions.json       # セッション情報
├── pane_info.json      # ペインID管理
└── current_session.txt # 現在のセッション
```

---

## ヒント

### いつtmuxモードを使う？

**使うべき時:**
- 長期プロジェクト（複数日）
- 複雑な機能開発
- 詳細なコードレビューが必要
- チーム開発

**使わない時:**
- クイックな修正
- プロトタイピング
- tmux未インストール

### 効率的なワークフロー

1. **小さく始める**: 1機能ずつ開発
2. **頻繁にレビュー**: 大きな変更前に確認
3. **履歴を活用**: 過去の決定を参照
4. **--notify活用**: 手動通知の手間を省く
5. **セッション永続化**: `Ctrl+b d`でデタッチ、後で再開

### トラブル時

```bash
# 何か変な時は再初期化
python3 ~/.claude/skills/codex-collab/scripts/session_manager.py \
  --end --session-name problematic
python3 ~/.claude/skills/codex-collab/scripts/session_manager.py \
  --init --session-name fresh-start

# メッセージが詰まったらクリア
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --action clear

# JSON破損時は .bak から復旧
ls /tmp/codex_collab/*.bak
cp /tmp/codex_collab/messages.bak /tmp/codex_collab/messages.json
```

---

## 実践例

### 例1: API開発（15分）

```bash
# セッション開始（tmux外から）
python3 ~/.claude/skills/codex-collab/scripts/session_manager.py \
  --init --session-name api-dev
tmux attach-session -t api-dev

# [左] ガイダンス要求
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py \
  --agent claude --type IMPLEMENT \
  --message "ユーザー登録APIの設計" --notify --wait

# [右] 応答（Codexが受信して返答）
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py \
  --agent codex --type SUGGEST \
  --message "POST /api/register: email validation, password strength, rate limiting" \
  --notify

# [左] 実装後、レビュー依頼
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py \
  --agent claude --type REVIEW \
  --message "登録API完成" --notify

# [右] 承認
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py \
  --agent codex --type APPROVE \
  --message "Good to go!" --notify
```

---

## ヘルプ

詳細は以下を参照：
- `SKILL.md` - 完全なドキュメント
- `references/communication_protocol.md` - プロトコル詳細
- `references/best_practices.md` - ベストプラクティス

問題があれば：
1. `tmux ls` でセッション確認
2. `/tmp/codex_collab/` のファイル確認
3. 再初期化を試す
