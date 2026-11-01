# chatgpt-notes

固定フォルダ内にMarkdownを書き出すLinux用stdio MCPサーバー。
要求元: 2026-11-01のユーザー提示構想と[Issue #1](https://gitea.honya.dev/honya/chatgpt-notes/issues/1)。このREADMEが仕様の正本。

## 仕様

公開ツールは `save_note(path, content)` のみ。起動時に保存rootを固定する（既定 `~/chatgpt-notes`）。pathはroot相対の `.md` パス。必要な親フォルダを作り、UTF-8で新規保存または全文更新する。戻り値は相対pathとUTF-8バイト数。追記専用機能はなく、更新後の全文を渡す。

絶対パス、空・`.`・`..` の要素、隠し要素、バックスラッシュ、NUL、非Markdownを拒否する。directory fdとO_NOFOLLOWでsymlinkをたどらず、既存ファイルのhardlink・非通常ファイルも拒否。一時ファイルへ書込後に同一フォルダで置換し、失敗で既存メモを切り詰めない。

保存rootとその親は信頼する利用者が管理し、他者に書込権限を与えない。特権で実行しない。配下の通常Markdownはツールから更新できるので、更新してよいメモだけを置く。読み取り・削除・シェル・Git・HTTP公開は提供しない。

## 実行

Python 3.13、Linux、共有venvを使用する。

```sh
uv pip install --python ~/.venv/bin/python -r requirements.txt
~/.venv/bin/python server.py --root ~/chatgpt-notes
```

stdio対応クライアントでcommandをPythonの絶対パス、argsを `["/絶対パス/server.py", "--root", "/絶対パス/chatgpt-notes"]` として登録する。stdoutはMCP通信専用。

ChatGPT Desktop/Androidの実機接続は未検証。stdioサーバーを作るだけでChatGPTに直接登録できるとは限らない。[OpenAI接続資料](https://developers.openai.com/api/docs/mcp)と[Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)で利用アカウントの接続方式を確認する。HTTP/Tunnelは後続。

## 検証

```sh
~/.venv/bin/python -m unittest discover -s tests -v
~/.venv/bin/python -m compileall -q notes.py server.py tests
```

保存・更新・UTF-8、不正パス、symlink/hardlink、失敗時の既存内容保護、MCP initialize/tools/list/tools/callを検証する。CIは未構成。
