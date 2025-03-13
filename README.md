# VJudge 获取 OJ 提交脚本

该项目是一个用 Python 编写的脚本，用于从 VJudge 批量获取账号在 OJ 的提交数据。项目使用虚拟环境 (venv) 管理依赖，并通过 .env 文件配置环境变量。

## 已支持 OJ

- CodeForces
- AtCoder
- 洛谷

## 安装与使用

### 1. 克隆仓库

使用 Git 克隆项目到本地：

```bash
git clone https://github.com/xiaowhang/vjudge-submission-tracker.git
cd vjudge-submission-tracker
```

### 2. 创建虚拟环境

建议使用 Python 内置的 `venv` 模块创建虚拟环境：

```bash
python3 -m venv .venv
```

### 3. 激活虚拟环境

- **Windows：**

  ```bash
  .venv\Scripts\activate
  ```

- **macOS/Linux：**

  ```bash
  source .venv/bin/activate
  ```

### 4. 安装依赖

在虚拟环境激活状态下，使用 `pip` 安装项目依赖：

```bash
pip install -r requirements.txt
```

### 5. 配置环境变量

项目使用 `.env` 文件存储环境变量信息。请按照以下步骤进行配置：

1. 在项目根目录下创建 `.env` 文件（可以复制 `.env.example` 文件）。
2. 根据需要在 `.env` 文件中设置以下变量（示例配置）：

   ```ini
   # .env 示例
   VJUDGE_COOKIE=your_vjudge_cookie_here
   
   CF_USER=your_CodeForces_username_here
   ATC_USER=your_AtCoder_username_here
   ```

> 在 [VJudge.net](https://vjudge.net/problem) 中按 F12 打开开发者工具（DevTools），在控制台（Console）中输入下面的代码即可获取所需的 cookie
> ```js
> prompt("复制以下 Cookie:", document.cookie);
> ```

### 6. 配置

在 [VJudge.net](https://vjudge.net/problem) 中给每个平台的题目添加账号信息：

- [AtCoder-abc123_a](https://vjudge.net/problem/AtCoder-abc123_a)
- [CodeForces-1A](https://vjudge.net/problem/CodeForces-1A)
- [洛谷-P1001](https://vjudge.net/problem/洛谷-P1001)

> 依次点击 `Submit`、`Submit by: Archive`、`Update`，填入对应的值。
> 参考 [Submit with your own account](https://vjudge.net/article/2790)。

### 7. 获取洛谷题目数据

因洛谷没有 API 获取帐号提交的详细信息，故需手动添加通过的题号：

在洛谷的个人主页中，点击 练习 可以查看已通过的题目。

在 luogu 文件夹下新建 `problems.txt` 文件，将题目编号直接复制粘贴进去，格式见 `luogu/problems.example.txt` 文件（普及− 等信息可有可无）。

### 8. 运行脚本

在虚拟环境中运行主程序：

```bash
python main.py
```

## 注意：解决状态码 401 错误的方法

在使用过程中，如果遇到类似 `❗ 发送 xxx 的更新请求失败, 状态码：401` 的错误，请依照以下步骤逐步排查并解决问题：

1. 获取最新 Cookie：
   - 打开 [VJudge.net](https://vjudge.net) 并重新登录账号。
   - 参照上面的配置环境变量步骤重新配置 VJUDGE_COOKIE

2. 获取完整 Cookie：
   - 如果更新后问题依旧，按 F12 打开开发者工具并切换到 **Network（网络）** 面板。
   - 按 F5 刷新页面，点击任意一个网络请求（如 `.png` 的请求）
   - 查看请求头中的 Cookie 信息，将其完整复制到 `.env` 文件更新对应的 `VJUDGE_COOKIE` 变量。


## 贡献

欢迎对本项目进行贡献。如果你有任何建议、问题或想提交 bug 修复，请提交 issue 或 pull request。
