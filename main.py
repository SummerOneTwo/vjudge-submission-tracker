import copy
import json
import logging
import os

import dotenv
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def read_lines(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return file.read().splitlines()


def write_lines(filename, lines):
    with open(filename, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))


def read_json(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)


def write_json(filename, data):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


class Vjudge:
    DEFAULT_DATA = {
        "method": "2",
        "language": None,  # 语言 ID
        "open": "1",  # 是否公开代码
        "source": "",
        "oj": None,  # OJ 平台
        "probNum": None,  # 题目编号
    }

    SUBMIT_URL = "https://vjudge.net/problem/submit"

    def __init__(self):
        if not dotenv.find_dotenv():
            logging.error("❗ 未找到 .env 文件")
            return

        dotenv.load_dotenv()
        self.cookies = dict(item.split("=", 1) for item in os.getenv("VJUDGE_COOKIE").split("; "))
        self.oj_config = {
            "atcoder": {"language": "5001", "oj": "AtCoder"},
            "codeforces": {"language": "91", "oj": "CodeForces"},
            "luogu": {"language": "27", "oj": "洛谷"},
        }
        
        # 添加请求头和会话配置
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 配置代理设置
        if os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY"):
            proxies = {}
            if os.getenv("HTTP_PROXY"):
                proxies['http'] = os.getenv("HTTP_PROXY")
            if os.getenv("HTTPS_PROXY"):
                proxies['https'] = os.getenv("HTTPS_PROXY")
            self.session.proxies.update(proxies)
            logging.info(f"已配置代理：{proxies}")

        self.update_problems()

    def update_problems(self):
        logging.info("开始更新做题信息")

        self.fetch("atcoder")
        self.fetch("codeforces")
        self.fetch("luogu")

    def fetch(self, oj_name):
        if not os.path.exists(oj_name):
            os.mkdir(oj_name)
        os.chdir(oj_name)

        if oj_name == "atcoder":
            self.get_ATC_problem()
        elif oj_name == "codeforces":
            self.get_CF_problem()
        elif oj_name == "luogu":
            self.get_LG_problem()

        logging.info(f"开始提交 {oj_name} 做题信息")

        problems = read_lines("problems.txt")
        try:
            succ = read_json("success_problems.json")
        except FileNotFoundError:
            succ = {}

        # 对于所有 OJ，只处理新增的题目（避免重复提交已处理的题目）
        # 获取已经处理过的题目（无论成功或失败）
        processed_problems = set(succ.keys())
        # 获取当前所有题目
        current_problems = set(problems)
        # 只处理新增的题目
        new_problems = current_problems - processed_problems
        problems = list(new_problems)
        if new_problems:
            logging.info(f"发现 {len(new_problems)} 道新增题目需要提交：{', '.join(sorted(new_problems))}")
        else:
            logging.info("没有发现新增题目，跳过提交")
            os.chdir("..")
            return

        for problem in problems:
            if problem in succ and "success" in succ[problem] and succ[problem]["success"]:
                continue

            if problem in succ and "error" in succ[problem] and succ[problem]["error"] == "No recent submissions found":
                continue

            data = copy.deepcopy(self.DEFAULT_DATA)
            for key, value in self.oj_config[oj_name].items():
                data[key] = value
            data["probNum"] = problem

            if oj_name == "codeforces" and len(problem) > 6:
                data["oj"] = "Gym"

            try:
                response = self.session.post(f"{self.SUBMIT_URL}/{data['oj']}-{data['probNum']}", 
                                           data=data, cookies=self.cookies, timeout=30)
            except requests.exceptions.RequestException as e:
                logging.error(f"❗ 请求 {data['oj']}-{data['probNum']} 时发生网络错误：{e}")
                continue

            if response.status_code != 200:
                logging.error(f"❗ 发送 {data['oj']}-{data['probNum']} 的更新请求失败, 状态码：{response.status_code}")
                if response.status_code == 401:
                    logging.error("❗ 请检查 VJUDGE_COOKIE 是否已过期或从网络请求中获取完整的 Cookie（参考 README.md）")
                continue

            # 解析本次请求结果
            try:
                result = json.loads(response.text)
            except json.JSONDecodeError:
                logging.error(f"❗ 解析 {data['oj']}-{data['probNum']} 响应失败，原始内容：{response.text[:200]}")
                continue

            # 仅在成功或允许的特定错误(无近期提交)时写入 success_problems.json
            allow_store = False
            if result.get("success") is True:
                allow_store = True
            elif result.get("error") == "No recent submissions found":
                # 这表示题目已读取但无最近提交，也视为无需再次尝试
                allow_store = True

            if allow_store:
                succ[problem] = result
                write_json("success_problems.json", succ)
                if result.get("success"):
                    logging.info(f"✅ 更新 {data['oj']}-{data['probNum']} 成功")
                else:
                    logging.info(f"ℹ️ {data['oj']}-{data['probNum']} 无最近提交记录 (No recent submissions found)")
            else:
                # 不写入成功文件，提醒用户可稍后重试
                logging.warning(
                    f"❌ 更新 {data['oj']}-{data['probNum']} 失败（未写入成功列表），错误信息：{result.get('error', '未知错误')}"
                )

        os.chdir("..")

    def get_ATC_problem(self):
        logging.info(f"获取 {'AtCoder':^10} 题目信息")
        url = "https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions"

        try:
            submissions = read_json("submissions.json")
        except FileNotFoundError:
            submissions = []

        while True:
            try:
                last_time = submissions[-1]["epoch_second"] + 1
            except IndexError:
                last_time = 0
            params = {"user": os.getenv("ATC_USER"), "from_second": last_time}

            try:
                response = self.session.get(url, params=params, timeout=30).json()
            except requests.exceptions.RequestException as e:
                logging.error(f"❗ AtCoder API 请求失败：{e}")
                break
            except json.JSONDecodeError as e:
                logging.error(f"❗ AtCoder API 响应解析失败：{e}")
                break
            submissions.extend(response)

            if response == []:
                break

        write_json("submissions.json", submissions)

        # 得到所有题目编号
        try:
            problems = set(read_lines("problems.txt"))
        except FileNotFoundError:
            problems = set()

        for item in submissions:
            problems.add(item["problem_id"])

        write_lines("problems.txt", list(problems))
        logging.info(f"获取 {'AtCoder':^10} 题目信息成功, 共 {len(problems)} 道题目")

    def get_CF_problem(self):
        logging.info(f"获取 {'Codeforces':^10} 题目信息")
        url = "https://codeforces.com/api/user.status"
        params = {"handle": os.getenv("CF_USER")}

        try:
            response = self.session.get(url, params=params, timeout=30).json()
        except requests.exceptions.RequestException as e:
            logging.error(f"❗ Codeforces API 请求失败：{e}")
            return
        except json.JSONDecodeError as e:
            logging.error(f"❗ Codeforces API 响应解析失败：{e}")
            return

        write_json("submissions.json", response)

        try:
            problems = set(read_lines("problems.txt"))
        except FileNotFoundError:
            problems = set()

        submissions = response["result"]

        for item in submissions:
            problems.add(str(item["problem"]["contestId"]) + item["problem"]["index"])

        write_lines("problems.txt", list(problems))
        logging.info(f"获取 {'Codeforces':^10} 题目信息成功, 共 {len(problems)} 道题目")

    def get_LG_problem(self):
        logging.info(f"获取 {'Luogu':^10} 题目信息")

        try:
            problems = read_lines("problems.txt")
        except FileNotFoundError:
            problems = []

        for item in ["暂无评定", "入门", "普及−", "普及/提高−", "普及+/提高", "提高+/省选−", "省选/NOI−", "NOI/NOI+/CTSC"]:
            if item in problems:
                problems.remove(item)  # 删除无效信息

        write_lines("problems.txt", problems)
        logging.info(f"获取 {'Luogu':^10} 题目信息成功, 共 {len(problems)} 道题目")


if __name__ == "__main__":
    vju = Vjudge()
